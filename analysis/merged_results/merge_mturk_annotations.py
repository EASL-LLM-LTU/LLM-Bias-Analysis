import argparse
import json
import re
from pathlib import Path
from typing import List, Dict, Any, Tuple

import pandas as pd
import numpy as np

DEFAULT_ITEM_RANGE = range(1, 7)  # 1..6 items per HIT

# Columns we expect from MTurk export (kept as metadata)
MTURK_META_COLS = [
    "HITId","HITTypeId","Title","Description","Keywords","Reward","CreationTime",
    "MaxAssignments","RequesterAnnotation","AssignmentDurationInSeconds","AutoApprovalDelayInSeconds",
    "Expiration","NumberOfSimilarHITs","LifetimeInSeconds","AssignmentId","WorkerId","AssignmentStatus",
    "AcceptTime","SubmitTime","AutoApprovalTime","ApprovalTime","RejectionTime","RequesterFeedback",
    "WorkTimeInSeconds","LifetimeApprovalRate","Last30DaysApprovalRate","Last7DaysApprovalRate",
    "Approve","Reject"
]

# Per-item input columns template
INPUT_TPL = {
    "output_id": "Input.output_id{idx}",
    "output":    "Input.output{idx}",
    "prompt_id": "Input.prompt_id{idx}",
    "prompt":    "Input.prompt{idx}",
    "alpha":     "Input.alpha{idx}",
    "beta":      "Input.beta{idx}",
    "mode":      "Input.mode{idx}",
    "var":       "Input.var{idx}",
    "embedding": "Input.embedding{idx}",
}

def find_annotation_col(columns: List[str], idx: int, discipline_label: str) -> str | None:
    """
    Return the column name for the annotation range for the given item index.
    Priority:
      1) Exact expected name based on discipline_label
      2) Fallback: any 'Answer.Answer.<something>_range{idx}' found in the CSV
    """
    label_to_prefix = {
        "gender_in_occupation": "gender",
        "power_distance": "power",
        "bloc_tilt": "bloc",
        "worldview": "worldview",
    }
    prefix = label_to_prefix.get(discipline_label, "")
    if prefix:
        expected = f"Answer.Answer.{prefix}_range{idx}"
        if expected in columns:
            return expected
    # Fallback: regex scan
    pattern = re.compile(rf"^Answer\.Answer\.[A-Za-z]+_range{idx}$")
    for col in columns:
        if pattern.match(col):
            return col
    return None

# Output normalized schema columns (order)
NORMALIZED_COLS = [
    # Provenance
    "source_file",
    "hit_id","hit_type_id","assignment_id","worker_id","assignment_status",
    "accept_time","submit_time","approval_time","rejection_time",
    # Item identity
    "item_index","prompt_id","prompt","output_id","output",
    # Model / discipline (discipline inferred from filename; model may be blank for now)
    "discipline","model",
    # EASL priors
    "alpha","beta","mode","var",
    # Embedding (JSON as text)
    "embedding",
    # Annotation
    "annotation_range","comment_optional",
    # Useful extras
    "work_time_seconds","reward"
]

DISCIPLINES = [
    {"menu": "gender", "file_prefix": "gender", "label": "gender_in_occupation"},
    {"menu": "worldview", "file_prefix": "worldview", "label": "worldview"},
    {"menu": "bloc tilt", "file_prefix": "bloctilt", "label": "bloc_tilt"},
    {"menu": "power distance", "file_prefix": "powerdistance", "label": "power_distance"},
]

def safe_get(row: pd.Series, col: str) -> Any:
    return row[col] if col in row else None

def infer_discipline_from_filename(fname: str) -> str:
    name = Path(fname).name.lower()
    # crude inference based on filename prefix
    if "gender" in name:
        return "gender_in_occupation"
    if "worldview" in name:
        return "worldview"
    if "bloc" in name or "tilt" in name:
        return "bloc_tilt"
    if "power" in name:
        return "power_distance"
    return "unknown"

def parse_args():
    p = argparse.ArgumentParser(description="Merge MTurk 6-up annotation CSVs into long format.")
    p.add_argument("--outdir", default="data/master", help="Directory to write outputs")
    p.add_argument("--outfile", default=None, help="Optional explicit output CSV filename")
    return p.parse_args()

