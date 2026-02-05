import sqlite3

conn = sqlite3.connect("data/issuer_phash.db")
cur = conn.cursor()

cur.execute("DELETE FROM issuer_phash WHERE issuer_id LIKE 'unknown_%'")
cur.execute("DELETE FROM issuer_phash WHERE issuer_id = 'unstop'")

conn.commit()

cur.execute("SELECT * FROM issuer_phash;")
print("Remaining rows:", cur.fetchall())

conn.close()
