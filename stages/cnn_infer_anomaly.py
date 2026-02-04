# stages/cnn_infer_anomaly.py

import torch
import joblib
from pathlib import Path

from stages.cnn_anomaly import (
    load_feature_extractor,
    preprocess_image
)

# ---------------- CONFIG ----------------

MODEL_PATH = "data/cnn_anomaly_model.pkl"

NORMAL_THRESHOLD = 0.06
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


# ---------------- PIPELINE FUNCTION ----------------

def run_cnn_anomaly(image_path: str) -> dict:
    """
    Image path → CNN anomaly detection
    """

    cnn = load_feature_extractor()
    anomaly_model = load_anomaly_model()

    x = preprocess_image(image_path)

    with torch.no_grad():
        embedding = cnn(x).numpy()

    score = anomaly_model.decision_function(embedding)[0]
    verdict = get_anomaly_verdict(score)

    return {
        "cnn_anomaly_score": float(score),
        "cnn_anomaly_verdict": verdict
    }