def infer_model_heuristic(text: str) -> str | None:
    if not text:
        return None
    text_l = text.lower()
    if "deepseek" in text_l:
        return "deepseek"
    if "gpt-5" in text_l or "gpt5" in text_l:
        return "gpt-5"
    if "gpt-4o" in text_l or "4o" in text_l or "chatgpt-4o" in text_l:
        return "gpt-4o"
    return None

def model_from_output_id(output_id: str) -> str | None:
    """
    Map output_id prefixes to model names.
    Rules (case-insensitive):
      - Gender:   G4o-* -> gpt-4o, G5-* -> gpt-5, GD-* -> deepseek
      - Worldview:W4o-* -> gpt-4o, W5-* -> gpt-5, WD-* -> deepseek
      - Bloc tilt:B4o-* -> gpt-4o, B5-* -> gpt-5, BD-* -> deepseek
      - Power dist:P4o-* -> gpt-4o, P5-* -> gpt-5, PD-* -> deepseek
    """
    if not output_id:
        return None
    s = str(output_id).strip().lower()
    # normalize hyphen variants
    # expected like g4o-053, p5-093, pd-093, etc.
    if re.match(r'^[gwbp]4o-', s):
        return 'gpt-4o'
    if re.match(r'^[gwbp]5-', s):
        return 'gpt-5'
    if re.match(r'^[gwbp]d-', s):  # GD-, WD-, BD-, PD-
        return 'deepseek'
    return None

def load_files_for_discipline(file_prefix: str) -> List[Path]:
    files = []
    idx = 0
    while True:
        filename = f"{file_prefix}_raw_result_{idx}.csv"
        path = Path(filename)
        if not path.exists():
            break
        files.append(path)
        idx += 1
    if not files:
        raise SystemExit(f"No files found for file prefix '{file_prefix}' with pattern '{file_prefix}_raw_result_*.csv'")
    return files

def read_csv_robust(path: Path) -> pd.DataFrame:
    encodings = ["utf-8", "utf-8-sig", "utf-16", "utf-16le", "utf-16be", "latin1", "cp1252"]
    last_exc = None
    for enc in encodings:
        try:
            df = pd.read_csv(path, dtype=str, keep_default_na=False, na_values=[], encoding=enc)
            print(f"[INFO] Successfully read '{path}' with encoding '{enc}' using default engine.")
            return df
        except Exception as e:
            last_exc = e
            try:
                df = pd.read_csv(path, dtype=str, keep_default_na=False, na_values=[], encoding=enc, engine="python", on_bad_lines="skip")
                print(f"[INFO] Successfully read '{path}' with encoding '{enc}' using python engine and skipping bad lines.")
                return df
            except Exception as e2:
                last_exc = e2
    raise last_exc

