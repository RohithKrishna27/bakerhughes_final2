"""Parsing utilities for extracting chemical composition data from table structures."""

import re
from typing import List, Dict, Optional, Tuple

# Handle relative and absolute imports
try:
    from .utils.config import ELEMENT_SYMBOLS, COMPOSITION_UNITS
except ImportError:
    from utils.config import ELEMENT_SYMBOLS, COMPOSITION_UNITS

# Priority elements to extract (6-8 elements, starting with Al and V)
PRIORITY_ELEMENTS = ['Al', 'V', 'Fe', 'C', 'N', 'O', 'Y', 'H']
ELEMENT_ORDER = {elem: idx for idx, elem in enumerate(PRIORITY_ELEMENTS)}


def infer_decimal_placement(value_str: str, is_trace_element: bool = False) -> Optional[float]:
    """
    Intelligently infer where decimal point should be based on value characteristics.
    
    Args:
        value_str: Numeric string without decimal point
        is_trace_element: Whether this is a trace element (indicated by < prefix)
    
    Returns:
        Float with corrected decimal placement or None
    """
    try:
        # Remove any non-digit characters except minus
        clean_str = re.sub(r'[^\d\-]', '', value_str)
        if not clean_str or clean_str == '-':
            return None
            
        num = int(clean_str)
        
        # For trace elements (< prefix), values should be very small
        if is_trace_element:
            if num < 10:  # 1 -> 0.001
                return num / 1000
            elif num < 100:  # 11 -> 0.0011, 25 -> 0.0025
                return num / 10000
            elif num < 1000:  # 190 -> 0.0019 or 0.19 depending on context
                return num / 10000
            else:  # 1900 -> 0.0019
                return num / 1000000
        
        # For regular elements, use statistical heuristics
        # Most composition values are 0.001% to 20%
        
        if num == 0:
            return 0.0
            
        # Single digit: likely 1 -> 1.0 or could be 0.1
        if num < 10:
            # Keep as is for major elements (1-9%)
            return float(num)
        
        # Two digits: 19 -> 0.19, 25 -> 0.25, 86 -> 0.86, but 65 could be 6.5
        elif num < 100:
            # If number is divisible by 10, might be X.0
            if num % 10 == 0:  # 50 -> 5.0
                return num / 10
            # Check if last digit suggests decimal: 19 -> 0.19, 25 -> 0.25
            # Most values < 1%, so prefer 0.XX interpretation
            if num < 30:  # 19, 25 -> 0.19, 0.25
                return num / 100
            else:  # 65, 86 -> could be 6.5, 8.6 or 0.65, 0.86
                # Use middle-ground: prefer single decimal (6.5 > 0.65)
                return num / 10
        
        # Three digits: 654 -> 6.54, 408 -> 4.08, 190 -> 1.90, 050 -> 0.050
        elif num < 1000:
            if num < 100:  # 050 -> 0.050 or 0.50
                if num < 10:  # 005 -> 0.005
                    return num / 1000
                else:  # 050 -> 0.050
                    return num / 1000
            elif num < 200:  # 190 -> 1.90, 119 -> 1.19
                return num / 100
            else:  # 654 -> 6.54, 408 -> 4.08
                return num / 100
        
        # Four digits: 0050 -> 0.0050, 0025 -> 0.0025, 0011 -> 0.0011
        elif num < 10000:
            if num < 100:  # 0050 -> 0.0050, 0025 -> 0.0025
                return num / 10000
            elif num < 1000:  # 0190 -> 0.0190
                return num / 10000
            else:  # 6540 -> 6.540 or 65.40
                return num / 1000
        
        # Five or more digits: likely very precise measurements
        else:
            # 00050 -> 0.00050
            return num / (10 ** (len(clean_str) - 1))
            
    except (ValueError, TypeError):
        return None


def normalize_number(value: str) -> Optional[float]:
    """
    Normalize numeric values from text, handling locale differences and OCR errors.
    
    Args:
        value: String representation of number (may have comma as decimal separator)
    
    Returns:
        Float value or None if not parseable
    """
    if not value or not isinstance(value, str):
        return None
    
    # Remove whitespace
    value = value.strip()
    
    # Handle "<" prefix (trace elements) - keep the value but mark it's a trace
    is_trace = value.startswith('<')
    if is_trace:
        value = value[1:].strip()
    
    # Replace comma with dot for decimal separator
    value = value.replace(',', '.')
    
    # Handle percentage signs - they don't change the numeric value
    value = value.replace('%', '')
    
    # Remove spaces between digits (OCR artifacts)
    value = re.sub(r'(\d)\s+(\d)', r'\1\2', value)
    
    # If already has decimal point, try to parse directly
    if '.' in value:
        try:
            num = float(value)
            # Validate range - if > 100, might need adjustment
            if num > 100 and not is_trace:
                # Try dividing by 10 or 100
                if num > 1000:
                    return num / 1000
                else:
                    return num / 10
            return num
        except (ValueError, TypeError):
            # Fall through to inference logic
            value = value.replace('.', '')
    
    # Remove non-numeric characters except minus sign
    value = re.sub(r'[^\d\-]', '', value)
    
    if not value or value == '-':
        return None
    
    # Use intelligent decimal placement inference
    return infer_decimal_placement(value, is_trace)


