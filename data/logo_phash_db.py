# data/logo_phash_db.py

from imagehash import hex_to_hash

"""
IMPORTANT:
These hashes MUST be generated from the SAME crop logic
used in phash.py (certificate logo region),
NOT from raw logo PNGs.
"""

def load_logo_phashes():
    return {
        # ✅ Unstop logo hash (generated from certificate crop)
        "unstop": hex_to_hash("b8c3c73c30c9cc67")
    }
