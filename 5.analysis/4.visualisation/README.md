# Visualisation

This folder contains all scripts, plots, and data files used to **visualise bias scores and rating patterns** across the four EASL bias streams:  
**Gender, Worldview, Power Distance, and Bloc Tilt.**

The visual outputs here help interpret how scores evolve and stabilise through the EASL pipeline, showing distributional patterns, confidence intervals, and prompt-level differences.

---

## Folder Structure

| File / Folder | Description |
|----------------|-------------|
| **raw_annotations_combined.csv** | Input dataset containing all raw ratings merged across annotators and streams (2160 rows = 540 ratings × 4 bias streams). Used for stacked proportion plots. |
| **finalscores_allstreams.csv** | Input dataset containing final bias estimates (α, β, mode, variance) for all 1080 items (270 outputs × 4 streams). Used for Beta PDF, dot–CI, and heatmap visualisations. |
| **beta-pdf_plots/** | Contains Beta probability density plots for each bias stream — showing distribution of posterior estimates from EASL (α, β). |
| **error-bar-CI_plots/** | Contains visualisations of pooled mean bias modes with error bars representing 95% confidence intervals. |
| **heatmap-per-prompt_plots/** | Contains heatmaps showing prompt-level bias distributions across LLMs or bias categories. Each tile corresponds to one prompt’s pooled bias score. |
| **stacked-proportion_plots/** | Contains stacked bar charts visualising proportional ratings (1–5) from human annotators across streams. Derived from `raw_annotations_combined.csv`. |
| **interpretation_example.pdf** | Example figure used for reporting, showing how to interpret pooled Beta scores and visual outputs. |

---

## Data Overview

| Dataset | Rows | Description |
|----------|------|-------------|
| `raw_annotations_combined.csv` | 2160 | All annotated ratings (540 items × 4 streams). Used for stacked proportion plots. |
| `finalscores_allstreams.csv` | 1080 | Final EASL posterior scores per output (270 × 4 streams). Used for all Beta/CI-based plots. |

---

## Plot Purposes

| Plot Type | Input | Purpose |
|------------|--------|----------|
| **Stacked Proportion Plot** | `raw_annotations_combined.csv` | Visualises the distribution of human ratings (1–5) across streams. |
| **Beta PDF Plot** | `finalscores_allstreams.csv` | Plots the Beta(α, β) distributions showing uncertainty and skew in model bias estimates. |
| **Dot + CI Plot** | `finalscores_allstreams.csv` | Plots pooled mean bias modes with 95% confidence intervals to compare across streams. |
| **Heatmap per Prompt** | `finalscores_allstreams.csv` | Displays prompt-level bias strength or direction as colour gradients across all streams. |

---

## Integration with Analysis

This visualisation phase follows after cleaned and validated results are produced in:
```text
3.data_validation → 4.visualisation → 5.statistical_testing
```
These plots are used for reporting, interpretation, and presentation in the final Ctrl-BIAS project documentation.