"""Table detection and structure extraction from OCR results."""

from typing import List, Dict, Tuple
import re
from collections import defaultdict


def detect_table_regions(ocr_results: List[Dict], min_rows: int = 3, min_cols: int = 2) -> List[Dict]:
    """
    Detect table-like structures from OCR bounding boxes.
    
    This function groups OCR text boxes that appear to form a table structure
    based on their alignment and proximity.
    
    Args:
        ocr_results: List of OCR results with bounding boxes
        min_rows: Minimum number of rows to consider it a table
        min_cols: Minimum number of columns to consider it a table
    
    Returns:
        List of detected table regions with structured data
    """
    if not ocr_results:
        return []
    
    # Group text by approximate row (similar y-coordinates)
    rows = defaultdict(list)
    row_tolerance = 25  # pixels - increased tolerance for better row grouping
    
    for item in ocr_results:
        # Find which row this item belongs to
        y_center = item['top'] + item['height'] // 2
        matched_row = None
        
        for row_y in rows.keys():
            if abs(y_center - row_y) < row_tolerance:
                matched_row = row_y
                break
        
        if matched_row is None:
            matched_row = y_center
        
        rows[matched_row].append(item)
    
    # Sort rows by y-coordinate
    sorted_rows = sorted(rows.items())
    
    # Group items in each row by x-coordinate to form columns
    table_data = []
    for row_y, items in sorted_rows:
        # Sort items in row by x-coordinate
        sorted_items = sorted(items, key=lambda x: x['left'])
        
        # Extract text values, but merge cells that are very close together
        # This helps when OCR splits a single value into multiple cells
        row_text = []
        prev_item = None
        col_tolerance = 30  # pixels
        
        for item in sorted_items:
            if prev_item and (item['left'] - prev_item['left'] - prev_item['width']) < col_tolerance:
                # Merge with previous cell if they're very close
                row_text[-1] = row_text[-1] + item['text']
            else:
                row_text.append(item['text'])
            prev_item = item
        
        if row_text:  # Skip empty rows
            table_data.append(row_text)
    
    return table_data


def is_chemical_composition_table(table_data: List[List[str]], keywords: List[str] = None) -> bool:
    """
    Check if the table appears to be a chemical composition table.
    
    Args:
        table_data: 2D list of table cells
        keywords: List of keywords to search for
    
    Returns:
        True if table appears to be chemical composition, False otherwise
    """
    if keywords is None:
        try:
            from .utils.config import TABLE_KEYWORDS
            keywords = TABLE_KEYWORDS
        except ImportError:
            from utils.config import TABLE_KEYWORDS
            keywords = TABLE_KEYWORDS
    
    # Flatten table and check for keywords
    flat_text = ' '.join([' '.join(row) for row in table_data]).lower()
    
    keyword_matches = sum(1 for keyword in keywords if keyword.lower() in flat_text)
    
    # Check for element symbols
    try:
        from .utils.config import ELEMENT_SYMBOLS
    except ImportError:
        from utils.config import ELEMENT_SYMBOLS
    element_matches = sum(1 for symbol in ELEMENT_SYMBOLS if symbol in flat_text)
    
    # Consider it a composition table if we find keywords or multiple element symbols
    return keyword_matches >= 2 or element_matches >= 3

