import os
import sys
import uuid
from datetime import datetime, timezone

# Ensure backend root is in python path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from services.user_repository import get_db_connection, init_user_table
from services.auth_service import hash_password, verify_password

def seed_demo_users():
    init_user_table()

    demo_accounts = [
        {
            "email": "user@nyayasarathi.in",
            "password": "User@12345",
            "full_name": "Adv. Rohan Verma",
            "role": "USER",
        },
        {
            "email": "judge@nyayasarathi.in",
            "password": "Judge@12345",
            "full_name": "Hon'ble Justice S. K. Mukherjee",
            "role": "JUDGE",
        },
        {
            "email": "admin@nyayasarathi.in",
            "password": "Admin@12345",
            "full_name": "Judicial System Administrator",
            "role": "ADMIN",
        },
    ]

    with get_db_connection() as conn:
        cursor = conn.cursor()
        for acc in demo_accounts:
            email = acc["email"].strip().lower()
            cursor.execute("SELECT id FROM users WHERE LOWER(email) = LOWER(?)", (email,))
            existing = cursor.fetchone()
            pw_hash = hash_password(acc["password"])
            now = datetime.now(timezone.utc).isoformat()

            if existing:
                cursor.execute(
                    "UPDATE users SET password_hash = ?, full_name = ?, role = ? WHERE id = ?",
                    (pw_hash, acc["full_name"], acc["role"], existing["id"]),
                )
                print(f"[UPDATED] {email} (Role: {acc['role']})")
            else:
                user_id = str(uuid.uuid4())
                cursor.execute(
                    """
                    INSERT INTO users (id, email, password_hash, full_name, role, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (user_id, email, pw_hash, acc["full_name"], acc["role"], now),
                )
                print(f"[SEEDED] {email} (Role: {acc['role']})")
        conn.commit()

    print("Demo accounts seeded successfully.")

if __name__ == "__main__":
    seed_demo_users()
