# Code

This folder contains the full implementation of the **Ctrl-BIAS EASL pipeline** — a modular system for efficient human-in-the-loop bias evaluation using the *Efficient Annotation of Scalar Labels (EASL)* framework.

---

## Structure Overview

| File / Folder | Purpose |
|----------------|----------|
| **main.py** | Entry point — runs EASL operations (`generate`, `update`, `analyze`). |
| **initialize.py** | Prepares raw outputs for EASL: adds priors (`alpha`, `beta`, `mode`, `var`, `embedding`). |
| **easl.py** | Core engine implementing the EASL update logic and item selection (variance + embedding-based). |
| **encode_emoji.py** | Helper to encode and decode emoji safely when writing CSVs. |
| **EASL-CODE_DOCUMENTATION.md** | Detailed explanation of the pipeline, file lifecycle, and embedding logic. |
| **CHANGE-LOG.md** | Summarised code updates across iterations and modules. |
| **MTurk/** | Sub-module for creating, uploading, and processing Human Intelligence Tasks (HITs). |
| **README.md** | This overview. |

---

## Environment Requirements

**Python:** 3.9 – 3.11  
**Memory:** ≥ 8 GB  
**Internet:** required once to download Hugging Face models

**Packages used**
- `numpy`
- `pandas`
- `torch`
- `transformers`

To install dependencies:
```bash
pip install numpy pandas torch transformers
```

## How this works

1. Start with a simple CSV of model outputs and prompts.  (can use something like gender_raw.csv)


2. Run `initialize.py` once – it adds some extra tracking columns (alpha, beta, mode, var, embedding).
   ```bash
   python initialize.py gender_raw.csv
   ```
 - above code creates gender_raw_0.csv


3.	Run main.py generate – it makes a HIT file (*_hit_1.csv) where each row has 5 outputs side-by-side for people to score.
   ```bash
   python main.py --operation generate --model gender_raw_0.csv --hits 20
   ```
 - above code creates gender_raw_hit_1.csv


4. Annotators rate those, we need to save their answers as *_result_1.csv.


5. Run main.py update - the scores get folded back into the model, producing a new CSV (*_1.csv) with updated values.
   ```bash   
   python main.py --operation update --model gender_raw_0.csv
   ```
- above code creates gender_raw_1.csv


6. just repeat: generate → annotate → update… until the scores settle down.
   ```bash
   python main.py --operation generate --model gender_raw_1.csv --hits 20
   # -> gender_raw_hit_2.csv -> annotate -> gender_raw_result_2.csv
   python main.py --operation update --model gender_raw_1.csv
   # -> gender_raw_2.csv
   ```


# What to expect
- The HIT CSVs will look wide (lots of repeated columns like output1..5), because each row is a “batch” of items to rate.

  
- When adding embeddings (stored as JSON arrays in the embedding column), the system will try to group semantically similar outputs together, so annotators rate things that are topically related.
  ```bash   
  python main.py --operation generate --model gender_raw_0.csv --hits 20 --emb-weight 0.6
  ```


- At the end, we’ll have a CSV with refined bias scores (mode and var) for every output, without needing to label the entire dataset.  

## Further Reading

For further information, refer to:   
- [EASL-CODE_DOCUMENTATION.md](./EASL-CODE_DOCUMENTATION.md) — full pipeline explanation and file lifecycle  
- [CHANGE-LOG.md](./CHANGE-LOG.md) — module-by-module update history
