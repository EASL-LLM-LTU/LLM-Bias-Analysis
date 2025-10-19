#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import csv
from encode_emoji import replace_emoji_characters

# Run: python initialize.py /path/to/raw.csv
# raw.csv needs: output_id, output, prompt_id, prompt
# Creates <name>_0.csv with these columns:
# output_id, output, prompt_id, prompt, alpha, beta, mode, var, embedding
# plus any extra columns from the input.

STANDARD_COLS = ["output_id", "output", "prompt_id", "prompt", "alpha", "beta", "mode", "var", "embedding"]

def build_header(input_fieldnames):
    if not input_fieldnames:
        print("Input CSV has no header.")
        sys.exit(1)

    # Start with standard columns
    header = list(STANDARD_COLS)

    # Add any extra input columns
    extras = [c for c in input_fieldnames if c not in STANDARD_COLS]
    header.extend(extras)
    return header

def main():
    if len(sys.argv) != 2:
        print("Usage: python initialize.py /path/to/raw.csv")
        sys.exit(1)

    in_file_path = sys.argv[1]
    if not os.path.exists(in_file_path):
        print(f"Input file not found: {in_file_path}")
        sys.exit(1)

    dir_path = os.path.dirname(in_file_path)
    file_name = os.path.basename(in_file_path).split('.csv')[0]
    out_file_path = os.path.join(dir_path, f"{file_name}_0.csv")

    # Read input with utf-8-sig, write output with utf-8
    with open(in_file_path, 'r', newline='', encoding='utf-8-sig') as f_in, \
         open(out_file_path, 'w', newline='', encoding='utf-8') as f_out:

        reader = csv.DictReader(f_in)
        # Check required columns
        required = {"output_id", "output", "prompt_id", "prompt"}
        missing = [c for c in required if c not in (reader.fieldnames or [])]
        if missing:
            print(f"Missing required columns in input CSV: {missing}")
            sys.exit(1)

        header = build_header(reader.fieldnames)
        writer = csv.DictWriter(f_out, fieldnames=header)
        writer.writeheader()

        for row in reader:
            # Skip rows missing output_id or output
            output_id = (row.get("output_id") or "").strip()
            output_txt = (row.get("output") or "").strip()
            if not output_id or not output_txt:
                print(f"Skipped invalid row (needs output_id & output): {row}")
                continue

            # Clean and normalize fields
            row["output_id"] = output_id
            row["prompt_id"] = (row.get("prompt_id") or "").strip()

            # Replace emojis safely
            row["output"] = replace_emoji_characters(output_txt)
            row["prompt"] = replace_emoji_characters((row.get("prompt") or "").strip())

            # Fill missing params with defaults
            row["alpha"] = (row.get("alpha") or "").strip() or "1"
            row["beta"]  = (row.get("beta")  or "").strip() or "1"
            row["mode"]  = (row.get("mode")  or "").strip() or "0.5"
            row["var"]   = (row.get("var")   or "").strip() or "0.0833"

            # Ensure embedding column exists
            row["embedding"] = (row.get("embedding") or "").strip()

            # Write row with all columns in order
            out_row = {col: row.get(col, "") for col in header}
            writer.writerow(out_row)

    print(f"Wrote initialized model: {out_file_path}")

if __name__ == "__main__":
    main()