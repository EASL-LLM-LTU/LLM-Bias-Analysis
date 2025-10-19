# ============================================
# Five panels (no legend):
#   Bloc Tilt, Gender in Occupation, Power Distance, Worldview, Geopolitical Bias
# ● = pooled mode (mode of Beta(mean α, mean β))
# CI = 80% credible interval of the same pooled Beta
# Visual row order (BOTTOM→TOP): DeepSeek → ChatGPT-4o → ChatGPT-5
# ============================================

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import beta
from pathlib import Path

# ---------- PATHS ----------
DATA_DIR = Path(r"D:\mgfin0\Desktop\Visualisations\cleaned_data")
INFILE   = DATA_DIR / "finalscores_withmeans_allstreams.csv"
OUTDIR   = DATA_DIR / "figures"
OUTDIR.mkdir(exist_ok=True)

# ---------- LABELS / ORDER ----------
discipline_map = {
    "bloc_tilt": "Bloc Tilt",
    "gender_in_occupation": "Gender in Occupation",
    "power_distance": "Power Distance",
    "worldview": "Worldview",
}
axis_legend = {
    "Bloc Tilt": "Bias Score (0–1)\n0 = Western-leaning (NATO/G7)      1 = BRICS-leaning",
    "Gender in Occupation": "Bias Score (0–1)\n0 = No bias                         1 = Severe gender bias",
    "Worldview": "Bias Score (0–1)\n0 = Individualist                   1 = Collectivist",
    "Power Distance": "Bias Score (0–1)\n0 = Low Power Distance (Egalitarian)  1 = High Power Distance",
    "Geopolitical Bias": "Bias Score (Average of Bloc Tilt, Worldview, Power Distance)\n0 = 'Western'-leaning               1 = 'Eastern'-leaning",
}
# raw -> pretty
model_pretty  = {"deepseek":"DeepSeek","gpt-4o":"ChatGPT-4o","gpt-5":"ChatGPT-5"}

# Visual order (BOTTOM→TOP)
ORDER = ["DeepSeek","ChatGPT-4o","ChatGPT-5"]
COLOR = {"DeepSeek":"#2ca02c","ChatGPT-4o":"#9467bd","ChatGPT-5":"#ff7f0e"}
Y_POS = {"DeepSeek": 0, "ChatGPT-4o": 1, "ChatGPT-5": 2}

# ---------- LOAD ----------
df = pd.read_csv(INFILE)
df.columns = [c.lower() for c in df.columns]

# numeric coercion
for c in ["alpha","beta","mode","var","beta_mean","ci_80_lower","ci_80_upper","ci_width"]:
    if c in df.columns:
        df[c] = pd.to_numeric(df[c], errors="coerce")

# tidy labels
df["discipline"] = df["discipline"].map(discipline_map).fillna(df["discipline"])
df["model"] = df["model"].map(model_pretty).fillna(df["model"])

# ---------- POOLED-BETA STATS (per discipline × model) ----------
# We aggregate the raw alpha/beta with means, then compute the pooled Beta’s mode & CI
eps = 1e-9
df["alpha"] = df["alpha"].fillna(0).clip(lower=eps)
df["beta"]  = df["beta"].fillna(0).clip(lower=eps)

gb = df.groupby(["discipline","model"], as_index=False, sort=False)
pooled = gb.agg(
    n_items     = ("mode","size"),
    alpha_mean  = ("alpha","mean"),
    beta_mean_p = ("beta","mean"),
)

# pooled mode of Beta(mean α, mean β)
def beta_mode_from_means(a_mean, b_mean):
    if not np.isfinite(a_mean) or not np.isfinite(b_mean) or a_mean <= 0 or b_mean <= 0:
        return np.nan
    if a_mean > 1 and b_mean > 1:
        return (a_mean - 1.0) / (a_mean + b_mean - 2.0)
    # boundary cases:
    if a_mean <= 1 and b_mean > 1: return 0.0
    if a_mean > 1 and b_mean <= 1: return 1.0
    # both <= 1: U-shaped; undefined single interior mode
    return np.nan

pooled["pooled_mode"] = [
    beta_mode_from_means(a, b)
    for a, b in zip(pooled["alpha_mean"], pooled["beta_mean_p"])
]

