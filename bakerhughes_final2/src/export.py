"""Export utilities for writing data to CSV format."""

import csv
import os
from typing import List, Dict
from datetime import datetime


def export_to_csv(data: List[Dict], output_path: str) -> None:
    """
    Export chemical composition data to CSV file.
    
    Args:
        data: List of dictionaries with element_symbol, value, unit keys
        output_path: Path to output CSV file
    """
    if not data:
        raise ValueError("No data to export")
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
    
    # Define CSV columns
    fieldnames = ['element_symbol', 'value', 'unit']
    
    # Write CSV file
    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for row in data:
            # Only include required fields
            csv_row = {
                'element_symbol': row.get('element_symbol', ''),
                'value': row.get('value', ''),
                'unit': row.get('unit', 'wt.%')
            }
            writer.writerow(csv_row)


def generate_summary_report(data: List[Dict], output_path: str, 
                           pages_processed: int = 0, tables_found: int = 0) -> None:
    """
    Generate a summary report of the extraction process.
    
    Args:
        data: List of extracted composition data
        output_path: Path to save the report
        pages_processed: Number of pages processed
        tables_found: Number of tables found
    """
    report_lines = [
        "Chemical Composition Table Extraction Report",
        "=" * 50,
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        f"Pages Processed: {pages_processed}",
        f"Tables Found: {tables_found}",
        f"Elements Extracted: {len(data)}",
        "",
        "Extracted Elements:",
        "-" * 50,
    ]
    
    # Group by element for summary
    element_totals = {}
    for item in data:
        elem = item.get('element_symbol', 'Unknown')
        value = item.get('value', 0)
        if elem not in element_totals:
            element_totals[elem] = []
        element_totals[elem].append(value)
    
    for elem, values in sorted(element_totals.items()):
        avg_val = sum(values) / len(values) if values else 0
        report_lines.append(f"{elem}: {avg_val:.4f} (found {len(values)} times)")
    
    report_lines.append("")
    report_lines.append("Validation:")
    report_lines.append("-" * 50)
    
    # Check if values sum to approximately 100% (for composition tables)
    total = sum(item.get('value', 0) for item in data)
    report_lines.append(f"Total composition: {total:.2f}%")
    
    if abs(total - 100) < 10:  # Within 10% of 100
        report_lines.append("✓ Sum appears reasonable for composition table")
    else:
        report_lines.append("⚠ Sum does not approximate 100% (may contain requirements/ranges)")
    
    # Write report
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report_lines))







