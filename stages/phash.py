from PIL import Image
import imagehash
import sqlite3
import re

DB_PATH = "data/issuer_phash.db"

# ------------------ ISSUER KEYWORDS ------------------

KNOWN_ISSUERS = {
    "cisco_ccna": ["cisco", "ccna", "networking academy"],
    "linkedin_learning": ["linkedin learning"],
    "microsoft": ["microsoft", "azure"],
    "nptel": ["nptel", "iit"],
    "udemy": ["udemy"],
    "eduskills": ["eduskills", "edu skills"],
    "aws": ["amazon web services", "aws"],
    "mongodb": ["mongodb", "mongo db", "mongo"],
}

HAMMING_THRESHOLD = 10


# ------------------ HASH UTILS ------------------

def compute_phash(image_path: str) -> str:
    image = Image.open(image_path).convert("RGB")
    return str(imagehash.phash(image))


def hamming_distance(hash1: str, hash2: str) -> int:
    return imagehash.hex_to_hash(hash1) - imagehash.hex_to_hash(hash2)


# ------------------ LOGO ISSUER DETECTION ------------------

def detect_issuer_from_logo(image_path: str):
    """
    ONLY used to identify issuer (not for visual comparison)
    """
    from data.logo_phash_db import load_logo_phashes

    image = Image.open(image_path).convert("RGB")
    w, h = image.size

    # 🔥 Conservative logo crop (top-left)
    logo_region = image.crop((
        int(w * 0.02),
        int(h * 0.02),
        int(w * 0.25),
        int(h * 0.18)
    ))

    region_hash = imagehash.phash(logo_region)
    logo_hashes = load_logo_phashes()

    for issuer, logo_hash in logo_hashes.items():
        distance = region_hash - logo_hash
        if distance <= 40:  # relaxed for logo-only match
            return issuer

    return None


# ------------------ OCR + LOGO ISSUER DETECTION ------------------

def detect_issuer(ocr_text: str, image_path: str) -> str:
    text = ocr_text.lower()

    # 1️⃣ OCR-based detection
    for issuer_id, keywords in KNOWN_ISSUERS.items():
        for kw in keywords:
            if kw in text:
                return issuer_id

    # 2️⃣ Logo-based detection (Unstop)
    logo_issuer = detect_issuer_from_logo(image_path)
    if logo_issuer:
        return logo_issuer

    return "unknown"


# ------------------ DB HELPERS ------------------

def get_next_unknown_id():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        SELECT issuer_id FROM issuer_phash
        WHERE issuer_id LIKE 'unknown_%'
    """)
    rows = cur.fetchall()
    conn.close()

    if not rows:
        return "unknown_1"

    nums = [int(re.findall(r"\d+", r[0])[0]) for r in rows]
    return f"unknown_{max(nums) + 1}"


def get_all_issuer_phashes(issuer_prefix):
    """
    Returns ALL template phashes for an issuer.
    Example: unstop_t1, unstop_t2, ...
    """
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        SELECT issuer_id, phash
        FROM issuer_phash
        WHERE issuer_id LIKE ?
    """, (f"{issuer_prefix}%",))

    rows = cur.fetchall()
    conn.close()
    return rows


def insert_new_issuer(issuer_id, issuer_name, phash):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        INSERT OR REPLACE INTO issuer_phash (issuer_id, issuer_name, phash)
        VALUES (?, ?, ?)
    """, (issuer_id, issuer_name, phash))

    conn.commit()
    conn.close()


# ------------------ MAIN pHASH PIPELINE ------------------

def process_phash_for_image(image_path: str, ocr_text: str) -> dict:
    detected_issuer = detect_issuer(ocr_text, image_path)
    current_phash = compute_phash(image_path)

    # -------- UNKNOWN ISSUER --------
    if detected_issuer == "unknown":
        uid = get_next_unknown_id()
        insert_new_issuer(uid, "Unknown Issuer", current_phash)

        return {
            "issuer_id": uid,
            "phash": current_phash,
            "baseline_exists": False,
            "phash_verdict": "UNKNOWN_BASELINE_CREATED"
        }

    # -------- MULTI-TEMPLATE COMPARISON --------
    baselines = get_all_issuer_phashes(detected_issuer)

    if not baselines:
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

    # Compare against ALL templates
    distances = []
    for template_id, base_phash in baselines:
        dist = hamming_distance(current_phash, base_phash)
        distances.append((template_id, dist))

    best_template, best_distance = min(distances, key=lambda x: x[1])

    verdict = (
        "VISUALLY_MATCHING"
        if best_distance <= HAMMING_THRESHOLD
        else "VISUALLY_SUSPICIOUS"
    )

    return {
        "issuer_id": detected_issuer,
        "matched_template": best_template,
        "phash": current_phash,
        "baseline_exists": True,
        "hamming_distance": best_distance,
        "phash_verdict": verdict
    }
