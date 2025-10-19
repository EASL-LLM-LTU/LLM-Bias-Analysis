#!/usr/bin/env python3
"""
Prompt-Level Exploratory Analysis for EASL
-------------------------------------------
Analyzes which prompt structures trigger bias in model responses.

Input CSV: finalscores_allstreams.csv
Outputs:
  - prompt_top_overall.csv
  - prompt_top_by_discipline.csv
  - keywords_support.csv
  - keywords_by_discipline.csv
  - analysis_report.md
"""

import os
import re
from collections import Counter, defaultdict

import numpy as np
import pandas as pd

REQUIRED_COLUMNS = [
    "output_id", "output", "prompt_id", "prompt", "alpha", "beta", "mode", "var",
    "ci_80_lower", "ci_80_upper", "ci_width", "discipline", "model"
]

STOPWORDS = {
    "a","an","the","and","or","but","if","so","than","then","that","those","these","this","to","for","of","in",
    "on","at","as","by","be","is","are","was","were","it","its","with","from","into","over","under","up","down",
    "not","no","do","does","did","should","would","could","can","may","might","must","will","shall","their",
    "there","they","them","he","she","his","her","we","us","our","you","your","i","me","my","one","all","any",
    "each","every","some","most","more","less","many","few","much","also","about","such","which","who","whom"
}

# Configuration - Edit these defaults if needed
INPUT_FILE = "finalscores_allstreams.csv"
OUTPUT_DIR = "prompt_analysis_results"
TOP_K_OVERALL = 15
TOP_K_PER_DISCIPLINE = 8
HIGH_BIAS_QUANTILE = 0.90
TOP_M_KEYWORDS = 20

def ensure_outdir(path: str):
    os.makedirs(path, exist_ok=True)

def validate_columns(df: pd.DataFrame):
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

