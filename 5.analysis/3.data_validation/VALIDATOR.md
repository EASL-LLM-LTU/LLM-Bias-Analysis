# Ctrl‑BIAS EASL Dataset Validator

## Purpose

This script validates consolidated EASL‑style annotation datasets for the **Ctrl‑BIAS** project. It scans a CSV and generates an **issues CSV** where each row represents a data quality issue (e.g., nulls, invalid scores, ID mismatches, missing annotations). Designed for use in CI/CD or pre‑merge data validation.

---

## Overview

The script performs these key actions:

1. **Load** the input dataset (`.csv`) into a pandas DataFrame.
2. **Auto‑detect** columns by common aliases for prompt IDs, output IDs, model names, scores, and annotations.
3. **Apply validation rules** to detect data inconsistencies.
4. **Write all detected issues** to an output `.csv` file.
5. **Exit** with status code `0` for success or `2` for file read/write errors.

---

## Validation Rules

Each detected issue is written as one row in the output CSV.

| Rule ID              | Description              | Checks                                                             | Output Column      |
| -------------------- | ------------------------ | ------------------------------------------------------------------ | ------------------ |
| `nulls`              | Missing key fields       | Null or blank values in `prompt_id`, `output_id`, `model`, `score` | `field`, `message` |
| `impossible_score`   | Invalid score values     | Scores outside `1–5` or non‑numeric                                | `found_value`      |
| `mismatched_ids`     | Inconsistent ID mappings | Same `output_id` linked to multiple prompts or models              | `field`, `message` |
| `model_coverage`     | Missing model outputs    | Each `prompt_id` must have outputs from **3 models**               | `model`            |
| `annotation_missing` | Missing annotations      | Rows without any non‑blank annotation fields                       | `field`, `message` |

---

## Column Auto‑Detection

The script finds columns using case‑insensitive matching:

* **Prompt ID:** `prompt_id`, `prompt id`, `promptid`, `prompt`
* **Output ID:** `output_id`, `output id`, `outputid`, `answer_id`, `response_id`
* **Model:** `model`, `model_name`, `llm`, `generator`
* **Score:** `score`, `rating`
* **Annotation (any of):** `annotation`, `label`, `mode`, `annotator_score`, `worker_score`, `final_label`

If **no annotation column** is found, every row will be flagged as missing annotations.

---

## Command Line Usage

```bash
python easl_validate.py --input /path/to/input.csv --out /path/to/issues.csv
```

### Exit Codes

| Code | Meaning                                          |
| ---- | ------------------------------------------------ |
| `0`  | Script ran successfully (issues may still exist) |
| `2`  | Error reading or writing CSV                     |

---

## Example

**Command:**

```bash
python easl_validate.py \
  --input ./data/master/worldview.csv \
  --out ./data/qa/worldview_issues.csv
```

**Arbitrary Sample Output (qa_issues.csv):**

| row_index | check_id           | field               | message                                        | prompt_id | output_id | model  | found_value |
| --------- | ------------------ | ------------------- | ---------------------------------------------- | --------- | --------- | ------ | ----------- |
| 12        | nulls              | output_id           | output_id is null or blank                     | P‑001     |           | gpt‑4o |             |
| 98        | impossible_score   | rating              | score outside allowed range 1‑5                | P‑014     | O‑422     | ds‑r1  | 5.8         |
| 201       | mismatched_ids     | output_id+prompt_id | same output_id maps to multiple prompt_ids     | P‑008     | O‑377     | gpt‑5  |             |
| 455       | model_coverage     | model               | prompt does not have outputs from all 3 models | P‑019     | O‑910     | ds‑r1  |             |
| 730       | annotation_missing | annotation,label    | output has no annotation                       | P‑033     | O‑1202    | gpt‑5  |             |

---

## Input and Output Details

### Input CSV Requirements

* Must include columns mappable to `prompt_id`, `output_id`, and `model`.
* Optionally include a `score` or `rating`.
* Should include at least one known annotation column.

### Output CSV Schema

| Column        | Description                         |
| ------------- | ----------------------------------- |
| `row_index`   | Row number in input dataset         |
| `check_id`    | Validation rule triggered           |
| `severity`    | Always `error` (future extension)   |
| `field`       | Column name(s) where issue occurred |
| `message`     | Human‑readable description of issue |
| `prompt_id`   | Copied from input                   |
| `output_id`   | Copied from input                   |
| `model`       | Copied from input                   |
| `found_value` | Relevant value (for score issues)   |

---

## Installation

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install pandas numpy
```

### Requirements

* **Python 3.9+**
* **pandas**, **numpy**

---

## Batch Validation

To validate all merged datasets at once:

```bash
for f in ./data/master/*.csv; do
  python easl_validate.py --input "$f" --out "./data/qa/$(basename "$f" .csv)_issues.csv"
done
```

---

## CI/CD Integration

* Run automatically when datasets are updated.
* Treat **non‑empty** issue CSV as a *soft warning*.
* Treat **exit code 2** as a *hard failure*.

---

## Troubleshooting

| Error Message                        | Possible Cause                            | Fix                            |
| ------------------------------------ | ----------------------------------------- | ------------------------------ |
| `ERROR: failed to read csv:`         | Invalid path or malformed CSV             | Check file path or format      |
| `ERROR: failed to write output csv:` | Missing directory or permissions          | Ensure output directory exists |
| Empty issues file                    | Column names don’t match expected aliases | Use canonical column names     |

---

## Extending the Validator

* Add new column aliases inside `find_col()` or `annot_cols_known`.
* Add new rules by inserting sections in `validate_minimal()`.
* Introduce `warning` severity for non‑critical checks (e.g., length, casing).


