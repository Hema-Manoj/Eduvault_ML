# main.py

import os
from utils.image_loader import process_drive_pdf
from stages.ocr import extract_text
from stages.phash import process_phash_for_image
from stages.pdf_name_forensics import run_pdf_name_forensics
from stages.cnn_infer_anomaly import run_cnn_anomaly
from stages.aggregator import aggregate_verdict



def main():
    print("🚀 EduVault verification started")

    link = input("Enter Google Drive PDF link: ").strip()

    # 🔍 STEP 0: PDF Name Forensics (non-blocking)
    pdf_forensics = run_pdf_name_forensics(link)

    print("\n🧾 PDF Name Forensics Result:")
    for k, v in pdf_forensics.items():
        print(f"{k}: {v}")

    # Step 1: Convert PDF → images
    image_paths = process_drive_pdf(link)

    if not image_paths:
        print("❌ No images generated")
        return

    image_path = os.path.abspath(image_paths[0])
    print(f"\n📄 Processing image: {image_path}")

    # Step 2: OCR
    ocr_out = extract_text(image_path)

    if not ocr_out["is_text_found"]:
        print("❌ No text found in certificate")
        return

    print("\n🧠 OCR Extraction Result:")
    print(ocr_out["raw_text"][:1000])
    if len(ocr_out["raw_text"]) > 1000:
        print("\n... [truncated]")

    # Step 3: pHash
    phash_result = process_phash_for_image(
        image_path=image_path,
        ocr_text=ocr_out["raw_text"]
    )

    print("\n🔎 pHash Verification Result:")
    for k, v in phash_result.items():
        print(f"{k}: {v}")

    # Step 4: CNN anomaly detection
    cnn_result = run_cnn_anomaly(image_path)

    print("\n🧠 CNN Anomaly Detection Result:")
    for k, v in cnn_result.items():
        print(f"{k}: {v}")

    # ---------------- FINAL AGGREGATION ----------------
    final_result = aggregate_verdict(
        pdf_forensics,
        phash_result,
        cnn_result
    )
    
    print("\n🧮 FINAL AGGREGATED VERDICT")
    for k, v in final_result.items():
        print(f"{k}: {v}")


    print("\n✅ Pipeline completed")


if __name__ == "__main__":
    main()