def light_tokenize(text: str):
    if not isinstance(text, str):
        return []
    text = text.lower()
    text = re.sub(r"[^a-z0-9'\-]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return [t for t in text.split(" ") if t]

def ngrams(tokens, n=2):
    return [" ".join(tokens[i:i+n]) for i in range(len(tokens)-n+1)]

def aggregate_prompt(df: pd.DataFrame) -> pd.DataFrame:
    agg = (
        df.groupby(["prompt_id", "prompt", "discipline"], dropna=False)
        .agg(
            mean_bias=("mode", "mean"),
            mean_ci=("ci_width", "mean"),
            n_models=("model", "nunique"),
        )
        .reset_index()
    )
    agg.sort_values("mean_bias", ascending=False, inplace=True)
    return agg

def top_overall(agg: pd.DataFrame, k: int) -> pd.DataFrame:
    cols = ["prompt_id", "discipline", "prompt", "mean_bias", "mean_ci", "n_models"]
    return agg.head(k)[cols]

def top_by_discipline(agg: pd.DataFrame, k: int) -> pd.DataFrame:
    frames = []
    for disc, g in agg.groupby("discipline", dropna=False):
        frames.append(g.head(k))
    out = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(columns=agg.columns)
    cols = ["discipline", "prompt_id", "prompt", "mean_bias", "mean_ci", "n_models"]
    return out[cols]

def keyword_support(agg: pd.DataFrame, high_q: float, top_m: int) -> pd.DataFrame:
    thr = agg["mean_bias"].quantile(high_q)
    high = agg[agg["mean_bias"] >= thr].copy()

    uni_counts = Counter()
    bi_counts = Counter()
    for text in high["prompt"].fillna("").astype(str):
        toks = [t for t in light_tokenize(text) if t not in STOPWORDS and len(t) > 1]
        uni_counts.update(toks)
        bi_counts.update(ngrams(toks, 2))

    global_mean = float(agg["mean_bias"].mean())
    token_sum = defaultdict(float); token_cnt = defaultdict(int)
    bigram_sum = defaultdict(float); bigram_cnt = defaultdict(int)

    for text, bias in zip(agg["prompt"].astype(str), agg["mean_bias"].astype(float)):
        toks = [t for t in light_tokenize(text) if t not in STOPWORDS and len(t) > 1]
        u_uni = set(toks); u_bi = set(ngrams(toks, 2))
        for t in u_uni:
            token_sum[t] += bias; token_cnt[t] += 1
        for t in u_bi:
            bigram_sum[t] += bias; bigram_cnt[t] += 1

    rows = []
    for tok, cnt in uni_counts.most_common(top_m):
        avg_bias = token_sum.get(tok, 0.0) / max(token_cnt.get(tok, 1), 1)
        rows.append(("unigram", tok, cnt, avg_bias, avg_bias - global_mean))
    for tok, cnt in bi_counts.most_common(top_m):
        avg_bias = bigram_sum.get(tok, 0.0) / max(bigram_cnt.get(tok, 1), 1)
        rows.append(("bigram", tok, cnt, avg_bias, avg_bias - global_mean))

    kw = pd.DataFrame(rows, columns=["type","token","count_in_highbias","avg_bias_across_all_prompts","delta_vs_global_mean"])
    kw["global_mean_bias"] = global_mean
    kw["highbias_threshold"] = thr
    return kw

def keyword_by_discipline(agg: pd.DataFrame, high_q: float, top_m: int) -> pd.DataFrame:
    """Compare keyword patterns across disciplines."""
    rows = []
    
    for disc in agg["discipline"].unique():
        disc_data = agg[agg["discipline"] == disc].copy()
        if len(disc_data) == 0:
            continue
            
        thr = disc_data["mean_bias"].quantile(high_q)
        high = disc_data[disc_data["mean_bias"] >= thr].copy()
        
        uni_counts = Counter()
        for text in high["prompt"].fillna("").astype(str):
            toks = [t for t in light_tokenize(text) if t not in STOPWORDS and len(t) > 1]
            uni_counts.update(toks)
        
        disc_mean = float(disc_data["mean_bias"].mean())
        token_sum = defaultdict(float); token_cnt = defaultdict(int)
        
        for text, bias in zip(disc_data["prompt"].astype(str), disc_data["mean_bias"].astype(float)):
            toks = [t for t in light_tokenize(text) if t not in STOPWORDS and len(t) > 1]
            for t in set(toks):
                token_sum[t] += bias; token_cnt[t] += 1
        
        for tok, cnt in uni_counts.most_common(top_m):
            avg_bias = token_sum.get(tok, 0.0) / max(token_cnt.get(tok, 1), 1)
            rows.append((disc, tok, cnt, avg_bias, avg_bias - disc_mean, disc_mean, thr))
    
    kw_disc = pd.DataFrame(rows, columns=[
        "discipline", "token", "count_in_highbias", 
        "avg_bias_in_discipline", "delta_vs_disc_mean",
        "discipline_mean_bias", "highbias_threshold"
    ])
    return kw_disc

def create_summary_report(agg: pd.DataFrame, high_q: float) -> pd.DataFrame:
    """Create a summary statistics report as a DataFrame."""
    n_prompts = agg["prompt_id"].nunique()
    n_disciplines = agg["discipline"].nunique()
    global_mean = float(agg["mean_bias"].mean())
    global_median = float(agg["mean_bias"].median())
    global_ci = float(agg["mean_ci"].mean())
    thr = float(agg["mean_bias"].quantile(high_q))
    
    # Overall summary
    summary_data = {
        "metric": [
            "total_prompts",
            "total_disciplines", 
            "global_mean_bias",
            "global_median_bias",
            "global_mean_ci_width",
            "high_bias_threshold"
        ],
        "value": [
            n_prompts,
            n_disciplines,
            round(global_mean, 3),
            round(global_median, 3),
            round(global_ci, 3),
            round(thr, 3)
        ]
    }
    
    return pd.DataFrame(summary_data)

def main():
    print("=" * 60)
    print("EASL Prompt-Level Exploratory Analysis")
    print("=" * 60)
    
    ensure_outdir(OUTPUT_DIR)
    
    print(f"\n📂 Reading input: {INPUT_FILE}")
    df = pd.read_csv(INPUT_FILE)
    validate_columns(df)
    print(f"✓ Loaded {len(df)} rows")
    
    print("\n🔄 Aggregating prompts by mean bias...")
    agg = aggregate_prompt(df)
    
    print("📊 Extracting top prompts...")
    topK = top_overall(agg, TOP_K_OVERALL)
    topDisc = top_by_discipline(agg, TOP_K_PER_DISCIPLINE)
    
    print("\n💾 Saving results...")
    path_top = os.path.join(OUTPUT_DIR, "prompt_top_overall.csv")
    path_disc = os.path.join(OUTPUT_DIR, "prompt_top_by_discipline.csv")
    topK.to_csv(path_top, index=False)
    topDisc.to_csv(path_disc, index=False)
    print(f"  ✓ {os.path.basename(path_top)}")
    print(f"  ✓ {os.path.basename(path_disc)}")
    
    print("\n🔍 Analyzing keywords in high-bias prompts...")
    kw = keyword_support(agg, HIGH_BIAS_QUANTILE, TOP_M_KEYWORDS)
    path_kw = os.path.join(OUTPUT_DIR, "keywords_support.csv")
    kw.to_csv(path_kw, index=False)
    print(f"  ✓ {os.path.basename(path_kw)}")
    
    kw_disc = keyword_by_discipline(agg, HIGH_BIAS_QUANTILE, TOP_M_KEYWORDS)
    path_kw_disc = os.path.join(OUTPUT_DIR, "keywords_by_discipline.csv")
    kw_disc.to_csv(path_kw_disc, index=False)
    print(f"  ✓ {os.path.basename(path_kw_disc)}")
    
    print("\n📊 Generating summary report...")
    summary = create_summary_report(agg, HIGH_BIAS_QUANTILE)
    path_summary = os.path.join(OUTPUT_DIR, "summary_statistics.csv")
    summary.to_csv(path_summary, index=False)
    print(f"  ✓ {os.path.basename(path_summary)}")
    
    print("\n" + "=" * 60)
    print("✅ Analysis complete!")
    print(f"📁 All outputs saved to: {OUTPUT_DIR}/")
    print("=" * 60)

if __name__ == "__main__":
    main()
