import tensorflow as tf
import numpy as np
import cv2
from utils.vaildation import is_valid_xray

# Load models
age_model = tf.keras.models.load_model('models/model_age.h5')
gender_model = tf.keras.models.load_model('models/model_gender.h5')


def preprocess_image(path):
    # Add validation check first
    is_valid, msg = is_valid_xray(path)
    if not is_valid:
        raise ValueError(msg)

    img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    img = 255 - img  # Invert image
    img = cv2.resize(img, (128, 128))
    return img.reshape(1, 128, 128, 1) / 255.0

# def preprocess_image(path):
#     img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
#     img = 255 - img  # Invert image
#     img = cv2.resize(img, (128, 128))
#     img = img.reshape(1, 128, 128, 1) / 255.0
#     return img

def predict_age_gender(path):
    img = preprocess_image(path)
    age = int(np.round(age_model.predict(img)[0][0]))
    gender_pred = gender_model.predict(img)[0][0]
    gender = 'Male' if gender_pred > 0.5 else 'Female'
    return age, gender
