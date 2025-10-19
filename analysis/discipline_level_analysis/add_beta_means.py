import pandas as pd
from pathlib import Path

# === File paths ===
DATA_DIR = Path(r"D:\mgfin0\Desktop\Visualisations\cleaned_data")
INFILE = DATA_DIR / "finalscores_allstreams.csv"
OUTFILE = DATA_DIR / "finalscores_withmeans_allstreams.csv"

# === Load data ===
df = pd.read_csv(INFILE)

# === Sanity check ===
if not {'alpha', 'beta'}.issubset(df.columns):
    raise ValueError("CSV must contain 'alpha' and 'beta' columns.")

# === Compute Beta mean ===
df['beta_mean'] = df['alpha'] / (df['alpha'] + df['beta'])

# === Save output ===
df.to_csv(OUTFILE, index=False)

print(f"✅ Added 'beta_mean' column and saved to:\n{OUTFILE}")
print("\nPreview of new columns:")
print(df[['output_id', 'alpha', 'beta', 'mode', 'beta_mean']].head())