def is_valid_composition_value(value: float, unit: str) -> bool:
    """
    Validate if a composition value is reasonable.
    
    Args:
        value: The numeric value
        unit: The unit (e.g., 'wt.%')
    
    Returns:
        True if value seems reasonable, False otherwise
    """
    if unit in ['wt.%', 'wt%', '%', 'weight%', 'mass%']:
        # For percentage values, typically should be 0-100
        # Allow some tolerance but reject obvious errors
        if value < 0:
            return abs(value) < 0.1  # Allow very small negatives (likely OCR error)
        # Most elements are < 50%, but allow up to 100% for major elements
        return 0 <= value <= 100
    # For other units, allow wider range
    return value >= 0


def extract_element_symbol(text: str) -> Optional[str]:
    """
    Extract element symbol from text (only priority elements).
    
    Args:
        text: Text that may contain an element symbol
    
    Returns:
        Element symbol if found and in priority list, None otherwise
    """
    text = text.strip()
    
    # Handle common OCR errors
    ocr_corrections = {
        'Kin': 'Mn',  # 'Kin' is often OCR misread of 'Mn'
        'kin': 'Mn',
        '5': 'S',  # '5' can be misread 'S' in context
        'Oe': None,  # Likely OCR error
        'c': 'C',  # lowercase c -> C
        'si': 'Si',
        'cr': 'Cr',
        'ni': 'Ni',
        'mo': 'Mo',
        'cu': 'Cu',
        'nb': 'Nb',
        'al': 'Al',
        'fe': 'Fe',
        'ti': 'Ti',
        'v': 'V',
        'n': 'N',
        'o': 'O',
        'h': 'H',
        'y': 'Y',
    }
    
    # Check OCR corrections first
    if text in ocr_corrections:
        corrected = ocr_corrections[text]
        if corrected and corrected in PRIORITY_ELEMENTS:
            return corrected
        elif corrected is None:
            return None
    
    # Check lowercase version
    text_lower = text.lower()
    if text_lower in ocr_corrections:
        corrected = ocr_corrections[text_lower]
        if corrected and corrected in PRIORITY_ELEMENTS:
            return corrected
    
    # Direct match (case-insensitive) - only check priority elements
    if text in PRIORITY_ELEMENTS:
        return text
    
    # Check if text matches element symbol case-insensitively
    for symbol in PRIORITY_ELEMENTS:
        if text.upper() == symbol.upper():
            return symbol
    
    # Check if text starts with an element symbol
    for symbol in PRIORITY_ELEMENTS:
        if text.startswith(symbol) or text_lower.startswith(symbol.lower()):
            return symbol
    
    # Try to find element symbol anywhere in text
    for symbol in PRIORITY_ELEMENTS:
        if symbol in text or symbol.lower() in text_lower:
            return symbol
    
    return None


def extract_unit(text: str) -> str:
    """
    Extract unit from text.
    
    Args:
        text: Text that may contain a unit
    
    Returns:
        Unit string (default: 'wt.%')
    """
    text = text.lower()
    
    for unit in COMPOSITION_UNITS:
        if unit.lower() in text:
            return unit
    
    # Default unit for composition tables
    return 'wt.%'


