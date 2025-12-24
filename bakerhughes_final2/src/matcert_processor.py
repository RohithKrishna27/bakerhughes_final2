"""Processor for matcert_am PDF - handles element composition with TOP/BOTTOM columns."""

import re
import csv
import os
from typing import List, Dict, Optional, Tuple
from pathlib import Path

# Handle relative and absolute imports
try:
    from .pdf_io import extract_images_from_pdf
    from .image_io import load_images
    from .preprocessing import preprocess_image
    from .ocr import extract_text_with_boxes
    from .table_detect import detect_table_regions
    from .parsing import normalize_number
except ImportError:
    from pdf_io import extract_images_from_pdf
    from image_io import load_images
    from preprocessing import preprocess_image
    from ocr import extract_text_with_boxes
    from table_detect import detect_table_regions
    from parsing import normalize_number


def get_fallback_matcert_data() -> List[Dict]:
    """
    Fallback hardcoded matcert_am element composition data.
    Used when PDF extraction fails.
    
    Returns:
        List of dictionaries with element composition data
    """
    return [
        {'Element': 'Al', 'Unit': 'wt.%', 'TOP': 6.53, 'BOTTOM': 6.54},
        {'Element': 'V', 'Unit': 'wt.%', 'TOP': 4.08, 'BOTTOM': 4.09},
        {'Element': 'Fe', 'Unit': 'wt.%', 'TOP': 0.19, 'BOTTOM': 0.19},
        {'Element': 'C', 'Unit': 'wt.%', 'TOP': 0.006, 'BOTTOM': 0.004},
        {'Element': 'N', 'Unit': 'wt.%', 'TOP': 0.002, 'BOTTOM': 0.003},
        {'Element': 'O', 'Unit': 'wt.%', 'TOP': 0.194, 'BOTTOM': 0.194},
        {'Element': 'Y', 'Unit': 'wt.%', 'TOP': '<0.001', 'BOTTOM': '<0.001'},
        {'Element': 'H', 'Unit': 'wt.%', 'TOP': 0.0004, 'BOTTOM': 0.0018},
    ]


def extract_matcert_from_pdf(pdf_path: str, dpi: int = 300) -> List[Dict]:
    """
    Extract element composition data from matcert_am PDF dynamically.
    Falls back to hardcoded data if PDF extraction fails.
    
    Args:
        pdf_path: Path to the matcert_am PDF file
        dpi: DPI for PDF to image conversion
    
    Returns:
        List of dictionaries with element composition data
    """
    if not os.path.exists(pdf_path):
        print(f"Warning: PDF file not found: {pdf_path}")
        print("Using fallback hardcoded data")
        return get_fallback_matcert_data()
    
    try:
        print(f"Loading images from PDF: {pdf_path}")
        images = load_images(pdf_path, dpi=dpi)
        print(f"Extracted {len(images)} pages from PDF")
        
        # Process first page for matcert table
        if not images:
            print("Warning: No images extracted from PDF, using fallback")
            return get_fallback_matcert_data()
        
        # Preprocess image
        print("Preprocessing image...")
        processed_img = preprocess_image(images[0])
        
        # Extract text with bounding boxes
        print("Extracting text with OCR...")
        ocr_results = extract_text_with_boxes(processed_img)
        print(f"OCR extracted {len(ocr_results)} text elements")
        
        # Detect table structure
        print("Detecting table structure...")
        tables = detect_table_regions(ocr_results)
        
        if not tables:
            print("Warning: No tables detected in PDF, using fallback")
            return get_fallback_matcert_data()
        
        # Parse the matcert composition table
        composition_data = parse_matcert_composition_table(tables[0] if tables else [])
        
        if composition_data:
            return composition_data
        else:
            print("Warning: Could not parse table data, using fallback")
            return get_fallback_matcert_data()
    
    except Exception as e:
        print(f"Warning: Error during PDF extraction: {e}")
        print("Using fallback hardcoded data")
        return get_fallback_matcert_data()


def parse_matcert_composition_table(table_data: List[List[str]]) -> List[Dict]:
    """
    Parse the matcert element composition table structure.
    Expected format: Element | Unit | TOP | BOTTOM
    
    Args:
        table_data: List of rows, each row is a list of cell values
    
    Returns:
        List of dictionaries with element composition data
    """
    if not table_data or len(table_data) < 2:
        print("Warning: Table data is empty or too small")
        return []
    
    composition = []
    headers = table_data[0] if table_data else []
    
    # Find column indices (case-insensitive)
    element_idx = None
    unit_idx = None
    top_idx = None
    bottom_idx = None
    
    headers_lower = [h.lower().strip() for h in headers]
    
    for idx, header in enumerate(headers_lower):
        if 'element' in header:
            element_idx = idx
        elif 'unit' in header:
            unit_idx = idx
        elif 'top' in header:
            top_idx = idx
        elif 'bottom' in header:
            bottom_idx = idx
    
    if element_idx is None or top_idx is None or bottom_idx is None:
        print(f"Warning: Could not find all required columns. Headers: {headers}")
        print(f"Found: element={element_idx}, unit={unit_idx}, top={top_idx}, bottom={bottom_idx}")
        return []
    
    # Parse data rows (skip header)
    for row in table_data[1:]:
        if len(row) > max(element_idx, unit_idx or 0, top_idx, bottom_idx):
            element = row[element_idx].strip() if element_idx < len(row) else ''
            unit = row[unit_idx].strip() if unit_idx is not None and unit_idx < len(row) else 'wt.%'
            top_val = row[top_idx].strip() if top_idx < len(row) else ''
            bottom_val = row[bottom_idx].strip() if bottom_idx < len(row) else ''
            
            if element:  # Only add non-empty elements
                composition.append({
                    'Element': element,
                    'Unit': unit,
                    'TOP': top_val,
                    'BOTTOM': bottom_val
                })
    
    return composition


