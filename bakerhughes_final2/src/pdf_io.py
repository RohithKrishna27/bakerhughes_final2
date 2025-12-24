"""PDF input/output operations for extracting images from PDF files."""

import os
from typing import List
from PIL import Image
import fitz  # PyMuPDF


def extract_images_from_pdf(pdf_path: str, dpi: int = 300) -> List[Image.Image]:
    """
    Extract all pages from PDF as images.
    
    Args:
        pdf_path: Path to the PDF file
        dpi: Resolution for image conversion (dots per inch)
    
    Returns:
        List of PIL Image objects, one per page
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    
    images = []
    try:
        # Use PyMuPDF (fitz) to convert PDF pages to images
        doc = fitz.open(pdf_path)
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            # Convert page to image with specified DPI
            mat = fitz.Matrix(dpi / 72, dpi / 72)  # 72 is default DPI
            pix = page.get_pixmap(matrix=mat)
            
            # Convert to PIL Image
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            images.append(img)
        
        doc.close()
        return images
    
    except Exception as e:
        raise RuntimeError(f"Error extracting images from PDF: {str(e)}")







