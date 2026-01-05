import sqlite3
import os

os.makedirs("data", exist_ok=True)

DB_PATH = "data/issuer_phash.db"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS issuer_phash (
    issuer_id TEXT PRIMARY KEY,
    issuer_name TEXT,
    phash TEXT NOT NULL
)
""")

conn.commit()
conn.close()

print("✅ issuer_phash database created successfully")