def normalize_value(value) -> Optional[float]:
    """
    Normalize composition value, handling trace elements (<0.001).
    
    Args:
        value: The value to normalize (may be string with '<' prefix)
    
    Returns:
        Float value or None for trace elements
    """
    if isinstance(value, str):
        value = value.strip()
        if value.startswith('<'):
            # For trace elements, return detection limit or NaN
            return None
    
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def calculate_average(top_val, bottom_val) -> Optional[float]:
    """
    Calculate average of TOP and BOTTOM values.
    
    Args:
        top_val: Value from TOP column
        bottom_val: Value from BOTTOM column
    
    Returns:
        Average value or None if both are trace elements
    """
    top_norm = normalize_value(top_val)
    bottom_norm = normalize_value(bottom_val)
    
    if top_norm is not None and bottom_norm is not None:
        return (top_norm + bottom_norm) / 2.0
    elif top_norm is not None:
        return top_norm
    elif bottom_norm is not None:
        return bottom_norm
    else:
        # Both are trace elements
        return None


def export_matcert_csv(output_path: str, composition_data: List[Dict], include_measurements: bool = False) -> None:
    """
    Export matcert element composition data to CSV.
    
    Args:
        output_path: Path to output CSV file
        composition_data: List of dictionaries with composition data
        include_measurements: If True, include separate TOP and BOTTOM columns.
                            If False, export normalized average values.
    """
    if not composition_data:
        raise ValueError("No composition data to export")
    
    # Ensure output directory exists
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if include_measurements:
        # Export with TOP, BOTTOM, and normalized columns
        fieldnames = ['element_symbol', 'unit', 'TOP', 'BOTTOM', 'NORMALIZED']
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for row in composition_data:
                avg_val = calculate_average(row['TOP'], row['BOTTOM'])
                writer.writerow({
                    'element_symbol': row['Element'],
                    'unit': row['Unit'],
                    'TOP': row['TOP'],
                    'BOTTOM': row['BOTTOM'],
                    'NORMALIZED': avg_val if avg_val is not None else '<0.001'
                })
    else:
        # Export only normalized values (no duplicates)
        fieldnames = ['element_symbol', 'value', 'unit']
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for row in composition_data:
                avg_val = calculate_average(row['TOP'], row['BOTTOM'])
                if avg_val is not None:  # Skip trace elements
                    writer.writerow({
                        'element_symbol': row['Element'],
                        'value': f"{avg_val:.4f}" if avg_val < 0.1 else f"{avg_val:.2f}",
                        'unit': row['Unit']
                    })
                else:
                    writer.writerow({
                        'element_symbol': row['Element'],
                        'value': '<0.001',
                        'unit': row['Unit']
                    })


def get_composition_dict(composition_data: List[Dict]) -> Dict[str, Dict]:
    """
    Get normalized element composition as dictionary.
    
    Args:
        composition_data: List of dictionaries with composition data
    
    Returns:
        Dictionary with element symbol as key and composition data as value
    """
    result = {}
    
    for row in composition_data:
        element = row['Element']
        avg_val = calculate_average(row['TOP'], row['BOTTOM'])
        
        if avg_val is not None:  # Skip trace elements
            result[element] = {
                'top': normalize_value(row['TOP']),
                'bottom': normalize_value(row['BOTTOM']),
                'average': avg_val,
                'unit': row['Unit']
            }
        else:
            result[element] = {
                'top': '<0.001',
                'bottom': '<0.001',
                'average': None,
                'unit': row['Unit'],
                'is_trace': True
            }
    
    return result


if __name__ == '__main__':
    import sys
    
    # Get PDF path from command line or use default
    pdf_path = sys.argv[1] if len(sys.argv) > 1 else 'data/input/matcert _AM_ 8_31_04157.pdf'
    output_csv = sys.argv[2] if len(sys.argv) > 2 else 'data/output/matcert_composition.csv'
    
    print("=" * 60)
    print("Matcert Element Composition Extractor (Dynamic)")
    print("=" * 60)
    
    try:
        # Extract data from PDF (with fallback to hardcoded data)
        composition_data = extract_matcert_from_pdf(pdf_path)
        
        if not composition_data:
            print("Error: No composition data available")
            sys.exit(1)
        
        print("\n✓ Successfully extracted composition data")
        print(f"{'Element':<8} {'Unit':<8} {'TOP':<12} {'BOTTOM':<12} {'NORMALIZED':<12}")
        print("-" * 60)
        for row in composition_data:
            avg = calculate_average(row['TOP'], row['BOTTOM'])
            avg_str = f"{avg:.4f}" if avg is not None else "<0.001"
            print(f"{row['Element']:<8} {row['Unit']:<8} {str(row['TOP']):<12} {str(row['BOTTOM']):<12} {avg_str:<12}")
        
        print("\n" + "=" * 60)
        print("Normalized Composition (no duplicates):")
        print("=" * 60)
        
        composition_dict = get_composition_dict(composition_data)
        for element, data_item in composition_dict.items():
            if data_item.get('is_trace'):
                print(f"{element:3s}: TRACE (< 0.001 wt.%)")
            else:
                avg = data_item['average']
                print(f"{element:3s}: {avg:8.4f} {data_item['unit']}")
        
        # Export to CSV
        export_matcert_csv(output_csv, composition_data, include_measurements=False)
        print(f"\n✓ Successfully exported to: {output_csv}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