def parse_table_to_composition_data(table_data: List[List[str]]) -> List[Dict]:
    """
    Parse table data into structured chemical composition records.
    
    Args:
        table_data: 2D list of table cells (rows x columns)
    
    Returns:
        List of dictionaries with element_symbol, value, unit keys
    """
    if not table_data or len(table_data) < 2:
        return []
    
    composition_data = []
    
    # Try to identify header row (usually first row or second row)
    header_row_idx = 0
    for i, row in enumerate(table_data[:3]):
        # Check if row contains element symbols or "element" keyword
        row_text = ' '.join(row).lower()
        if any(symbol.lower() in row_text for symbol in ELEMENT_SYMBOLS) or 'element' in row_text:
            header_row_idx = i
            break
    
    # Extract headers
    headers = table_data[header_row_idx] if header_row_idx < len(table_data) else []
    
    # Determine unit from header or default
    header_text = ' '.join(headers).lower()
    unit = extract_unit(header_text)
    
    # Parse data rows (skip header row)
    data_start = header_row_idx + 1
    
    # Collect all values first to get context
    all_parsed_values = []
    seen_elements = set()  # Track elements to avoid duplicates
    
    for row_idx in range(data_start, len(table_data)):
        row = table_data[row_idx]
        
        # Skip empty rows
        if not row or all(not cell.strip() for cell in row):
            continue
        
        # Try to extract element symbol from first column
        element_symbol = None
        value = None
        
        # Strategy 1: First column is element, subsequent columns are values
        if len(row) >= 2:
            element_symbol = extract_element_symbol(row[0])
            if element_symbol and element_symbol not in seen_elements:
                # Try to find numeric value in subsequent columns
                candidates = []
                for col_idx, col in enumerate(row[1:]):
                    num = normalize_number(col)
                    if num is not None:
                        candidates.append((num, col_idx + 1))
                
                # Prefer values in reasonable range and closest to element
                if candidates:
                    valid_candidates = [(v, idx) for v, idx in candidates if is_valid_composition_value(v, unit)]
                    if valid_candidates:
                        valid_candidates.sort(key=lambda x: (x[1], x[0]))
                        value = valid_candidates[0][0]
                    else:
                        candidates.sort(key=lambda x: (x[1], abs(x[0])))
                        value = candidates[0][0]
        
        # Strategy 2: Look for element-value pairs in the row
        if element_symbol is None or element_symbol in seen_elements:
            for cell_idx, cell in enumerate(row):
                elem = extract_element_symbol(cell)
                if elem and elem not in seen_elements:
                    element_symbol = elem
                    num_match = re.search(r'[\d,\.]+', cell)
                    if num_match:
                        value = normalize_number(num_match.group())
                    else:
                        if cell_idx + 1 < len(row):
                            value = normalize_number(row[cell_idx + 1])
                        if value is None and cell_idx > 0:
                            value = normalize_number(row[cell_idx - 1])
                    if value is not None:
                        break
        
        # Strategy 3: Row-based parsing where headers are elements
        if element_symbol is None and len(headers) > 1:
            for col_idx, header in enumerate(headers):
                elem = extract_element_symbol(header)
                if elem and elem not in seen_elements and col_idx < len(row):
                    element_symbol = elem
                    value = normalize_number(row[col_idx])
                    if value is not None:
                        break
        
        # Store parsed result (only if not duplicate)
        if element_symbol and element_symbol not in seen_elements and value is not None and is_valid_composition_value(value, unit):
            all_parsed_values.append({
                'element_symbol': element_symbol,
                'value': value,
                'unit': unit
            })
            seen_elements.add(element_symbol)  # Mark as seen
    
    # Post-process: if most values are very large, apply correction
    if all_parsed_values:
        values_list = [item['value'] for item in all_parsed_values]
        avg_value = sum(values_list) / len(values_list)
        
        # If average is suspiciously high, apply global correction
        if avg_value > 50:  # Likely all values missing decimal point
            for item in all_parsed_values:
                item['value'] = item['value'] / 100
        elif avg_value > 20:  # Some might need correction
            for item in all_parsed_values:
                if item['value'] > 50:
                    item['value'] = item['value'] / 100
    
    # Sort by element priority (Al, V first, then others)
    all_parsed_values.sort(key=lambda x: ELEMENT_ORDER.get(x['element_symbol'], 999))
    
    return all_parsed_values


def parse_table_simple_heuristic(table_data: List[List[str]]) -> List[Dict]:
    """
    Simple heuristic parser that looks for element-value pairs in table cells.
    
    This is a fallback method that scans all cells for element symbols and values.
    Only extracts priority elements (6-8 elements).
    
    Args:
        table_data: 2D list of table cells
    
    Returns:
        List of dictionaries with element_symbol, value, unit keys (sorted by priority)
    """
    composition_data = []
    unit = 'wt.%'
    
    # Determine unit from table content
    flat_text = ' '.join([' '.join(row) for row in table_data]).lower()
    unit = extract_unit(flat_text)
    
    # Scan all cells for element-value patterns
    seen_elements = set()
    
    for row in table_data:
        for cell in row:
            cell = cell.strip()
            if not cell:
                continue
            
            element_symbol = extract_element_symbol(cell)
            
            if element_symbol and element_symbol not in seen_elements:
                num_pattern = r'[\d,\.]+(?:-[\d,\.]+)?'
                num_match = re.search(num_pattern, cell)
                
                if num_match:
                    num_str = num_match.group()
                    if '-' in num_str and not num_str.startswith('-'):
                        parts = num_str.split('-')
                        if len(parts) == 2:
                            val1 = normalize_number(parts[0])
                            val2 = normalize_number(parts[1])
                            value = val1 if val1 is not None else val2
                        else:
                            value = normalize_number(num_str)
                    else:
                        value = normalize_number(num_str)
                    
                    if value is not None and is_valid_composition_value(value, unit):
                        composition_data.append({
                            'element_symbol': element_symbol,
                            'value': value,
                            'unit': unit
                        })
                        seen_elements.add(element_symbol)
    
    # Sort by element priority (Al, V first, then others)
    composition_data.sort(key=lambda x: ELEMENT_ORDER.get(x['element_symbol'], 999))
    
    return composition_data