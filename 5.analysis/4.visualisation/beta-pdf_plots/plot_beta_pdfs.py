import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import beta
from pathlib import Path

# ---------- PATHS ----------
DATA_DIR = Path(r"D:\mgfin0\Desktop\Visualisations\cleaned_data")
CSV_PATH = DATA_DIR / "finalscores_allstreams.csv"
OUTDIR   = DATA_DIR / "figures"
OUTDIR.mkdir(exist_ok=True)

# ---------- LABELS ----------
discipline_pretty = {
    "bloc_tilt": "Bloc Tilt",
    "gender_in_occupation": "Gender in Occupation",
    "power_distance": "Power Distance",
    "worldview": "Worldview",
}
x_caption = {
    "bloc_tilt": "Bias score (0 = Western-leaning, 1 = BRICS-leaning)",
    "gender_in_occupation": "Bias score (0 = No bias, 1 = Severe gender bias)",
    "power_distance": "Bias score (0 = Low Power Distance, 1 = High Power Distance)",
    "worldview": "Bias score (0 = Individualist, 1 = Collectivist)",
}
model_pretty = {"deepseek":"DeepSeek","gpt-4o":"ChatGPT-4o","gpt-5":"ChatGPT-5"}
ORDER        = ["gpt-5", "gpt-4o", "deepseek"]
COLORS       = {"deepseek":"#2ca02c","gpt-4o":"#9467bd","gpt-5":"#ff7f0e"}

# ---------- LOAD ----------
df = pd.read_csv(CSV_PATH)
df.columns = [c.lower() for c in df.columns]
for c in ["alpha","beta","mode","beta_mean"]:
    df[c] = pd.to_numeric(df[c], errors="coerce")

# keep canonical lowercase keys for matching
df["discipline"] = df["discipline"].str.lower().str.strip()

# ---------- CALC AGGREGATES ----------
agg = (
    df.groupby(["discipline","model"], as_index=False)
      .agg(
          a_mean=("alpha","mean"),
          b_mean=("beta","mean"),
          median_mode=("mode","median"),
          mean_of_means=("beta_mean","mean")
      )
)

# ensure same casing used in the loop
agg["discipline"] = agg["discipline"].str.lower().str.strip()

# ---------- PLOTTING ----------
x = np.linspace(0, 1, 800)
disc_list = ["bloc_tilt","gender_in_occupation","power_distance","worldview"]

for disc in disc_list:
    sub = agg.loc[agg["discipline"] == disc].copy()
    print(f"→ Processing {disc}: {len(sub)} rows")
    if sub.empty:
        print(f"⚠️ No data for {disc}")
        continue

    fig, ax = plt.subplots(figsize=(9, 5))
    ymax_global = 0.0
    pdfs = {}

    # draw PDFs
    for m in ORDER:
        row = sub[sub["model"] == m]
        if row.empty:
            continue

        a = row["a_mean"].iloc[0]
        b = row["b_mean"].iloc[0]

        y = beta.pdf(x, a, b)
        color = COLORS[m]
        pdfs[m] = (a, b, y)

        ax.plot(x, y, color=color, lw=2, label=model_pretty[m])
        ax.fill_between(x, 0, y, color=color, alpha=0.08)
        ymax_global = max(ymax_global, float(y.max()))

    # pooled-mode dotted lines only
    for m in ORDER:
        if m not in pdfs:
            continue
        a, b, y = pdfs[m]
        color = COLORS[m]

        # pooled mode
        if a > 1 and b > 1:
            pooled_mode = (a - 1.0) / (a + b - 2.0)
        elif a <= 1 < b:
            pooled_mode = 0.0
        elif b <= 1 < a:
            pooled_mode = 1.0
        else:
            pooled_mode = np.nan
        if not np.isfinite(pooled_mode):
            continue

        y_at_mode = float(beta.pdf(pooled_mode, a, b))
        ax.vlines(pooled_mode, 0, y_at_mode, color=color, ls=":", lw=2, alpha=0.9)

    # cosmetics
    ax.set_title(f"{discipline_pretty.get(disc,disc)} — Posterior Beta Distributions\n",
                 fontsize=13, weight="bold")
    ax.set_xlabel(x_caption.get(disc,"Bias score (0–1)"), fontsize=11)
    ax.set_ylabel("Density", fontsize=11)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, ymax_global * 1.08)
    ax.grid(alpha=0.25)

    ax.legend(title="Model", title_fontsize=10, fontsize=10,
              loc="upper right", frameon=True, facecolor="white", edgecolor="lightgray")

    plt.tight_layout()

    base = disc.replace(" ", "_").lower()
    out_png = OUTDIR / f"{base}_posterior_beta_pdfs.png"
    out_pdf = OUTDIR / f"{base}_posterior_beta_pdfs.pdf"
    fig.savefig(out_png, dpi=300)
    try:
        fig.savefig(out_pdf)
    except PermissionError:
        print(f"⚠️ PDF for {disc} open – skipped.")
    plt.close(fig)
    print(f"✅ Saved: {out_png}")
