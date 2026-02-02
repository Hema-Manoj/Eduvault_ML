# stages/cnn_train_anomaly.py

import os
import joblib
import torch
import numpy as np
from sklearn.ensemble import IsolationForest

from stages.cnn_anomaly import (
    load_feature_extractor,
    preprocess_image
)

# ---------------- CONFIG ----------------

TRAIN_DIR = "cnn_training_data/normal"
MODEL_OUT = "data/cnn_anomaly_model.pkl"

# ---------------------------------------


def load_training_images():
    images = []
    for fname in os.listdir(TRAIN_DIR):
        if fname.lower().endswith((".png", ".jpg", ".jpeg")):
            images.append(os.path.join(TRAIN_DIR, fname))
    return images


def extract_embeddings(model, image_paths):
    embeddings = []

    model.eval()
    with torch.no_grad():
        for path in image_paths:
            x = preprocess_image(path)
            features = model(x)
            embeddings.append(features.squeeze(0).numpy())

    return np.array(embeddings)


def train_anomaly_model(embeddings):
    model = IsolationForest(
        n_estimators=200,
        contamination=0.1,   # conservative
        random_state=42
    )
    model.fit(embeddings)
    return model


if __name__ == "__main__":
    print("🚀 Training CNN Anomaly Model")

    # 1️⃣ Load CNN feature extractor
    cnn = load_feature_extractor()

    # 2️⃣ Load training images
    image_paths = load_training_images()
    print(f"📸 Found {len(image_paths)} training images")

    # 3️⃣ Extract embeddings
    embeddings = extract_embeddings(cnn, image_paths)
    print("🧠 Embeddings shape:", embeddings.shape)

    # 4️⃣ Train Isolation Forest
    anomaly_model = train_anomaly_model(embeddings)

    # 5️⃣ Save model
    os.makedirs("data", exist_ok=True)
    joblib.dump(anomaly_model, MODEL_OUT)

    print(f"✅ Anomaly model saved to {MODEL_OUT}")
