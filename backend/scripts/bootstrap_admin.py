"""
NyayaSarathi Secure Administrator Bootstrap CLI.
Provision or verify the initial system administrator account in the authoritative database.

Usage:
  # Via Environment Variables (Recommended for CI/CD and production deployment):
  export BOOTSTRAP_ADMIN_EMAIL="admin@court.gov.in"
  export BOOTSTRAP_ADMIN_PASSWORD="StrongSecurePassword123"
  export BOOTSTRAP_ADMIN_NAME="Chief Judicial Administrator"
  python backend/scripts/bootstrap_admin.py

  # Via CLI Arguments:
  python backend/scripts/bootstrap_admin.py --email "admin@court.gov.in" --name "Chief Admin"

  # Verification / Status Check Only:
  python backend/scripts/bootstrap_admin.py --email "admin@court.gov.in" --check

Security Notice:
  Never commit passwords to version control. Passwords are validated for complexity
  and hashed immediately using bcrypt before persistence.
"""

import argparse
import getpass
import os
import re
import sys
from typing import Optional

# Ensure backend root is in sys.path
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from dotenv import load_dotenv
load_dotenv(os.path.join(BACKEND_DIR, ".env"))

from services.user_repository import (
    get_user_by_email,
    create_user,
    update_user_role_with_audit,
    is_postgres_authoritative,
    get_pg_connection,
    get_db_connection,
    init_user_table,
)
from services.auth_service import hash_password


EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")


def validate_password_strength(password: str) -> bool:
    """Enforce minimum 8 characters, at least one letter, and at least one digit."""
    if len(password) < 8:
        return False
    has_letter = any(c.isalpha() for c in password)
    has_digit = any(c.isdigit() for c in password)
    return has_letter and has_digit


def bootstrap_admin(
    email: str,
    password: Optional[str] = None,
    name: str = "System Administrator",
    reset_password: bool = False,
    promote: bool = False,
    check_only: bool = False,
) -> int:
    init_user_table()
    clean_email = email.strip().lower()

    if not EMAIL_REGEX.match(clean_email):
        print(f"[ERROR] Invalid email format: '{clean_email}'")
        return 1

    existing_user = get_user_by_email(clean_email)

    if check_only:
        if not existing_user:
            print(f"[STATUS] No account exists for {clean_email}.")
            return 1
        role = existing_user.get("role", "UNKNOWN")
        is_admin = role == "ADMIN"
        print(f"[STATUS] Account found: {clean_email} | Role: {role} | Active Administrator: {is_admin}")
        return 0 if is_admin else 1

    if existing_user:
        current_role = existing_user.get("role", "USER")
        if current_role == "ADMIN":
            if not reset_password:
                print(f"[INFO] Administrator account already exists for {clean_email}. No changes made.")
                print("       Use --reset-password if you wish to rotate this administrator's credentials.")
                return 0

            # Safe Password Rotation
            if not password:
                print("[ERROR] Password is required to reset administrator password.")
                return 1

            if not validate_password_strength(password):
                print("[ERROR] Password must be at least 8 characters long and contain both letters and digits.")
                return 1

            pw_hash = hash_password(password)
            user_id = existing_user["id"]

            if is_postgres_authoritative():
                conn = get_pg_connection()
                try:
                    with conn:
                        with conn.cursor() as cur:
                            cur.execute(
                                "UPDATE public.users SET password_hash = %s, updated_at = NOW() WHERE id = %s",
                                (pw_hash, user_id)
                            )
                finally:
                    conn.close()

            with get_db_connection() as sconn:
                scur = sconn.cursor()
                scur.execute("UPDATE users SET password_hash = ? WHERE id = ?", (pw_hash, user_id))
                sconn.commit()

            print(f"[SUCCESS] Credentials successfully rotated for administrator: {clean_email}")
            return 0

        else:
            # User exists with non-admin role
            if not promote:
                print(f"[WARNING] Account exists for {clean_email} with role '{current_role}'.")
                print("          To elevate this account to ADMIN, re-run with --promote flag.")
                return 1

            update_user_role_with_audit(
                target_user_id=existing_user["id"],
                actor_user_id=existing_user["id"],
                new_role="ADMIN",
                reason="Privileged initial administrator promotion via bootstrap CLI",
            )

            if reset_password and password:
                if validate_password_strength(password):
                    pw_hash = hash_password(password)
                    if is_postgres_authoritative():
                        conn = get_pg_connection()
                        try:
                            with conn:
                                with conn.cursor() as cur:
                                    cur.execute("UPDATE public.users SET password_hash = %s WHERE id = %s", (pw_hash, existing_user["id"]))
                        finally:
                            conn.close()
                    with get_db_connection() as sconn:
                        scur = sconn.cursor()
                        scur.execute("UPDATE users SET password_hash = ? WHERE id = ?", (pw_hash, existing_user["id"]))
                        sconn.commit()

            print(f"[SUCCESS] Account {clean_email} successfully promoted to ADMIN.")
            return 0

    # User does not exist — Create new ADMIN
    if not password:
        print("[ERROR] Password is required to create a new administrator account.")
        return 1

    if not validate_password_strength(password):
        print("[ERROR] Password must be at least 8 characters long and contain both letters and numbers.")
        return 1

    pw_hash = hash_password(password)
    created = create_user(
        email=clean_email,
        password_hash=pw_hash,
        full_name=name.strip(),
        role="ADMIN",
        profile_completed=True,
    )

    print(f"[SUCCESS] Initial administrator created: {clean_email} (User ID: {created['id']})")
    return 0


def main():
    parser = argparse.ArgumentParser(description="NyayaSarathi Administrator Bootstrap Tool")
    parser.add_argument("--email", default=os.getenv("BOOTSTRAP_ADMIN_EMAIL"), help="Admin email address")
    parser.add_argument("--name", default=os.getenv("BOOTSTRAP_ADMIN_NAME", "System Administrator"), help="Admin full name")
    parser.add_argument("--password", default=os.getenv("BOOTSTRAP_ADMIN_PASSWORD"), help="Admin password (or prompts interactively)")
    parser.add_argument("--reset-password", action="store_true", help="Explicitly rotate password of existing admin")
    parser.add_argument("--promote", action="store_true", help="Promote existing non-admin user to ADMIN")
    parser.add_argument("--check", action="store_true", help="Check status of admin account without modification")

    args = parser.parse_args()

    email = args.email
    if not email:
        email = input("Enter Administrator Email: ").strip()

    if not email:
        print("[ERROR] Administrator email is required.")
        sys.exit(1)

    password = args.password
    if not password and not args.check and (not args.email or args.reset_password):
        if sys.stdin.isatty():
            password = getpass.getpass("Enter Administrator Password: ")

    exit_code = bootstrap_admin(
        email=email,
        password=password,
        name=args.name,
        reset_password=args.reset_password,
        promote=args.promote,
        check_only=args.check,
    )
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
