"""Image preprocessing utilities for OCR improvement."""

import numpy as np
from PIL import Image
import cv2


def preprocess_image(image: Image.Image, denoise: bool = True, enhance_contrast: bool = True) -> Image.Image:
    """
    Preprocess image to improve OCR accuracy.
    
    Args:
        image: PIL Image to preprocess
        denoise: Whether to apply denoising
        enhance_contrast: Whether to enhance contrast
    
    Returns:
        Preprocessed PIL Image
    """
    # Convert PIL Image to OpenCV format (numpy array)
    img_array = np.array(image)
    
    # Convert RGB to BGR for OpenCV
    if len(img_array.shape) == 3 and img_array.shape[2] == 3:
        img_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
    
    # Convert to grayscale if color image
    if len(img_array.shape) == 3:
        gray = cv2.cvtColor(img_array, cv2.COLOR_BGR2GRAY)
    else:
        gray = img_array
    
    # Denoise
    if denoise:
        gray = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)
    
    # Enhance contrast using CLAHE (Contrast Limited Adaptive Histogram Equalization)
    if enhance_contrast:
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        gray = clahe.apply(gray)
    
    # Convert back to PIL Image
    return Image.fromarray(gray)







