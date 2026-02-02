# stages/cnn_infer_anomaly.py

import torch
import joblib
from pathlib import Path

from stages.cnn_anomaly import (
    load_feature_extractor,
    preprocess_image
)

from utils.image_loader import process_drive_pdf

# ---------------- CONFIG ----------------

MODEL_PATH = "data/cnn_anomaly_model.pkl"

# Thresholds (can be tuned later)
NORMAL_THRESHOLD = 0.05
UNUSUAL_THRESHOLD = -0.05


# ---------------- MODEL LOADERS ----------------

def load_anomaly_model():
    if not Path(MODEL_PATH).exists():
        raise FileNotFoundError("❌ CNN anomaly model not found. Train it first.")

    return joblib.load(MODEL_PATH)


def get_anomaly_verdict(score: float) -> str:
    """
    IsolationForest:
    Higher score = more normal
    Lower score = more anomalous
    """
    if score >= NORMAL_THRESHOLD:
        return "NORMAL"
    elif score >= UNUSUAL_THRESHOLD:
        return "UNUSUAL"
    else:
        return "SUSPICIOUS"


# ---------------- MAIN PIPELINE ----------------

def run_cnn_anomaly_from_drive(drive_link: str) -> dict:
    """
    Drive link → PDF → PNG → CNN anomaly detection
    """

    # 1️⃣ Convert PDF → PNG (first page only)
    image_paths = process_drive_pdf(drive_link)

    if not image_paths:
        raise RuntimeError("❌ No images generated from PDF")

    image_path = image_paths[0]  # use first page

    # 2️⃣ Load models
    cnn = load_feature_extractor()
    anomaly_model = load_anomaly_model()

    # 3️⃣ Preprocess image
    x = preprocess_image(image_path)

    # 4️⃣ Extract embedding
    with torch.no_grad():
        embedding = cnn(x).numpy()  # shape: (1, 512)

    # 5️⃣ Compute anomaly score
    score = anomaly_model.decision_function(embedding)[0]
    verdict = get_anomaly_verdict(score)

    return {
        "image_used": image_path,
        "anomaly_score": float(score),
        "anomaly_verdict": verdict
    }


# ---------------- TEST ----------------

if __name__ == "__main__":
    link = input("Enter Google Drive PDF link: ").strip()

    result = run_cnn_anomaly_from_drive(link)

    print("\n🧠 CNN Anomaly Detection Result:")
    for k, v in result.items():
        print(f"{k}: {v}")
