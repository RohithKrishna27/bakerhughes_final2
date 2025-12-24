"""
Simple runner script - just provide PDF path and output CSV path.
Usage: python run.py input.pdf output.csv
"""

import sys
from pathlib import Path

if len(sys.argv) < 3:
    print("Usage: python run.py <input_pdf> <output_csv>")
    print("Example: python run.py data/input/sample.pdf data/output/result.csv")
    sys.exit(1)

input_pdf = sys.argv[1]
output_csv = sys.argv[2]

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

# Run main
from main import main
sys.argv = ['main.py', '--input', input_pdf, '--output', output_csv]
main()







