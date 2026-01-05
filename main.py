# main.py

import os
from utils.image_loader import process_drive_pdf
from stages.ocr import extract_text
from stages.phash import process_phash_for_image


def main():
    print("🚀 EduVault verification started")

    link = input("Enter Google Drive PDF link: ").strip()

    # Step 1: Convert PDF → images
    image_paths = process_drive_pdf(link)

    if not image_paths:
        print("❌ No images generated")
        return

    # Step 2: Process first page (certificate)
    image_path = os.path.abspath(image_paths[0])   # ✅ NORMALIZE PATH
    print(f"\n📄 Processing image: {image_path}")

    # Step 3: OCR
    ocr_out = extract_text(image_path)

    if not ocr_out["is_text_found"]:
        print("❌ No text found in certificate")
        return

    # Step 4: pHash + DB logic
    phash_result = process_phash_for_image(
        image_path=image_path,
        ocr_text=ocr_out["raw_text"]
    )

    print("\n🔎 pHash Verification Result:")
    for k, v in phash_result.items():
        print(f"{k}: {v}")

    print("\n✅ Pipeline completed")


if __name__ == "__main__":
    main()
