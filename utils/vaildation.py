import cv2
import numpy as np


def is_valid_xray(image_path):
    """Check if image has X-ray characteristics"""
    try:
        img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)

        # Basic checks
        if img is None:
            return False, "Cannot read image file"

        if img.shape[0] < 512 or img.shape[1] < 512:  # X-rays are typically large
            return False, "Image resolution too low for X-ray analysis"

        # Histogram analysis
        hist = cv2.calcHist([img], [0], None, [256], [0, 256])
        peak = np.argmax(hist)

        # X-rays typically have most pixels in darker ranges
        if peak > 150:  # Adjust based on your dataset
            return False, "Image does not appear to be an X-ray"

        return True, "Valid X-ray"

    except Exception as e:
        return False, f"Validation error: {str(e)}"