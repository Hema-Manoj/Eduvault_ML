# stages/cnn_anomaly.py

import torch
import torch.nn as nn
from torchvision import models


def load_feature_extractor():
    """
    Loads a pretrained ResNet18 model
    and removes the final classification layer.
    Output: 512-D feature vector
    """

    # Load pretrained ResNet18
    model = models.resnet18(weights=models.ResNet18_Weights.DEFAULT)

    # Remove final classification layer (fc)
    model.fc = nn.Identity()

    # Set model to evaluation mode
    model.eval()

    return model

from PIL import Image
from torchvision import transforms


def get_preprocess_transform():
    """
    Returns preprocessing pipeline compatible with ImageNet CNNs
    """
    return transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225]
        )
    ])


def preprocess_image(image_path):
    """
    Loads and preprocesses a certificate image
    """
    image = Image.open(image_path).convert("RGB")
    transform = get_preprocess_transform()
    tensor = transform(image)

    # Add batch dimension → (1, 3, 224, 224)
    return tensor.unsqueeze(0)



if __name__ == "__main__":
    model = load_feature_extractor()

    image_path = "output_images/unstop_sample.png" #IMAGE PATH !

    x = preprocess_image(image_path)

    with torch.no_grad():
        features = model(x)

    print("Feature vector shape:", features.shape)

