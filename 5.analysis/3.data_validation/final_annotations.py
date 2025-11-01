import pandas as pd
import glob
import os

# === Paths ===
base_path = r"D:\mgfin0\Desktop\Visualisations\cleaned_data"
output_path = os.path.join(base_path, "raw_annotations_combined.csv")

# === Step 1: Find all CSVs in folder ===
csv_files = glob.glob(os.path.join(base_path, "*.csv"))

print(f"Found {len(csv_files)} files:")
for f in csv_files:
    print(f" - {os.path.basename(f)}")

# === Step 2: Read and combine ===
df_list = []
for file in csv_files:
    df = pd.read_csv(file)
    df["source_file"] = os.path.basename(file)  # track which discipline it came from
    df_list.append(df)

combined_df = pd.concat(df_list, ignore_index=True)

# === Step 3: Keep only relevant columns ===
columns_to_keep = [
    "source_file",
    "worker_id",
    "output_id",
    "discipline",
    "model",
    "annotation_range"
]
combined_df = combined_df[columns_to_keep]

# === Step 4: Save combined file ===
combined_df.to_csv(output_path, index=False)
print(f"\n✅ Combined file saved to: {output_path}")
print(f"Total rows: {len(combined_df)}")
