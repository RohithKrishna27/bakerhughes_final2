"""Image input/output operations - supports both PDF and image files."""

import os
from typing import List, Union
from PIL import Image
import fitz  # PyMuPDF


def load_images(input_path: str, dpi: int = 300) -> List[Image.Image]:
    """
    Load images from PDF or image file.
    
    Args:
        input_path: Path to PDF or image file
        dpi: Resolution for PDF conversion (dots per inch)
    
    Returns:
        List of PIL Image objects
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"File not found: {input_path}")
    
    images = []
    
    # Check file extension
    ext = os.path.splitext(input_path)[1].lower()
    
    if ext == '.pdf':
        # Extract from PDF
        try:
            doc = fitz.open(input_path)
            for page_num in range(len(doc)):
                page = doc[page_num]
                mat = fitz.Matrix(dpi / 72, dpi / 72)
                pix = page.get_pixmap(matrix=mat)
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                images.append(img)
            doc.close()
        except Exception as e:
            raise RuntimeError(f"Error extracting images from PDF: {str(e)}")
    
    elif ext in ['.png', '.jpg', '.jpeg', '.tiff', '.tif', '.bmp']:
        # Load image directly
        try:
            img = Image.open(input_path)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            images.append(img)
        except Exception as e:
            raise RuntimeError(f"Error loading image: {str(e)}")
    
    else:
        raise ValueError(f"Unsupported file format: {ext}. Use PDF, PNG, JPG, or TIFF.")
    
    return images







