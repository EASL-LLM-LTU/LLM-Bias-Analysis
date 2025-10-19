# summarize_disc_model_with_geo_pooled_mode.py
# Outputs:
#   - discipline_model_summary_with_geo.csv
#   - discipline_model_pairwise_with_geo.csv
#
# Per discipline × model, this reports:
#   n_items
#   pooled_mode           (mode of Beta(mean α, mean β)  ← aligns with your plotted PDFs)
#   mode_median, mode_mean
#   ciw_median            (median item-level 80% CI width, robust)
#   beta_mean_avg
#   beta_mean_ci_lower/upper/width  (from Beta(mean α, mean β))
#   var_median, var_mean
#
# It also adds "geopolitical_bias" rows by averaging discipline-level aggregates
# over {bloc_tilt, worldview, power_distance} per model, including pooled_mode.

import pandas as pd
import numpy as np
from scipy.stats import beta

INPUT = r"D:\mgfin0\Desktop\Visualisations\cleaned_data\finalscores_withmeans_allstreams.csv"

# ---------- Load & clean ----------
df = pd.read_csv(INPUT)
df.columns = [c.lower() for c in df.columns]

eps = 1e-9
for c in ["alpha","beta","mode","var","beta_mean"]:
    if c in df.columns:
        df[c] = pd.to_numeric(df[c], errors="coerce")
df["alpha"] = df["alpha"].fillna(0).clip(lower=eps)
df["beta"]  = df["beta"].fillna(0).clip(lower=eps)

# Recompute 80% CI per item from alpha,beta (10th..90th) → item-level width
df["ci_lower80"] = beta.ppf(0.1, df["alpha"], df["beta"])
df["ci_upper80"] = beta.ppf(0.9, df["alpha"], df["beta"])
df["ciw80_item"] = (df["ci_upper80"] - df["ci_lower80"])

# ---------- Per-discipline × model summary with pooled Beta(mean α, mean β) ----------
gb = df.groupby(["discipline","model"], as_index=False)
summ = gb.agg(
    n_items       = ("mode","size"),
    mode_median   = ("mode","median"),
    mode_mean     = ("mode","mean"),
    ciw_median    = ("ciw80_item","median"),     # robust typical width
    beta_mean_avg = ("beta_mean","mean"),
    var_median    = ("var","median"),
    var_mean      = ("var","mean"),
    alpha_mean    = ("alpha","mean"),            # for pooled Beta
    beta_mean_par = ("beta","mean"),             # for pooled Beta
)

# Pooled CI around Beta(mean α, mean β)
summ["beta_mean_ci_lower"] = beta.ppf(0.1, summ["alpha_mean"], summ["beta_mean_par"])
summ["beta_mean_ci_upper"] = beta.ppf(0.9, summ["alpha_mean"], summ["beta_mean_par"])
summ["beta_mean_ci_width"] = summ["beta_mean_ci_upper"] - summ["beta_mean_ci_lower"]

# Mode of Beta(mean α, mean β) → this matches your plotted curve's peak
def beta_mode_from_means(a_mean, b_mean):
    if not np.isfinite(a_mean) or not np.isfinite(b_mean) or a_mean <= 0 or b_mean <= 0:
        return np.nan
    if a_mean > 1 and b_mean > 1:
        return (a_mean - 1.0) / (a_mean + b_mean - 2.0)
    # boundary cases:
    if a_mean <= 1 and b_mean > 1:
        return 0.0
    if a_mean > 1 and b_mean <= 1:
        return 1.0
    # both <= 1 → U-shaped; both ends are modes
    return np.nan

summ["pooled_mode"] = [
    beta_mode_from_means(a, b)
    for a, b in zip(summ["alpha_mean"], summ["beta_mean_par"])
]

# Keep tidy report columns
summary = summ[[
    "discipline","model","n_items",
    "pooled_mode",
    "mode_median","mode_mean",
    "ciw_median",
    "beta_mean_avg","beta_mean_ci_lower","beta_mean_ci_upper","beta_mean_ci_width",
    "var_median","var_mean",
]].copy()

# ---------- Add Geopolitical Bias (average of discipline-level aggregates) ----------
geo_set = {"bloc_tilt","worldview","power_distance"}
geo = (
    summary[summary["discipline"].isin(geo_set)]
    .groupby("model", as_index=False)
    .agg({
        "n_items":"sum",
        "pooled_mode":"mean",        # centre consistent with plotted pooled curve
        "mode_median":"mean",
        "mode_mean":"mean",
        "ciw_median":"mean",
        "beta_mean_avg":"mean",
        "beta_mean_ci_lower":"mean",
        "beta_mean_ci_upper":"mean",
        "beta_mean_ci_width":"mean",
        "var_median":"mean",
        "var_mean":"mean",
    })
)
geo.insert(0, "discipline", "geopolitical_bias")

summary_all = pd.concat([summary, geo], ignore_index=True)

# ---------- Ordering & save ----------
disc_order  = ["bloc_tilt","gender_in_occupation","power_distance","worldview","geopolitical_bias"]
model_order = ["gpt-5","gpt-4o","deepseek"]
summary_all["discipline"] = pd.Categorical(summary_all["discipline"], categories=disc_order, ordered=True)
summary_all["model"]      = pd.Categorical(summary_all["model"],      categories=model_order, ordered=True)
summary_all = summary_all.sort_values(["discipline","model"]).reset_index(drop=True)

summary_all.round(4).to_csv("discipline_model_summary_with_geo.csv", index=False)
print("Saved: discipline_model_summary_with_geo.csv")
print(summary_all.round(4).to_string(index=False))

# ---------- Optional: pairwise deltas within each discipline (incl. geo) ----------
def pairwise_rows(df_disc: pd.DataFrame) -> pd.DataFrame:
    need = {"gpt-5","gpt-4o","deepseek"}
    if not need.issubset(set(df_disc["model"])):
        return pd.DataFrame()
    wide = df_disc.set_index("model")
    def d(a,b,metric): return float(wide.loc[a, metric]) - float(wide.loc[b, metric])
    rows = []
    for (a,b) in [("gpt-5","gpt-4o"), ("gpt-5","deepseek"), ("gpt-4o","deepseek")]:
        rows.append({
            "discipline": df_disc["discipline"].iloc[0],
            "delta_pair": f"{a} - {b}",
            "Δpooled_mode": d(a,b,"pooled_mode"),
            "Δmode_median": d(a,b,"mode_median"),
            "Δmode_mean":   d(a,b,"mode_mean"),
            "Δbeta_mean":   d(a,b,"beta_mean_avg"),
            "Δciw_median":  d(a,b,"ciw_median"),
        })
    return pd.DataFrame(rows)

pairwise = (
    summary_all.groupby("discipline", as_index=False, group_keys=False)
               .apply(pairwise_rows)
               .reset_index(drop=True)
)

pairwise.round(4).to_csv("discipline_model_pairwise_with_geo.csv", index=False)
print("Saved: discipline_model_pairwise_with_geo.csv")
print(pairwise.round(4).to_string(index=False))
