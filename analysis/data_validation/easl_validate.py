"""
Ctrl-BIAS EASL dataset validator

Validation rules implemented:
1) nulls: flag null/blank in prompt_id, output_id, model, and score/rating (if present).
2) impossible scores: flag values outside the allowed inclusive range 1-5 or non-numeric.
3) mismatched ids: flag same output_id mapping to multiple prompt_ids or multiple models.
4) model coverage: each prompt must have outputs from all 3 models.
5) annotation presence: each output must have an annotation (any of the known columns).

output: a single csv file containing one row per validation issue.

usage:
  python easl_validate.py --input /path/to/inputdata.csv --out /path/to/qa_issues.csv

exit codes:
  0 = script ran successfully (issues may still be present; see csv)
  2 = script error (bad path, unreadable csv, etc.)
"""
import argparse
import sys
import pandas as pd
import numpy as np
from typing import List, Optional

#helper to find the first matching column name by candidate aliases (case-insensitive)
def find_col(candidates: List[str], df_cols: List[str]) -> Optional[str]:
    lower_map = {c.lower(): c for c in df_cols}
    for cand in candidates:
        if cand.lower() in lower_map:
            return lower_map[cand.lower()]
    return None

#main validation routine 
def validate_minimal(df: pd.DataFrame) -> pd.DataFrame:
    issues = []
    cols = df.columns.tolist()

    #identify columns by common aliases
    prompt_col = find_col(["prompt_id","prompt id","promptid","prompt"], cols)
    output_id_col = find_col(["output_id","output id","outputid","answer_id","response_id"], cols)
    model_col = find_col(["model","model_name","llm","generator"], cols)
    score_col = find_col(["score","rating"], cols)
    annot_cols_known = ["annotation","label","mode","annotator_score","worker_score","final_label"]
    ann_cols_present = [c for c in annot_cols_known if c in cols]

    #helper to add an issue row
    def add_issue(i, check_id, field, message, found_value=None):
        issues.append({
            "row_index": int(i),
            "check_id": check_id,
            "severity": "error",
            "field": field,
            "message": message,
            "prompt_id": (df.at[i, prompt_col] if prompt_col else None),
            "output_id": (df.at[i, output_id_col] if output_id_col else None),
            "model": (df.at[i, model_col] if model_col else None),
            "found_value": found_value
        })

    #rule 1 - nulls in prompt_id, output_id, model, and score/rating (if present)
    for key_col in [prompt_col, output_id_col, model_col]:
        if key_col and key_col in df.columns:
            null_mask = df[key_col].isna() | (df[key_col].astype(str).str.strip() == "")
            for i in np.where(null_mask)[0]:
                add_issue(i, "nulls", key_col, key_col + " is null or blank")
    if score_col and score_col in df.columns:
        null_mask = df[score_col].isna() | (df[score_col].astype(str).str.strip() == "")
        for i in np.where(null_mask)[0]:
            add_issue(i, "nulls", score_col, score_col + " is null or blank")

    #rule 2 - impossible scores, allowed inclusive range is 1-5; also flag non-numeric
    if score_col and score_col in df.columns:
        s = pd.to_numeric(df[score_col], errors="coerce")
        bad_mask = s.notna() & ((s < 1) | (s > 5))
        for i in np.where(bad_mask)[0]:
            add_issue(i, "impossible_score", score_col, "score outside allowed inclusive range 1-5", s.iloc[i])
        nonnum_mask = df[score_col].notna() & s.isna()
        for i in np.where(nonnum_mask)[0]:
            add_issue(i, "impossible_score", score_col, "non-numeric score value", df.at[i, score_col])

    #rule 3 - mismatched ids
    if output_id_col and output_id_col in df.columns:
        if prompt_col and prompt_col in df.columns:
            mapping = df.groupby(output_id_col, dropna=False)[prompt_col].nunique(dropna=False)
            bad_outputs = set(mapping[mapping > 1].index.tolist())
            bad_mask = df[output_id_col].isin(bad_outputs)
            for i in np.where(bad_mask)[0]:
                add_issue(i, "mismatched_ids", output_id_col + "+" + prompt_col, "same output_id maps to multiple prompt_ids")
        if model_col and model_col in df.columns:
            mapping_m = df.groupby(output_id_col, dropna=False)[model_col].nunique(dropna=False)
            bad_outputs_m = set(mapping_m[mapping_m > 1].index.tolist())
            bad_mask_m = df[output_id_col].isin(bad_outputs_m)
            for i in np.where(bad_mask_m)[0]:
                add_issue(i, "mismatched_ids", output_id_col + "+" + model_col, "same output_id maps to multiple models")

    #rule 4 - each prompt must have outputs from all 3 models
    if prompt_col and model_col and prompt_col in df.columns and model_col in df.columns:
        model_counts = df.groupby(prompt_col, dropna=False)[model_col].nunique(dropna=True)
        bad_prompts = set(model_counts[model_counts != 3].index.tolist())
        bad_mask = df[prompt_col].isin(bad_prompts)
        for i in np.where(bad_mask)[0]:
            add_issue(i, "model_coverage", model_col, "prompt does not have outputs from all 3 models")

    #rule 5 - each output must have an annotation in any known annotation column
    if len(ann_cols_present) == 0:
        for i in range(len(df)):
            add_issue(i, "annotation_missing", "", "no annotation columns found in dataset")
    else:
        has_ann = df[ann_cols_present].apply(lambda r: any(pd.notna(v) and str(v).strip() != "" for v in r), axis=1)
        for i in np.where(~has_ann)[0]:
            add_issue(i, "annotation_missing", ",".join(ann_cols_present), "output has no annotation")

    out_df = pd.DataFrame(issues, columns=[
        "row_index","check_id","severity","field","message","prompt_id","output_id","model","found_value"
    ])
    return out_df

#entry point with only --input, --out, and --help
def main():
    epilog_text = (
        "example:\n"
        r'  python easl_validate.py --input "c:\data\gender.csv" --out "c:\data\qa_issues.csv' + "\n"
    )
    parser = argparse.ArgumentParser(
        description=(
            "validates a dataset per jira task: checks for nulls, impossible scores (1-5), "
            "mismatched ids, model coverage of 3 per prompt, and presence of annotations. "
            "writes a single csv of issues."
        ),
        epilog=epilog_text,
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("--input", required=True, metavar="PATH", help="path to input csv file")
    parser.add_argument("--out", required=True, metavar="PATH", help="path to output csv file for validation issues")
    args = parser.parse_args()

    try:
        df = pd.read_csv(args.input)
    except Exception as e:
        print("ERROR: failed to read csv: " + str(e), file=sys.stderr)
        sys.exit(2)

    issues_df = validate_minimal(df)

    try:
        issues_df.to_csv(args.out, index=False)
    except Exception as e:
        print("ERROR: failed to write output csv: " + str(e), file=sys.stderr)
        sys.exit(2)

    sys.exit(0)

if __name__ == "__main__":
    main()
