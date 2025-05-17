import tensorflow as tf
import numpy as np
import cv2
from utils.vaildation import is_valid_xray
# Load model
pneumonia_model = tf.keras.models.load_model('models/pneumonia_model (1).h5')

#def preprocess_image(path):
#     img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
#     img = cv2.resize(img, (150, 150))
#     img = img.reshape(1, 150, 150, 1) / 255.0
#     return img

def preprocess_image(path):
    # Add validation check first
    is_valid, msg = is_valid_xray(path)
    if not is_valid:
        raise ValueError(msg)

    img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    img = cv2.resize(img, (150, 150))
    return img.reshape(1, 150, 150, 1) / 255.0

def predict_pneumonia(path):
    img = preprocess_image(path)
    pred = pneumonia_model.predict(img)[0][0]
    label = 'PNEUMONIA' if pred > 0.5 else 'NORMAL'
    confidence = pred * 100 if pred > 0.5 else (1 - pred) * 100
    return label, confidence
