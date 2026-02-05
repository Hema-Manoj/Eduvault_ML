import sqlite3

conn = sqlite3.connect("data/issuer_phash.db")
cur = conn.cursor()

cur.execute("DELETE FROM issuer_phash WHERE issuer_id = 'unknown'")
conn.commit()

cur.execute("SELECT issuer_id FROM issuer_phash")
print("Remaining issuers:", cur.fetchall())

conn.close()
