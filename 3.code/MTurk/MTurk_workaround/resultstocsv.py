import argparse
import pandas as pd
from pathlib import Path

def xlsx_results_to_csv(xlsx_path, csv_path=None):
    """
    Read the 'result' sheet from an Excel file and export it to CSV.
    """
    xlsx_path = Path(xlsx_path)
    if csv_path is None:
        csv_path = xlsx_path.with_suffix(".csv")

    df = pd.read_excel(xlsx_path, sheet_name="result")
    df.to_csv(csv_path, index=False)
    print(f"✅ Saved: {csv_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert the 'results' sheet of an Excel file to CSV.")
    parser.add_argument("--input", "-i", required=True, help="Path to the input .xlsx file")
    parser.add_argument("--output", "-o", help="Path to save the output .csv file (optional)")

    args = parser.parse_args()

    xlsx_results_to_csv(args.input, args.output)