def normalize_one_file(path: Path, discipline_label: str | None = None) -> pd.DataFrame:
    # Read with robust CSV reader to preserve all raw values and handle encoding issues
    df = read_csv_robust(path)
    cols = list(df.columns)

    records = []
    discipline = discipline_label if discipline_label is not None else infer_discipline_from_filename(str(path))

    for _, row in df.iterrows():
        # Base MTurk metadata
        meta = {
            "source_file": str(path.name),
            "hit_id": safe_get(row, "HITId"),
            "hit_type_id": safe_get(row, "HITTypeId"),
            "assignment_id": safe_get(row, "AssignmentId"),
            "worker_id": safe_get(row, "WorkerId"),
            "assignment_status": safe_get(row, "AssignmentStatus"),
            "accept_time": safe_get(row, "AcceptTime"),
            "submit_time": safe_get(row, "SubmitTime"),
            "approval_time": safe_get(row, "ApprovalTime"),
            "rejection_time": safe_get(row, "RejectionTime"),
            "work_time_seconds": safe_get(row, "WorkTimeInSeconds"),
            "reward": safe_get(row, "Reward"),
        }

        comment_optional = safe_get(row, "Answer.comment_optional")

        for idx in DEFAULT_ITEM_RANGE:
            # Build per-item field names
            inputs = {k: INPUT_TPL[k].format(idx=idx) for k in INPUT_TPL}

            # Extract values; missing columns yield None
            output_id = safe_get(row, inputs["output_id"])
            output = safe_get(row, inputs["output"])
            prompt_id = safe_get(row, inputs["prompt_id"])
            prompt = safe_get(row, inputs["prompt"])
            alpha = safe_get(row, inputs["alpha"])
            beta = safe_get(row, inputs["beta"])
            mode = safe_get(row, inputs["mode"])
            var = safe_get(row, inputs["var"])
            embedding = safe_get(row, inputs["embedding"])
            range_col = find_annotation_col(cols, idx, discipline)
            annotation_range = safe_get(row, range_col) if range_col else None

            # Skip empty item slots (no output and no output_id)
            if (output_id is None or output_id == "") and (output is None or output == ""):
                continue

            rec = dict(meta)
            rec.update({
                "item_index": idx,
                "prompt_id": prompt_id,
                "prompt": prompt,
                "output_id": output_id,
                "output": output,
                "discipline": discipline,
                "model": "",  # can be filled later if derivable
                "alpha": alpha,
                "beta": beta,
                "mode": mode,
                "var": var,
                "embedding": embedding,
                "annotation_range": annotation_range,
                "comment_optional": comment_optional,
            })
            records.append(rec)

    if not records:
        return pd.DataFrame(columns=NORMALIZED_COLS)

    tidy = pd.DataFrame.from_records(records)
    # Enforce column order
    for col in NORMALIZED_COLS:
        if col not in tidy.columns:
            tidy[col] = np.nan
    tidy = tidy[NORMALIZED_COLS]
    return tidy

def main():
    args = parse_args()
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    print("Select a discipline from the list:")
    for i, d in enumerate(DISCIPLINES):
        print(f"  {i}: {d['menu']}")
    while True:
        choice = input("Enter the number of your choice: ").strip()
        if choice.isdigit():
            choice_idx = int(choice)
            if 0 <= choice_idx < len(DISCIPLINES):
                file_prefix = DISCIPLINES[choice_idx]["file_prefix"]
                discipline_label = DISCIPLINES[choice_idx]["label"]
                break
        print("Invalid choice, please try again.")

    files = load_files_for_discipline(file_prefix)

    frames = []
    for f in files:
        tidy = normalize_one_file(f, discipline_label=discipline_label)
        frames.append(tidy)

    merged = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(columns=NORMALIZED_COLS)

    # Heuristic fill for empty model values
    def infer_model_for_row(row):
        current_model = row["model"]
        if current_model and str(current_model).strip():
            return current_model
        # Try deterministic model_from_output_id first
        model = model_from_output_id(row["output_id"])
        if model:
            return model
        # Fallback to original heuristic
        out_id = row["output_id"]
        model = infer_model_heuristic(str(out_id) if out_id else "")
        if model:
            return model
        # Try source_file
        src = row["source_file"]
        model = infer_model_heuristic(str(src) if src else "")
        if model:
            return model
        # Try output
        out = row["output"]
        model = infer_model_heuristic(str(out) if out else "")
        if model:
            return model
        return current_model

    before_heuristic_missing = merged["model"].isna() | (merged["model"].astype(str).str.len() == 0)
    merged["model"] = merged.apply(infer_model_for_row, axis=1)
    after_heuristic_missing = merged["model"].isna() | (merged["model"].astype(str).str.len() == 0)

    rows_filled_by_heuristic = before_heuristic_missing.sum() - after_heuristic_missing.sum()
    rows_still_missing = after_heuristic_missing.sum()

    # Sort for stability
    merged = merged.sort_values(by=["discipline","hit_id","assignment_id","item_index","output_id"], na_position="last")

    # Write merged CSV
    if args.outfile:
        out_csv = outdir / args.outfile
    else:
        # infer a name from the file_prefix + date-agnostic suffix
        prefix = file_prefix
        out_csv = outdir / f"{prefix}_annotations_merged.csv"

    merged.to_csv(out_csv, index=False, encoding="utf-8-sig")
    print(f"[OK] Wrote merged file: {out_csv}  (rows={len(merged)})")

    print(f"[INFO] Model fill summary: filled by heuristic: {rows_filled_by_heuristic}, still missing: {rows_still_missing}")

if __name__ == "__main__":
    main()
