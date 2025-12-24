import cv2
import easyocr

# Initialize OCR model once (faster)
reader = easyocr.Reader(['en'], gpu=False)


def preprocess_image(image_path):
    """Clean the image for better OCR accuracy."""
    img = cv2.imread(image_path)

    if img is None:
        raise ValueError(f"❌ Could not load image: {image_path}")

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    thresh = cv2.adaptiveThreshold(
        blur, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        11,
        2
    )

    return thresh


def extract_text(image_path):
    """Run OCR and return structured output."""
    processed = preprocess_image(image_path)
    results = reader.readtext(processed)

    raw_text = " ".join([r[1] for r in results])

    return {
        "text_blocks": [
            {
                "bbox": r[0],
                "text": r[1],
                "confidence": r[2]
            } for r in results
        ],
        "raw_text": raw_text,
        "is_text_found": len(results) > 0
    }
