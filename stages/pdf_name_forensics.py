# stages/pdf_name_forensics.py

import fitz  # PyMuPDF
import os
import requests
from urllib.parse import urlparse, parse_qs

# ---------------- CONFIG ----------------

TEMP_DIR = "temp_pdfs"
os.makedirs(TEMP_DIR, exist_ok=True)

CANVA_KEYWORDS = ["canva"]
STRONG_EDIT_THRESHOLD = 5
SUSPICIOUS_THRESHOLD = 3


# ---------------- GOOGLE DRIVE ----------------

def extract_drive_file_id(link: str) -> str:
    if "drive.google.com" not in link:
        raise ValueError("Not a Google Drive link")

    if "/file/d/" in link:
        return link.split("/file/d/")[1].split("/")[0]

    parsed = urlparse(link)
    return parse_qs(parsed.query).get("id", [None])[0]


def download_pdf_from_drive(link: str) -> str:
    file_id = extract_drive_file_id(link)
    if not file_id:
        raise ValueError("Unable to extract file ID")

    url = f"https://drive.google.com/uc?export=download&id={file_id}"
    out_path = os.path.join(TEMP_DIR, f"temp_{file_id}.pdf")

    r = requests.get(url, stream=True)
    r.raise_for_status()

    with open(out_path, "wb") as f:
        for chunk in r.iter_content(8192):
            f.write(chunk)

    return out_path


# ---------------- FORENSICS ----------------

def get_pdf_producer(doc):
    meta = doc.metadata or {}
    return ((meta.get("producer") or "") + (meta.get("creator") or "")).lower()


def find_largest_text_span(page):
    spans = []
    for b in page.get_text("dict").get("blocks", []):
        if b.get("type") != 0:
            continue
        for line in b.get("lines", []):
            for span in line.get("spans", []):
                text = span.get("text", "").strip()
                if len(text) >= 3:
                    spans.append(span)

    spans.sort(key=lambda s: s.get("size", 0), reverse=True)
    return spans[0] if spans else None


def analyze_pdf_name_region(pdf_path):
    doc = fitz.open(pdf_path)
    page = doc[0]

    score = 0
    reasons = []

    # 1️⃣ Producer metadata (STRONG)
    producer = get_pdf_producer(doc)
    if any(k in producer for k in CANVA_KEYWORDS):
        score += 4
        reasons.append("PDF metadata indicates Canva")

    # 2️⃣ Name detection
    name_span = find_largest_text_span(page)
    if not name_span:
        return {
            "verdict": "UNKNOWN",
            "forensic_score": 0,
            "reason": "Name text not found"
        }

    name_text = name_span.get("text", "").strip()
    name_font = name_span.get("font", "UNKNOWN")
    name_size = round(name_span.get("size", 0), 2)

    # 3️⃣ Font embedding (WEAK)
    embedded_fonts = []
    for p in doc:
        for f in p.get_fonts():
            embedded_fonts.append(f[3])

    if not any(name_font in f for f in embedded_fonts):
        score += 1
        reasons.append("Name font not embedded")

    # 4️⃣ Object order (MEDIUM)
    blocks = page.get_text("rawdict").get("blocks", [])
    name_block_index = None

    for i, b in enumerate(blocks):
        if b.get("type") != 0:
            continue
        for line in b.get("lines", []):
            for span in line.get("spans", []):
                if span.get("text", "").strip() == name_text:
                    name_block_index = i
                    break

    if name_block_index is not None and name_block_index > len(blocks) * 0.7:
        score += 2
        reasons.append("Name text added late in PDF structure")

    # 5️⃣ Raster presence (WEAK)
    if page.get_images(full=True):
        score += 1
        reasons.append("Raster elements near text")

    # Verdict
    if score >= STRONG_EDIT_THRESHOLD:
        verdict = "LIKELY_EDITED"
    elif score >= SUSPICIOUS_THRESHOLD:
        verdict = "SUSPICIOUS"
    else:
        verdict = "LIKELY_ORIGINAL"

    return {
        "verdict": verdict,
        "forensic_score": score,
        "name_text": name_text,
        "name_font": name_font,
        "name_size": name_size,
        "reasons": reasons
    }


# ---------------- PIPELINE ENTRY ----------------

def run_pdf_name_forensics(drive_link: str) -> dict:
    pdf_path = download_pdf_from_drive(drive_link)
    try:
        result = analyze_pdf_name_region(pdf_path)
    finally:
        if os.path.exists(pdf_path):
            os.remove(pdf_path)

    return result
