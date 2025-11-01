import argparse
from pathlib import Path
import time
import pandas as pd
import win32com.client as win32

SHEET_PASSWORD = "1379"
TARGET_SHEET   = "raw_hit"
MAX_COL_WIDTH  = 80  # cap wide columns

def df_to_2d(df: pd.DataFrame):
    """Convert DataFrame to tuple-of-tuples including header row (A1)."""
    header = tuple(df.columns)
    body   = [tuple(row) for row in df.itertuples(index=False, name=None)]
    return tuple([header, *body])

def write_table(ws, df: pd.DataFrame):
    """Clear contents and write df (with headers) into ws starting at A1."""
    ws.UsedRange.ClearContents()
    if df.shape[0] == 0:  # if empty, just write headers
        if df.shape[1] > 0:
            header = tuple(df.columns)
            rng = ws.Range(ws.Cells(1,1), ws.Cells(1, df.shape[1]))
            rng.Value = (header,)
        return

    data = df_to_2d(df)
    nrows, ncols = len(data), len(data[0])
    dest = ws.Range(ws.Cells(1,1), ws.Cells(nrows, ncols))
    dest.Value = data

def process(source_csv: Path, target_xlsx: Path, save_as: Path|None):
    # Read CSV as strings to preserve IDs
    df = pd.read_csv(source_csv, dtype=str).fillna("")

    excel = win32.gencache.EnsureDispatch("Excel.Application")
    excel.Visible = False
    excel.DisplayAlerts = False

    wb = excel.Workbooks.Open(str(target_xlsx.resolve()))
    try:
        try:
            ws = wb.Worksheets(TARGET_SHEET)
        except Exception:
            raise RuntimeError(f"Sheet '{TARGET_SHEET}' not found in {target_xlsx.name}")

        # Unprotect
        try:
            ws.Unprotect(Password=SHEET_PASSWORD)
        except Exception:
            pass

        # Write table
        write_table(ws, df)

        # Wrap + AutoFit + cap column width
        used = ws.UsedRange
        used.WrapText = True
        used.Columns.AutoFit()
        used.Rows.AutoFit()
        for col in used.Columns:
            if col.ColumnWidth > MAX_COL_WIDTH:
                col.ColumnWidth = MAX_COL_WIDTH

        # Re-protect
        try:
            ws.Protect(
                Password=SHEET_PASSWORD,
                DrawingObjects=True,
                Contents=True,
                Scenarios=True,
                AllowFormattingColumns=True,
                AllowFormattingRows=True
            )
        except Exception:
            pass

        # Save
        if save_as:
            wb.SaveAs(str(save_as.resolve()))
            print(f"✅ HITs loaded into '{TARGET_SHEET}' → saved as {save_as}")
        else:
            wb.Save()
            print(f"✅ HITs loaded into '{TARGET_SHEET}' → updated {target_xlsx}")

    finally:
        wb.Close(SaveChanges=True)
        time.sleep(0.2)
        excel.Quit()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Load HITs from CSV into the 'raw_hit' sheet of an Excel workbook.")
    parser.add_argument("-s", "--source", required=True, help="Path to source CSV (e.g., bloctilt_raw_hit_7.csv)")
    parser.add_argument("-t", "--target", required=True, help="Path to target workbook (e.g., bloctilt_i7_hooman.xlsx)")
    parser.add_argument("-o", "--save-as", help="Optional path to save as new workbook; if omitted, saves in-place")
    args = parser.parse_args()

    process(Path(args.source), Path(args.target), Path(args.save_as) if args.save_as else None)
