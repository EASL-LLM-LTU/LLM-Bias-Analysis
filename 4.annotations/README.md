# Annotations

This directory contains all annotated datasets and iterative model updates generated through the **EASL (Efficient Annotation of Scalar Labels)** framework for the Ctrl-BIAS project.  
Each subfolder corresponds to one **bias stream** (e.g., Gender, Worldview, Power Distance, Bloc Tilt).

---

## Folder Structure

| Folder / File | Description |
|----------------|-------------|
| **gender/**, **worldview/**, etc. | Contain the full sequence of EASL outputs, HIT batches, results, and updates for each bias domain. |
| **statistical_foundations_stopping_criteria.md** | Explains the mathematical underpinnings of the EASL process — including Beta updates, uncertainty reduction, and stopping criteria for annotation. |

---

## EASL Iteration Overview

Each stream follows the same update cycle: 

```text
initialize → generate → annotate → update → repeat
```

### File Types

- **HIT files (`*_raw_hit_#.csv`)** — Batches prepared for annotation.  
- **Result files (`*_result_#.csv`)** — Collected ratings from MTurk or manual Excel annotation.  
- **Updated models (`*_raw_#.csv`)** — EASL posterior updates reflecting new bias scores and reduced uncertainty.  

Over successive iterations, the `mode` and `var` columns converge — indicating stable bias estimation.

---

### Example (Gender Stream)

| File Type | Example | Purpose |
|------------|----------|----------|
| **HIT batch** | `gender_raw_hit_7.csv` | Dataset presented to annotators for scoring. |
| **Result file** | `gender_raw_result_7.csv` | Worker ratings collected and cleaned. |
| **Updated model** | `gender_raw_7.csv` | Posterior bias parameters updated via EASL. |

---

### Reference

For a detailed explanation of variance thresholds, Beta updating, and stopping conditions, see:  
- [statistical_foundations_stopping_criteria.md](./statistical_foundations_stopping_criteria.md)

---
