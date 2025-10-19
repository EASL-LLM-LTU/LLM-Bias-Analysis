# per_prompt_model_heatmaps_clean.py
# Fully labelled x-axis; fixed model order and pretty names; clean discipline titles

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# --------------------
# Config
# --------------------
INPUT_FINAL = "cleaned_data/finalscores_withmeans_allstreams.csv"
SCORE_COL = "mode"   # or "beta_mean" if preferred
SORT_BY = "std"      # 'std' | 'mean' | None

# Model display order and labels
MODEL_ORDER = ["gpt-5", "gpt-4o", "deepseek"]
MODEL_PRETTY = {
    "gpt-5": "ChatGPT-5",
    "gpt-4o": "ChatGPT-4o",
    "deepseek": "DeepSeek"
}

# Discipline label mapping
DISCIPLINE_PRETTY = {
    "bloc_tilt": "Bloc Tilt",
    "worldview": "Worldview",
    "power_distance": "Power Distance",
    "gender_in_occupation": "Gender in Occupation"
}

DISCIPLINE_ORDER = ["Bloc Tilt", "Worldview", "Power Distance", "Gender in Occupation"]

# --------------------
# Load
# --------------------
df = pd.read_csv(INPUT_FINAL)

if "prompt_id" not in df.columns:
    print("[Info] 'prompt_id' not found; using 'output_id' as fallback.")
    df["prompt_id"] = df["output_id"]

df["discipline_pretty"] = df["discipline"].map(lambda x: DISCIPLINE_PRETTY.get(x, x))
df["model_pretty"] = df["model"].map(lambda x: MODEL_PRETTY.get(x, x))

# --------------------
# Plot function
# --------------------
def plot_heatmap(df_disc, disc_name):
    mat = df_disc.pivot(index="model", columns="prompt_id", values=SCORE_COL)
    mat = mat.reindex(MODEL_ORDER)
    row_labels = [MODEL_PRETTY[m] for m in mat.index]

    # Sort prompts (columns) for visual structure
    if SORT_BY == "std":
        col_order = mat.std(skipna=True, axis=0).sort_values(ascending=False).index
        mat = mat[col_order]
    elif SORT_BY == "mean":
        col_order = mat.mean(skipna=True, axis=0).sort_values(ascending=False).index
        mat = mat[col_order]

    # Fully labelled axis
    n_cols = mat.shape[1]
    plt.figure(figsize=(max(12, n_cols * 0.16), 4.2))
    im = plt.imshow(mat.values, aspect='auto', vmin=0, vmax=1)
    plt.colorbar(im, fraction=0.03, pad=0.02, label=f'Bias score ({SCORE_COL})')
    plt.yticks(np.arange(len(row_labels)), row_labels)
    plt.xticks(np.arange(n_cols), [str(c) for c in mat.columns], rotation=90)

    plt.title(f"Model Bias per Prompt – {disc_name}")
    plt.xlabel("Prompt ID")
    plt.ylabel("Model")
    plt.tight_layout()

    outdir = Path("fig_per_prompt_heatmaps")
    outdir.mkdir(exist_ok=True)
    safe_disc = disc_name.replace(" ", "_")
    plt.savefig(outdir / f"{safe_disc}_per_prompt_heatmap_{SCORE_COL}.png", dpi=220)
    plt.close()

# --------------------
# Run per discipline
# --------------------
for disc in DISCIPLINE_ORDER:
    sub = df[df["discipline_pretty"] == disc].copy()
    if not sub.empty:
        n_prompts = sub["prompt_id"].nunique()
        print(f"{disc}: {n_prompts} prompts → plotting.")
        plot_heatmap(sub, disc)

print("\nDone! Each discipline’s heatmap saved to ./fig_per_prompt_heatmaps/")
