#!/usr/bin/python
# -*- coding: utf-8 -*-

# Import required modules
import os, sys
import csv
from scripts.encode_emoji import replace_emoji_characters  # helper to make emoji MTurk-safe

# 1. Read input file path from command-line arguments
in_file_path = sys.argv[1]  

# 2. Derive the directory containing the input file
dir_path = '/'.join(in_file_path.split('/')[:-1])  

# 3. Extract the base file name without extension
file_name = in_file_path.split('/')[-1].split('.csv')[0]  

# 4. Construct the output file name by appending "_0" (iteration 0)
out_file_name = file_name + "_0.csv"  

# 5. Full path for the new model CSV
out_file_path = os.path.join(dir_path, out_file_name)  

# 6. Open the input CSV for reading
f_in = open(in_file_path, 'r')

# 7. Open the output CSV for writing
f_out = open(out_file_path, 'w')

# 8. Create a CSV reader for the input file
csv_reader = csv.reader(f_in)

# 9. Create a CSV writer for the output file
csv_writer = csv.writer(f_out)

# Will store the number of columns in the original file
column_length = 0  

# 10. Loop through each row in the input CSV
for i, row in enumerate(csv_reader):
    skip = False  # Flag to mark rows to be skipped if invalid

    if i == 0:
        # First row → header row
        column_length = len(row)  # Save the number of columns in header

        # Validate that there are at least two columns (e.g., id, sent)
        if column_length <= 1:
            print("Columns must have at least length of two (e.g., id, sent)")
            exit(1)

        # Append EASL parameter headers to the header row
        row = row + ["alpha", "beta", "mode", "var"]

    else:
        # For all data rows
        if len(row) != column_length:
            # Row has incorrect number of columns → skip it
            print("skipped invalid row: {}".format(row))
            skip = True
        else:
            # Encode any emoji in each cell for safe storage/annotation
            row_encoded = []
            for r in row:
                row_encoded.append(replace_emoji_characters(r))

            # Append initial EASL values:
            # alpha=1, beta=1 (Beta(1,1) prior)
            # mode=0.5 (midpoint of scale)
            # var=0.0833 (variance of Beta(1,1) ≈ 1/12)
            row = row_encoded + ["1", "1", "0.5", "0.0833"]

    # Write the processed row to output file if not skipped
    if not skip:
        csv_writer.writerow(row)