# 80% CI of the same pooled Beta
pooled["ci_lower"] = beta.ppf(0.1, pooled["alpha_mean"], pooled["beta_mean_p"])
pooled["ci_upper"] = beta.ppf(0.9, pooled["alpha_mean"], pooled["beta_mean_p"])

# left/right half-widths (asymmetric ok)
pooled["left_hw"]  = (pooled["pooled_mode"] - pooled["ci_lower"]).clip(lower=0)
pooled["right_hw"] = (pooled["ci_upper"] - pooled["pooled_mode"]).clip(lower=0)

# ---------- BUILD "Geopolitical Bias" (average pooled α,β across 3 geo disciplines) ----------
geo_src = pooled[pooled["discipline"].isin(["Bloc Tilt","Worldview","Power Distance"])].copy()
geo = (
    geo_src.groupby("model", as_index=False, sort=False)
           .agg(
               n_items     = ("n_items","sum"),
               alpha_mean  = ("alpha_mean","mean"),
               beta_mean_p = ("beta_mean_p","mean"),
           )
)
geo["discipline"] = "Geopolitical Bias"

# compute pooled stats for geo rows
geo["pooled_mode"] = [
    beta_mode_from_means(a, b)
    for a, b in zip(geo["alpha_mean"], geo["beta_mean_p"])
]
geo["ci_lower"] = beta.ppf(0.1, geo["alpha_mean"], geo["beta_mean_p"])
geo["ci_upper"] = beta.ppf(0.9, geo["alpha_mean"], geo["beta_mean_p"])
geo["left_hw"]  = (geo["pooled_mode"] - geo["ci_lower"]).clip(lower=0)
geo["right_hw"] = (geo["ci_upper"] - geo["pooled_mode"]).clip(lower=0)

# Combine pooled + geo rows for plotting
plot_df = pd.concat([pooled, geo], ignore_index=True)

# ---------- PLOTTER (pooled mode ± CI only) ----------
def plot_one(sub: pd.DataFrame, disc_name: str):
    sub = sub[sub["model"].isin(ORDER)].copy()
    sub["y"] = sub["model"].map(Y_POS)
    sub = sub.dropna(subset=["pooled_mode","left_hw","right_hw","y"]).sort_values("y")

    fig, ax = plt.subplots(figsize=(9, 3.6))
    for _, row in sub.iterrows():
        m = row["model"]; color = COLOR[m]
        # ● pooled mode ± 80% CI (of pooled Beta)
        ax.errorbar(
            x=row["pooled_mode"], y=row["y"],
            xerr=[[row["left_hw"]],[row["right_hw"]]],
            fmt="o", color=color, capsize=5, markersize=8, lw=1.8
        )

    # Cosmetics
    ax.axvline(0.5, color="gray", ls="--", lw=1, alpha=0.7)
    ax.set_xlim(0, 1)

    ticks = [Y_POS[m] for m in ORDER]  # [0,1,2]
    ax.set_yticks(ticks)
    ax.set_yticklabels(ORDER)          # bottom: DeepSeek … top: ChatGPT-5

    ax.set_xlabel(axis_legend.get(disc_name, "Bias Score (0–1)"), labelpad=8)
    ax.set_title(f"{disc_name} — ● Pooled Mode (Beta(mean α, mean β)) ± 80% CI",
                 fontsize=9, weight="bold", pad=6)
    ax.grid(axis="x", alpha=0.25)

    plt.tight_layout()
    plt.subplots_adjust(left=0.22)

    base = disc_name.replace(" ", "_").lower()
    out_png = OUTDIR / f"{base}_dot_ci_pooled.png"
    out_pdf = OUTDIR / f"{base}_dot_ci_pooled.pdf"
    fig.savefig(out_png, dpi=300)
    try:
        fig.savefig(out_pdf)
    except PermissionError:
        print(f"⚠️ PDF for {disc_name} may be open—skipping.")
    plt.close(fig)
    print(f"✅ Saved: {out_png}")

# ---------- RUN (4 disciplines + 1 aggregate) ----------
for disc in ["Bloc Tilt","Gender in Occupation","Power Distance","Worldview","Geopolitical Bias"]:
    plot_one(plot_df[plot_df["discipline"] == disc], disc)

print("\n✅ All figures saved to:", OUTDIR)
