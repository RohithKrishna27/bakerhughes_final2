"""OCR operations using Tesseract."""

import pytesseract
from PIL import Image
from typing import Dict, List, Tuple
import re
import os

# Try to find Tesseract in common Windows installation locations
if os.name == 'nt':  # Windows
    common_paths = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        r"C:\Tesseract-OCR\tesseract.exe",
    ]
    for path in common_paths:
        if os.path.exists(path):
            pytesseract.pytesseract.tesseract_cmd = path
            break


def extract_text_with_boxes(image: Image.Image, lang: str = 'eng') -> List[Dict]:
    """
    Extract text with bounding box coordinates using Tesseract OCR.
    
    Args:
        image: PIL Image to perform OCR on
        lang: Language code for OCR (default: 'eng')
    
    Returns:
        List of dictionaries with 'text', 'left', 'top', 'width', 'height', 'conf' keys
    """
    try:
        # Get detailed data including bounding boxes
        data = pytesseract.image_to_data(image, lang=lang, output_type=pytesseract.Output.DICT)
        
        # Extract relevant information
        results = []
        n_boxes = len(data['text'])
        
        for i in range(n_boxes):
            text = data['text'][i].strip()
            conf = int(data['conf'][i])
            
            # Skip empty text and low confidence detections
            if text and conf > 0:
                results.append({
                    'text': text,
                    'left': data['left'][i],
                    'top': data['top'][i],
                    'width': data['width'][i],
                    'height': data['height'][i],
                    'conf': conf
                })
        
        return results
    
    except Exception as e:
        raise RuntimeError(f"OCR extraction failed: {str(e)}")


def extract_text_simple(image: Image.Image, lang: str = 'eng') -> str:
    """
    Simple text extraction without bounding boxes.
    
    Args:
        image: PIL Image to perform OCR on
        lang: Language code for OCR
    
    Returns:
        Extracted text as string
    """
    try:
        return pytesseract.image_to_string(image, lang=lang)
    except Exception as e:
        raise RuntimeError(f"OCR extraction failed: {str(e)}")

