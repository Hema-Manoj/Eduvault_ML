import sqlite3

DB_PATH = "data/issuer_phash.db"

BASELINE_DATA = [
    ("cisco_ccna", "Cisco (CCNA)", "a7619e89691fe036"),
    ("linkedin_learning", "LinkedIn Learning", "d0255a9b2d522d7e"),
    ("microsoft", "Microsoft", "ecc19b8f318ec6c1"),
    ("nptel", "NPTEL", "f2b742ea298267b2"),
    ("udemy", "Udemy", "bf63c2d0362ce19c"),
    ("unstop", "Unstop", "85fb0ae85f823475"),
    ("eduskills", "EduSkills", "c5334fb16cb1681b"),
]

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

for issuer_id, issuer_name, phash in BASELINE_DATA:
    cursor.execute("""
    INSERT OR REPLACE INTO issuer_phash (issuer_id, issuer_name, phash)
    VALUES (?, ?, ?)
    """, (issuer_id, issuer_name, phash))

conn.commit()
conn.close()

print("✅ Baseline issuer pHashes inserted successfully")
