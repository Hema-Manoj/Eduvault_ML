import sqlite3

conn = sqlite3.connect("data/issuer_phash.db")
cur = conn.cursor()

cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
print("Tables:", cur.fetchall())

cur.execute("SELECT issuer_id, issuer_name, phash FROM issuer_phash;")
rows = cur.fetchall()

print("\nRows in issuer_phash:")
for r in rows:
    print(r)

conn.close()
