# PDF Chemical Composition Table Extractor

A Python-based tool that automatically extracts chemical composition data from PDF material certificates and exports it to CSV format using OCR (Optical Character Recognition) technology.

📋 **Visual Diagrams:**
- **SVG Diagram**: `workflow_diagram.svg` - View in browser or import to Visio


## Features

- ✅ **Automated Extraction**: Extracts chemical composition tables from PDFs without manual data entry
- ✅ **OCR Technology**: Uses Tesseract OCR engine for accurate text recognition
- ✅ **Smart Parsing**: Multiple parsing strategies to handle different table formats
- ✅ **Error Correction**: Automatic correction of common OCR errors (e.g., "Kin" → "Mn")
- ✅ **Value Validation**: Filters unrealistic values and validates composition percentages
- ✅ **Multi-Page Support**: Processes multiple pages and combines results
- ✅ **Flexible Output**: CSV format for easy import into Excel, databases, or other tools

## Supported Element Symbols

The system recognizes 29+ chemical elements including:
**C, Si, Mn, P, S, Cr, Ni, Mo, Cu, W, Ti, V, Al, Fe, Nb, Ta, Zr, Sn, Pb, Bi, Zn, Mg, Ca, B, Be, Co, Y, H, N, O** and more.

## System Requirements

- **Python**: 3.7 or higher
- **Tesseract OCR**: Must be installed separately (see Setup below)
- **Operating System**: Windows, macOS, or Linux

## Setup

### Step 1: Install Tesseract OCR

**Windows:**
1. Download installer from: https://github.com/UB-Mannheim/tesseract/wiki
2. Run the installer (e.g., `tesseract-ocr-w64-setup-5.x.x.exe`)
3. **Important**: Check "Add to PATH" during installation
4. Default installation path: `C:\Program Files\Tesseract-OCR`
5. Restart terminal/command prompt after installation
6. Verify installation: `tesseract --version`

**macOS:**
```bash
brew install tesseract
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr
```

**Linux (Fedora/RHEL):**
```bash
sudo dnf install tesseract
```

### Step 2: Install Python Dependencies

```bash
pip install -r requirements.txt
```

This will install:
- `PyMuPDF` - PDF processing and image conversion
- `Pillow` - Image manipulation
- `opencv-python` - Advanced image preprocessing
- `pytesseract` - Python wrapper for Tesseract OCR

## Usage

### Basic Usage

1. **Place your PDF file** in the `data/input/` folder

2. **Run the extraction script**:
   ```bash
   python run.py "data/input/your_file.pdf" "data/output/result.csv"
   ```

### Alternative Usage

**Using the main script directly:**
```bash
python src/main.py --input "data/input/material.pdf" --output "data/output/composition.csv"
```

**With additional options:**
```bash
python src/main.py \
  --input "data/input/material.pdf" \
  --output "data/output/composition.csv" \
  --dpi 300 \
  --lang eng \
  --log "data/output/extraction.log"
```

### Command-Line Arguments

| Argument | Short | Description | Default |
|----------|-------|-------------|---------|
| `--input` | `-i` | Path to input PDF file | Required |
| `--output` | `-o` | Path to output CSV file | `output.csv` |
| `--dpi` | | DPI for PDF to image conversion | `300` |
| `--lang` | | OCR language code | `eng` |
| `--log` | | Path to log file (optional) | None |
| `--report` | | Path to summary report file (optional) | None |

## Output Format

The system generates a CSV file with three columns:

```csv
element_symbol,value,unit
C,0.05,wt.%
Si,0.34,wt.%
Mn,1.12,wt.%
P,0.013,wt.%
S,0.011,wt.%
```

### Output Fields

- **element_symbol**: Chemical element symbol (e.g., C, Si, Mn)
- **value**: Numeric composition value
- **unit**: Unit of measurement (typically `wt.%` for weight percentage)

## How It Works

The extraction process follows these steps:

1. **PDF to Image**: Converts PDF pages to high-resolution images (300 DPI)
2. **Image Preprocessing**: Enhances image quality (grayscale, denoise, contrast)
3. **OCR Processing**: Extracts text with bounding box coordinates using Tesseract
4. **Table Detection**: Identifies and structures table data from OCR results
5. **Validation**: Verifies the table is a chemical composition table
6. **Data Parsing**: Extracts element symbols and values using multiple strategies
7. **Export**: Writes structured data to CSV file

For detailed technical information, see [ARCHITECTURE.md](ARCHITECTURE.md).

## Parsing Strategies

The system uses multiple parsing strategies to handle different table formats:

1. **Column-based**: Element in first column, values in subsequent columns
2. **Cell-based**: Element and value in the same cell
3. **Header-based**: Element symbols in header row, values in data rows
4. **Heuristic fallback**: Scans all cells for element-value patterns

## Error Handling

The system automatically handles common OCR errors:

- **Element misreads**: "Kin" → "Mn", "5" → "S"
- **Number format**: "0134" → "0.013", "011" → "0.011"
- **Value validation**: Filters unrealistic values (>150% for percentages)
- **Missing decimals**: Attempts to correct missing decimal points

## Troubleshooting

### Tesseract Not Found

**Error**: `tesseract is not installed or it's not in your PATH`

**Solution**:
- Verify Tesseract installation: `tesseract --version`
- If not found, add to PATH or manually set path in `src/ocr.py`:
  ```python
  pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
  ```

### No Data Extracted

**Possible causes**:
- PDF contains scanned images with poor quality
- Table format is not recognized
- OCR cannot read the text clearly

**Solutions**:
- Ensure PDF has good image quality (at least 300 DPI)
- Try increasing DPI: `--dpi 400`
- Check if table contains recognized element symbols
- Review log file for detailed error messages

### Incorrect Values

OCR accuracy depends on:
- Image quality and resolution
- Font clarity and size
- Table structure complexity

**Recommendations**:
- Use high-quality PDFs (scanned at 300+ DPI)
- Ensure good contrast and clear text
- Some manual verification may be needed for critical data

## Project Structure

```
bakerhughes/
├── README.md                 # This file
├── ARCHITECTURE.md           # Detailed system architecture
├── workflow_diagram.svg      # Visual workflow diagram (SVG)
├── workflow_diagram.png      # Visual workflow diagram (PNG)
├── requirements.txt          # Python dependencies
├── run.py                    # Simple runner script
├── data/
│   ├── input/               # Place your PDFs here
│   └── output/              # Extracted CSV files appear here
└── src/
    ├── main.py              # Main extraction script
    ├── pdf_io.py            # PDF to image conversion
    ├── preprocessing.py     # Image enhancement
    ├── ocr.py               # OCR processing
    ├── table_detect.py      # Table structure detection
    ├── parsing.py           # Data extraction and parsing
    ├── export.py            # CSV export
    └── utils/
        ├── config.py        # Configuration and constants
        └── logging.py       # Logging setup
```
