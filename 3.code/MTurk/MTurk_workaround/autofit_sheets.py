# autofit_sheets.py — hybrid: AutoFit + force row height = 30
import time
from pathlib import Path
import win32com.client as win32

SHEET_PASSWORD = "1379"
MAX_COL_WIDTH  = 80
ROW_HEIGHT     = 55

def autofit_excel(file_path):
    file_path = Path(file_path).resolve()
    excel = win32.gencache.EnsureDispatch("Excel.Application")
    excel.Visible = False
    excel.DisplayAlerts = False

    wb = excel.Workbooks.Open(str(file_path))

    try:
        for ws in wb.Worksheets:
            if not str(ws.Name).strip().upper().startswith("HIT"):
                continue  # only process HIT* sheets

            # Unprotect (ok if not protected)
            try:
                ws.Unprotect(Password=SHEET_PASSWORD)
            except Exception:
                pass

            # Clear cells D3:D8
            try:
                ws.Range("D3:D8").ClearContents()
            except Exception:
                pass

            # Wrap + AutoFit
            used = ws.UsedRange
            used.WrapText = True
            used.Columns.AutoFit()
            used.Rows.AutoFit()

            # Cap column widths
            for col in used.Columns:
                if col.ColumnWidth > MAX_COL_WIDTH:
                    col.ColumnWidth = MAX_COL_WIDTH

            # Force uniform row height = 30 (hybrid cap)
            for row in used.Rows:
                if row.RowHeight != ROW_HEIGHT:
                    row.RowHeight = ROW_HEIGHT

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

        wb.Save()
        print(f"✅ HIT sheets updated (cleared D3:D8, WrapText, col≤{MAX_COL_WIDTH}, rows={ROW_HEIGHT}) → {file_path}")
    finally:
        wb.Close(SaveChanges=True)
        time.sleep(0.2)
        excel.Quit()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Format HIT* sheets: clear D3:D8, WrapText, cap col width, set row height=30.")
    parser.add_argument("-f", "--file", required=True, help="Path to the Excel file (.xlsx)")
    args = parser.parse_args()
    autofit_excel(args.file)
