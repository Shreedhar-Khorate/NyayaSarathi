import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), "..", "data", "nyayasarathi.db")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("PRAGMA foreign_keys=OFF;")
cursor.execute("BEGIN TRANSACTION;")

cursor.execute("""
CREATE TABLE IF NOT EXISTS users_new (
    id TEXT PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT,
    full_name TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'USER',
    avatar_url TEXT,
    organization TEXT,
    designation TEXT,
    profile_completed INTEGER NOT NULL DEFAULT 0,
    google_sub TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
""")

cursor.execute("""
INSERT INTO users_new (
    id, email, password_hash, full_name, role, avatar_url,
    organization, designation, profile_completed, google_sub,
    created_at, updated_at
)
SELECT 
    id, email, password_hash, full_name, role, avatar_url,
    organization, designation, profile_completed, google_sub,
    created_at, updated_at
FROM users;
""")

cursor.execute("DROP TABLE users;")
cursor.execute("ALTER TABLE users_new RENAME TO users;")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_google_sub ON users(google_sub);")

conn.commit()
conn.close()
print("[OK] SQLite users table schema migrated successfully.")
