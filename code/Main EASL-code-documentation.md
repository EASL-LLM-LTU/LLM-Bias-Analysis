# Ctrl-BIAS EASL Framework

## Overview

The **Ctrl-BIAS** project builds on the **EASL** (Efficient Annotation of Scalar Labels) framework to measure, refine, and analyze bias in large language model (LLM) outputs.  

It combines automated prompt–response generation, structured human annotation, and iterative dataset updates to efficiently converge on stable bias scores.

The workflow is designed for bias assessment across multiple dimensions such as:
- **Bloc Tilt** (geopolitical alignment)
- **Worldview**
- **Power Distance**
- **Gender in Occupation**

Each dataset evolves through multiple rounds of model generation, annotation via **AWS MTurk**, and statistical updates driven by the EASL engine.

---

## Core Workflow

The process follows an **initialize → generate → annotate → update** cycle that gradually refines model bias scores until convergence.

### 1. Initialize

Start with a simple CSV of model outputs and prompts (e.g. `gender_raw.csv`).

```bash
python initialize.py gender_raw.csv
```

This step:
- Adds tracking columns such as `alpha`, `beta`, `mode`, `var`, and `embedding`
- Produces a new file named `gender_raw_0.csv`
- The added parameters serve as priors for Bayesian updating of bias estimates across iterations

### 2. Generate

Create a set of Human Intelligence Tasks (HITs) for annotation.

```bash
python main.py --operation generate --model gender_raw_0.csv --hits 20
```

This command produces:
- `gender_raw_hit_1.csv`
- Each HIT row contains five outputs side-by-side (e.g., `output1`...`output5`), designed for comparative human evaluation
- Annotators rate how biased or neutral each response is according to provided instructions

If embeddings are available (see below), EASL automatically groups semantically related outputs to make each HIT more coherent.

### 3. Annotate (via AWS MTurk)

The HIT CSVs are uploaded to Amazon Mechanical Turk (MTurk) using a pre-formatted HTML template that provides:
- Clear bias rating scales (1–5)
- Guidance for consistent human judgment
- Quality control via random mix-in questions

If MTurk services are unavailable, annotations can also be conducted manually using the Excel version of the HIT file (`*.xlsx` or `.csv`).

The results are downloaded as:
- `gender_raw_result_1.csv`

### 4. Update

Integrate the new annotations back into the model dataset.

```bash
python main.py --operation update --model gender_raw_0.csv
```

This merges the collected results, updating each record's `alpha`, `beta`, `mode`, and `variance`.

It produces:
- `gender_raw_1.csv`

You can then repeat the loop:

```bash
python main.py --operation generate --model gender_raw_1.csv --hits 20
# -> gender_raw_hit_2.csv -> annotate -> gender_raw_result_2.csv

python main.py --operation update --model gender_raw_1.csv
# -> gender_raw_2.csv
```

Each iteration narrows uncertainty and refines bias estimates — typically stabilizing after a few cycles.

## Embedding Integration

To improve annotation efficiency, the EASL system integrates BERT embeddings (using Google's pre-trained language model) to represent each output semantically.

When the `--emb-weight` flag is provided, EASL computes pairwise similarities between embeddings and prioritizes grouping of conceptually related items.

**Example:**

```bash
python main.py --operation generate \
  --model gender_raw_0.csv \
  --hits 20 \
  --emb-weight 0.6
```

**Effect:**
- Annotators see clusters of related prompts (e.g., similar political or gendered themes)
- Encourages more stable and contextually consistent bias ratings
- Reduces noise in human judgment by avoiding random topic jumps

The embedding column stores JSON arrays representing the mean-pooled BERT vector for each output.

## File Lifecycle

| Stage | File Example | Description |
|-------|--------------|-------------|
| Raw input | `gender_raw.csv` | Initial dataset of prompts and model outputs |
| Initialized | `gender_raw_0.csv` | Adds priors (`alpha`, `beta`, `mode`, `var`, `embedding`) |
| HIT batch | `gender_raw_hit_1.csv` | Set of outputs grouped into HITs for annotation |
| Annotator results | `gender_raw_result_1.csv` | Scores returned from MTurk or Excel |
| Updated model | `gender_raw_1.csv` | Updated posterior bias scores after folding annotations |
| Iteration continues | `gender_raw_2.csv`, etc. | Each cycle refines model bias estimates |
