import sqlite3

conn = sqlite3.connect("data/issuer_phash.db")
cursor = conn.cursor()

cursor.execute("SELECT * FROM issuer_phash")
rows = cursor.fetchall()

for row in rows:
    print(row)

conn.close()
