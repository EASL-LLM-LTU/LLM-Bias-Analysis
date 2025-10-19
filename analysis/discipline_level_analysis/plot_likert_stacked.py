# plot_likert_stacked_pretty.py
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# ---- paths ----
BASE   = Path(r"D:\mgfin0\Desktop\Visualisations\cleaned_data")
INFILE = BASE / "raw_annotations_combined.csv"
OUTDIR = BASE / "figures"
OUTDIR.mkdir(exist_ok=True)

# ---- pretty labels ----
discipline_title = {
    "bloc_tilt": "Bloc Tilt",
    "gender_in_occupation": "Gender in Occupation",
    "power_distance": "Power Distance",
    "worldview": "Worldview",
}
model_title = {
    "deepseek": "DeepSeek",
    "gpt-4o": "ChatGPT-4o",
    "gpt-5": "ChatGPT-5",
}

# ---- load ----
df = pd.read_csv(INFILE)
df.columns = [c.lower() for c in df.columns]

# expected columns: discipline, model, annotation_range (1–5)
rating_col = "annotation_range"
rating_order = [1, 2, 3, 4, 5]

# (Keep all rows as-is; assuming data are already clean.)

# ---- precompute % by discipline × model × rating ----
cnt = (
    df.groupby(["discipline", "model", rating_col])
      .size()
      .unstack(fill_value=0)
      .reindex(columns=rating_order, fill_value=0)
)
pct = cnt.div(cnt.sum(axis=1).replace(0, np.nan), axis=0).fillna(0)
N = cnt.sum(axis=1)

# ---- plotting ----
disciplines = pct.index.get_level_values("discipline").unique()

# fix a consistent model order (DeepSeek, ChatGPT-4o, ChatGPT-5 if present)
desired_model_order = ["gpt-5", "gpt-4o", "deepseek"]

for d in disciplines:
    sub = pct.loc[d]                        # rows = model, cols = 1..5
    # align model order if present
    models_present = [m for m in desired_model_order if m in sub.index]
    # plus any others not in the desired list
    models_present += [m for m in sub.index if m not in models_present]
    sub = sub.reindex(index=models_present)

    # human-friendly y tick labels
    yticklabels = [model_title.get(m, m) for m in sub.index]

    models = sub.index.tolist()
    bottoms = np.zeros(len(models))

    fig, ax = plt.subplots(figsize=(9, 4.6))
    bar_containers = []

    # draw bars
    for r in rating_order:
        bars = ax.barh(models, sub[r].values, left=bottoms, label=str(r))
        bar_containers.append((r, bars))
        bottoms += sub[r].values

    # annotate % labels inside segments (only if segment >= 6% to avoid clutter)
    for r, bars in bar_containers:
        vals = sub[r].values
        for i, bar in enumerate(bars):
            width = vals[i]
            if width >= 0.04:  # 6% threshold for label
                x = bar.get_x() + bar.get_width() / 2.0
                y = bar.get_y() + bar.get_height() / 2.0
                ax.text(x, y, f"{width*100:.0f}%", ha="center", va="center", fontsize=9, color="white")

    # annotate N to the right of bars
    Ns = N.loc[d]
    for i, m in enumerate(models):
        ax.text(1.005, i, f"N={int(Ns.loc[m])}", va="center")

    title_txt = discipline_title.get(d, d)
    ax.set_title(f"{title_txt}: Raw Rating Distribution (1–5) by Model")
    ax.set_xlim(0, 1)
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x*100:.0f}%"))
    ax.set_xlabel("Percentage of ratings")
    ax.set_yticks(range(len(models)))
    ax.set_yticklabels(yticklabels)
    ax.invert_yaxis()  # top model first

    # Legend under the plot
    ax.legend(title="Rating", ncol=5, bbox_to_anchor=(0.5, -0.2), loc="upper center")
    plt.tight_layout()

    # filenames use the original key for consistency
    fig.savefig(OUTDIR / f"{d}_stacked_props.png", dpi=200)
    fig.savefig(OUTDIR / f"{d}_stacked_props.pdf")
    plt.close(fig)

print(f"✅ Saved figures to: {OUTDIR}")
