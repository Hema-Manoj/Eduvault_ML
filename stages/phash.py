# stages/phash.py

from PIL import Image
import imagehash
import sqlite3
import re

DB_PATH = "data/issuer_phash.db"

# Known issuer keywords
KNOWN_ISSUERS = {
    "cisco_ccna": ["cisco", "ccna", "networking academy"],
    "linkedin_learning": ["linkedin learning"],
    "microsoft": ["microsoft", "azure"],
    "nptel": ["nptel", "iit"],
    "udemy": ["udemy"],
    "unstop": ["unstop"]
}

HAMMING_THRESHOLD = 10


# ------------------ HASH UTILS ------------------

def compute_phash(image_path: str) -> str:
    image = Image.open(image_path)
    return str(imagehash.phash(image))


def hamming_distance(hash1: str, hash2: str) -> int:
    return imagehash.hex_to_hash(hash1) - imagehash.hex_to_hash(hash2)


# ------------------ ISSUER DETECTION ------------------

def detect_issuer(ocr_text: str) -> str:
    text = ocr_text.lower()

    for issuer_id, keywords in KNOWN_ISSUERS.items():
        for kw in keywords:
            if kw in text:
                return issuer_id

    return "unknown"


def get_next_unknown_id():
    """
    Generates unknown_1, unknown_2, unknown_3 ...
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT issuer_id FROM issuer_phash
        WHERE issuer_id LIKE 'unknown_%'
    """)

    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return "unknown_1"

    nums = [int(re.findall(r'\d+', r[0])[0]) for r in rows if re.findall(r'\d+', r[0])]
    return f"unknown_{max(nums) + 1}"


# ------------------ DB HELPERS ------------------

def get_issuer_phash(issuer_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT phash FROM issuer_phash WHERE issuer_id = ?",
        (issuer_id,)
    )
    row = cursor.fetchone()
    conn.close()

    return row[0] if row else None


def insert_new_issuer(issuer_id, issuer_name, phash):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO issuer_phash (issuer_id, issuer_name, phash)
        VALUES (?, ?, ?)
    """, (issuer_id, issuer_name, phash))

    conn.commit()
    conn.close()


# ------------------ MAIN PIPELINE ------------------

def process_phash_for_image(image_path: str, ocr_text: str) -> dict:
    detected_issuer = detect_issuer(ocr_text)
    current_phash = compute_phash(image_path)

    # -------- UNKNOWN ISSUER --------
    if detected_issuer == "unknown":
        unique_unknown_id = get_next_unknown_id()

        insert_new_issuer(
            unique_unknown_id,
            "Unknown Issuer",
            current_phash
        )

        return {
            "issuer_id": unique_unknown_id,
            "phash": current_phash,
            "baseline_exists": False,
            "phash_verdict": "UNKNOWN_BASELINE_CREATED"
        }

    # -------- KNOWN ISSUER --------
    baseline_phash = get_issuer_phash(detected_issuer)

    # First time seeing this known issuer
    if baseline_phash is None:
        insert_new_issuer(
            detected_issuer,
            detected_issuer.replace("_", " ").title(),
            current_phash
        )

        return {
            "issuer_id": detected_issuer,
            "phash": current_phash,
            "baseline_exists": False,
            "phash_verdict": "BASELINE_CREATED"
        }

    # Compare visually
    distance = hamming_distance(current_phash, baseline_phash)

    verdict = (
        "VISUALLY_MATCHING"
        if distance <= HAMMING_THRESHOLD
        else "VISUALLY_SUSPICIOUS"
    )

    return {
        "issuer_id": detected_issuer,
        "phash": current_phash,
        "baseline_exists": True,
        "baseline_phash": baseline_phash,
        "hamming_distance": distance,
        "phash_verdict": verdict
    }
