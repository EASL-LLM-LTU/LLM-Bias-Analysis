#!/usr/bin/env python3
"""
Hard-coded paths:
  CSV = D:\mgfin0\Desktop\Visualisations\discipline_level_analysis\cleaned_data\finalscores_withmeans_allstreams.csv
  OUT = D:\mgfin0\Desktop\Visualisations\kruskal_results

What it does (per discipline: bloc_tilt, gender_in_occupation, power_distance, worldview):
  1) Runs Kruskal–Wallis across models {deepseek, gpt-4o, gpt-5} on item-level Beta 'mode' values
  2) ALWAYS runs pairwise Mann–Whitney U tests for all model pairs (two-sided)
     and applies Holm–Bonferroni correction

Outputs exactly 5 CSV files:
  - overall_kruskal_summary.csv
  - posthoc_pairwise_holm_bloc_tilt.csv
  - posthoc_pairwise_holm_gender_in_occupation.csv
  - posthoc_pairwise_holm_power_distance.csv
  - posthoc_pairwise_holm_worldview.csv

Dependencies: pandas, numpy, scipy
Install:
  py -m pip install --upgrade pip
  py -m pip install pandas numpy scipy
"""

import itertools
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import kruskal, mannwhitneyu

# ===== Hard-coded I/O =====
CSV_PATH = Path(r"D:\mgfin0\Desktop\Visualisations\discipline_level_analysis\cleaned_data\finalscores_withmeans_allstreams.csv")
OUT_DIR  = Path(r"D:\mgfin0\Desktop\Visualisations\kruskal_results")
OUT_DIR.mkdir(parents=True, exist_ok=True)

DISCIPLINES = ["bloc_tilt", "gender_in_occupation", "power_distance", "worldview"]
VALID_MODELS = ["deepseek", "gpt-4o", "gpt-5"]

def _canon(s: pd.Series) -> pd.Series:
    return s.astype(str).str.strip().str.lower()

def holm_bonferroni_correction(pvals_dict, alpha=0.05):
    """Return DataFrame with raw p, Holm-adjusted p, and reject flag."""
    items = sorted(pvals_dict.items(), key=lambda kv: kv[1])  # (label, p) ascending by p
    m = len(items)
    rows = []
    running_max = 0.0
    for i, (label, p) in enumerate(items, start=1):
        threshold = alpha / (m - i + 1)
        reject = p <= threshold
        adj = (m - i + 1) * p
        running_max = max(running_max, adj)
        rows.append((label, p, min(1.0, running_max), reject))
    df = pd.DataFrame(rows, columns=["comparison", "p_raw", "p_adj_holm", "reject_0.05"]).sort_values("p_raw")
    return df

def eta_squared_kw(H, k, N):
    try:
        return float((H - k + 1) / (N - k))
    except Exception:
        return np.nan

def main():
    df = pd.read_csv(CSV_PATH)

    cols_lower = {c.lower(): c for c in df.columns}
    needed = {"discipline", "model", "mode"}
    if not needed.issubset(set(cols_lower.keys())):
        raise SystemExit(f"CSV must contain columns: {sorted(needed)}")

    df = df.rename(columns={cols_lower["discipline"]: "discipline",
                            cols_lower["model"]: "model",
                            cols_lower["mode"]: "mode"})

    df["discipline"] = _canon(df["discipline"])
    df["model"] = _canon(df["model"])
    df = df[df["discipline"].isin(DISCIPLINES)]
    df = df[df["model"].isin(VALID_MODELS)]

    overall_rows = []

    for disc in DISCIPLINES:
        sub = df[df["discipline"] == disc].copy()

        groups = [sub.loc[sub["model"] == m, "mode"].dropna().to_numpy() for m in VALID_MODELS]
        present = [m for m, g in zip(VALID_MODELS, groups) if g.size > 0]
        non_empty = [g for g in groups if g.size > 0]

        if len(non_empty) >= 2:
            H, p_kw = kruskal(*non_empty)
        else:
            H, p_kw = (np.nan, np.nan)

        N = int(sum(g.size for g in groups))
        k = int(len(non_empty))
        eta2 = eta_squared_kw(H, k, N) if (isinstance(H, (int, float)) and isinstance(N, int) and k >= 2 and N > k) else np.nan

        overall_rows.append({
            "discipline": disc,
            "present_models": ",".join(present),
            "n_deepseek": int(groups[0].size),
            "n_gpt-4o": int(groups[1].size),
            "n_gpt-5": int(groups[2].size),
            "kruskal_H": H,
            "kruskal_p": p_kw,
            "eta2_kw": eta2
        })

        # Pairwise tests for all 3 pairs, regardless of KW significance
        pairs = [(VALID_MODELS[0], VALID_MODELS[1]),
                 (VALID_MODELS[0], VALID_MODELS[2]),
                 (VALID_MODELS[1], VALID_MODELS[2])]
        pvals = {}
        for a, b in pairs:
            x = sub.loc[sub["model"] == a, "mode"].dropna().to_numpy()
            y = sub.loc[sub["model"] == b, "mode"].dropna().to_numpy()
            if x.size == 0 or y.size == 0:
                pvals[f"{a} vs {b}"] = np.nan
            else:
                u, p_raw = mannwhitneyu(x, y, alternative="two-sided")
                pvals[f"{a} vs {b}"] = float(p_raw)

        # Holm correction on available p-values
        p_clean = {k: v for k, v in pvals.items() if isinstance(v, float) and np.isfinite(v)}
        if len(p_clean) > 0:
            holm_df = holm_bonferroni_correction(p_clean, alpha=0.05)
        else:
            holm_df = pd.DataFrame(columns=["comparison", "p_raw", "p_adj_holm", "reject_0.05"])

        # Reindex to fixed order and write per-discipline CSV
        target_order = [f"{VALID_MODELS[0]} vs {VALID_MODELS[1]}",
                        f"{VALID_MODELS[0]} vs {VALID_MODELS[2]}",
                        f"{VALID_MODELS[1]} vs {VALID_MODELS[2]}"]
        holm_df = holm_df.set_index("comparison").reindex(target_order).reset_index()
        holm_df.insert(0, "discipline", disc)
        holm_df.to_csv(OUT_DIR / f"posthoc_pairwise_holm_{disc}.csv", index=False)

    pd.DataFrame(overall_rows).to_csv(OUT_DIR / "overall_kruskal_summary.csv", index=False)
    print(f"Done. Wrote 5 CSVs to: {OUT_DIR}")

if __name__ == "__main__":
    main()
