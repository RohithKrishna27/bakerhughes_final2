"""Main entry point for PDF chemical composition table extraction."""

import argparse
import sys
import os
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent))

from image_io import load_images
from preprocessing import preprocess_image
from ocr import extract_text_with_boxes
from table_detect import detect_table_regions, is_chemical_composition_table
from parsing import parse_table_to_composition_data, parse_table_simple_heuristic
from export import export_to_csv, generate_summary_report
from utils.logging import setup_logger


def main():
    """Main function to orchestrate PDF to CSV extraction."""
    parser = argparse.ArgumentParser(
        description='Extract chemical composition tables from PDF images and export to CSV'
    )
    parser.add_argument('--input', '-i', required=True, help='Path to input PDF file')
    parser.add_argument('--output', '-o', default='output.csv', help='Path to output CSV file')
    parser.add_argument('--dpi', type=int, default=300, help='DPI for PDF to image conversion (default: 300)')
    parser.add_argument('--log', help='Path to log file (optional)')
    parser.add_argument('--report', help='Path to summary report file (optional)')
    parser.add_argument('--lang', default='eng', help='OCR language (default: eng)')
    
    args = parser.parse_args()
    
    # Setup logging
    logger = setup_logger(log_file=args.log)
    logger.info("=" * 60)
    logger.info("Chemical Composition Table Extractor")
    logger.info("=" * 60)
    logger.info(f"Input PDF: {args.input}")
    logger.info(f"Output CSV: {args.output}")
    logger.info(f"DPI: {args.dpi}")
    
    all_composition_data = []
    pages_processed = 0
    tables_found = 0
    
    try:
        # Step 1: Load images from PDF or image file
        logger.info("Step 1: Loading images...")
        images = load_images(args.input, dpi=args.dpi)
        logger.info(f"Loaded {len(images)} image(s)")
        
        # Step 2: Process each page
        for page_num, image in enumerate(images, 1):
            logger.info(f"\nProcessing page {page_num}/{len(images)}...")
            pages_processed += 1
            
            # Step 3: Preprocess image
            logger.info("Preprocessing image...")
            processed_image = preprocess_image(image, denoise=True, enhance_contrast=True)
            
            # Step 4: Perform OCR
            logger.info("Performing OCR...")
            ocr_results = extract_text_with_boxes(processed_image, lang=args.lang)
            logger.info(f"OCR extracted {len(ocr_results)} text elements")
            
            if not ocr_results:
                logger.warning(f"No text found on page {page_num}")
                continue
            
            # Step 5: Detect table regions
            logger.info("Detecting table structures...")
            table_data = detect_table_regions(ocr_results)
            
            if not table_data or len(table_data) < 2:
                logger.warning(f"No table structure detected on page {page_num}")
                continue
            
            logger.info(f"Detected table with {len(table_data)} rows")
            
            # Step 6: Check if it's a chemical composition table
            if is_chemical_composition_table(table_data):
                logger.info("Table appears to be a chemical composition table")
                tables_found += 1
                
                # Step 7: Parse table data
                logger.info("Parsing table data...")
                composition_data = parse_table_to_composition_data(table_data)
                
                # If main parser didn't find much, try heuristic parser
                if len(composition_data) < 3:
                    logger.info("Trying alternative parsing method...")
                    composition_data = parse_table_simple_heuristic(table_data)
                
                if composition_data:
                    logger.info(f"Extracted {len(composition_data)} composition entries")
                    all_composition_data.extend(composition_data)
                    
                    # Log extracted elements
                    for entry in composition_data:
                        logger.info(f"  - {entry['element_symbol']}: {entry['value']} {entry['unit']}")
                else:
                    logger.warning("No composition data could be extracted from table")
            else:
                logger.info("Table does not appear to be a chemical composition table")
        
        # Step 8: Export to CSV
        if all_composition_data:
            logger.info(f"\nExporting {len(all_composition_data)} entries to CSV...")
            export_to_csv(all_composition_data, args.output)
            logger.info(f"CSV exported successfully to {args.output}")
            
            # Generate report if requested
            if args.report:
                logger.info("Generating summary report...")
                generate_summary_report(
                    all_composition_data, 
                    args.report,
                    pages_processed=pages_processed,
                    tables_found=tables_found
                )
                logger.info(f"Report saved to {args.report}")
        else:
            logger.error("No composition data extracted. Please check the PDF format.")
            sys.exit(1)
        
        logger.info("\n" + "=" * 60)
        logger.info("Extraction completed successfully!")
        logger.info("=" * 60)
    
    except Exception as e:
        logger.error(f"Error during extraction: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()

