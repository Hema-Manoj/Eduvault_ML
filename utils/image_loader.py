import os
import requests
from pdf2image import convert_from_path
from urllib.parse import urlparse, parse_qs

# Import OCR from stages folder
from eduvault_ml.stages.ocr import extract_text

POPPLER_PATH = r"C:\poppler\Library\bin"


def extract_file_id(drive_link):
    """Extract FILE_ID from any Google Drive link."""
    if "id=" in drive_link:
        return parse_qs(urlparse(drive_link).query)["id"][0]
    elif "/d/" in drive_link:
        return drive_link.split("/d/")[1].split("/")[0]
    else:
        raise ValueError("Invalid Google Drive link")


def download_pdf_temp(drive_link, file_id):
    """Download PDF temporarily (will be deleted after PNG conversion)."""
    url = f"https://drive.google.com/uc?export=download&id={file_id}"
    temp_pdf = f"temp_{file_id}.pdf"

    print(f"⬇ Downloading PDF ({file_id})...")

    response = requests.get(url, stream=True)
    response.raise_for_status()

    with open(temp_pdf, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)

    return temp_pdf


def pdf_to_images(pdf_path, file_id, output_folder="../utils/output_images"):
    """Convert PDF → PNG and DELETE the PDF afterwards."""
    os.makedirs(output_folder, exist_ok=True)

    print("🖼 Converting PDF to PNG...")

    images = convert_from_path(
        pdf_path,
        dpi=300,
        poppler_path=POPPLER_PATH
    )

    output_paths = []

    for i, img in enumerate(images, start=1):
        out_path = os.path.join(output_folder, f"{file_id}_page_{i}.png")
        img.save(out_path, "PNG")
        output_paths.append(out_path)

    print(f"✅ Saved {len(images)} PNG files in {output_folder}")

    # Delete the temporary PDF
    if os.path.exists(pdf_path):
        os.remove(pdf_path)
        print(f"🗑 Deleted temporary PDF: {pdf_path}")

    return output_paths


def process_drive_pdf(drive_link):
    """Main function: Drive link → temp PDF → PNG → OCR → delete PDF."""
    file_id = extract_file_id(drive_link)

    # Step 1: Download PDF
    temp_pdf_path = download_pdf_temp(drive_link, file_id)

    # Step 2: Convert PDF → PNG
    png_paths = pdf_to_images(temp_pdf_path, file_id)

    # Step 3: Auto-run OCR on FIRST page
    print("\n🔍 Running OCR on first page...")
    ocr_output = extract_text(png_paths[0])

    return png_paths, ocr_output


if __name__ == "__main__":
    link = input("Enter Google Drive PDF link: ").strip()
    paths, ocr_out = process_drive_pdf(link)

    print("\n============================")
    print("📁 Generated PNG files:")
    for p in paths:
        print(" →", p)

    print("\n📝 OCR RAW TEXT:")
    print("--------------------------------")
    print(ocr_out["raw_text"])

    print("\n🔍 OCR TEXT BLOCKS:")
    print("--------------------------------")
    for block in ocr_out["text_blocks"]:
        print(f"Text: {block['text']} | Confidence: {block['confidence']:.2f}")

    print("\n📌 Text Found?:", ocr_out["is_text_found"])
    print("============================")
