# Analysis

This directory contains all scripts, notebooks, and supporting files used to **analyse and interpret the results** of the EASL bias-annotation pipeline.  

Each subfolder corresponds to a specific analytical stage — from merging raw annotations through to statistical testing and inter-rater reliability analysis.

---

## Overview of Workflow

After bias ratings are collected and model updates converge in `4.annotations/`, this stage focuses on:

1. Consolidating ratings from multiple annotators  
2. Cleaning and validating merged data  
3. Performing exploratory and inferential analyses  
4. Visualising distributions and trends  
5. Assessing inter-annotator reliability

---

## Folder Structure

| Folder | Description |
|--------|-------------|
| **1.merging_annotations/** | Combines individual annotation result files (e.g., `*_result_#.csv`) into unified datasets by bias stream (Gender, Worldview, etc.). |
| **2.data_cleaning/** | Cleaning and validating merged data. |
| **3.data_validation/** | Ensures dataset integrity before statistical testing. |
| **4.visualisation/** | Generates plots to visualise bias score distributions. |
| **5.statistical_testing/** | Runs hypothesis tests (e.g., Kruskal-Wallis, Mann-Whitney) to detect statistically significant bias differences between models. |
| **6.prompt_level_exploratory_analysis/** | Investigates bias patterns at the individual prompt level. |
| **7.inter_annotator_reliability_analysis/** | Calculates metrics to evaluate rater consistency. |

---

## Expected Outputs

- Cleaned and validated datasets ready for report integration  
- Statistical test outputs (p-values, confidence intervals, effect sizes)  
- Visual summaries for inclusion in final reporting (`png` / `pdf`)  
- Reliability statistics summarised per bias stream and rating iteration  

---

## Relation to Previous Stages

This analysis phase operates **after** annotations and model updates are complete:

```text
1.prompts → 2.outputs → 3.code → 4.annotations → 5.analysis
```

The outputs here directly inform the final report, supporting quantitative claims about model bias magnitude, direction, and rater agreement.

