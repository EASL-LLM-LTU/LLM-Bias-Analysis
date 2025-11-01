# Outputs

Collected model responses for each bias stream.

This folder contains: 
- *_raw.csv — full sets (≈270 outputs per stream).
- *_30_raw.csv — trial subsets (30 outputs) for dry runs / smoke tests.
- output_collection.mp4 — short screencast showing the collection workflow.

## Files

- Bloc Tilt: [bloctilt_raw.csv](./bloctilt_raw.csv), [bloctilt_30_raw.csv](./bloctilt_30_raw.csv)
- Gender: [gender_raw.csv](./gender_raw.csv), [gender_30_raw.csv](./gender_30_raw.csv)
- Power Distance: [powerdistance_raw.csv](./powerdistance_raw.csv), [powerdistance_30_raw.csv](./powerdistance_30_raw.csv)
- Worldview: [worldview_raw.csv](./worldview_raw.csv), [worldview_30_raw.csv](./worldview_30_raw.csv)
- Demo: [output_collection.mp4](./output_collection.mp4)

Prompts live in ../prompts (see: [README](../1.prompts/README.md), [prompt_template.md](../1.prompts/prompt_template.md), [prompts_guardrails_and_scoring.md](../1.prompts/prompts_guardrails_and_scoring.md)).

## CSV schema

Columns required in every outputs CSV (order recommended):
output_id, output, prompt_id, prompt, model

- output_id — unique per (prompt × model), e.g., for a Gender Bias prompt G-001 using GPT-4o: G4o-001
- output — the model’s response (single short sentence in our setup)
- prompt_id — stable ID from the prompts CSV (e.g., G-001)
- prompt — the exact prompt string used
- model — model name/label (e.g., gpt-4o, deepseek)

CSV tips: If any text contains commas or quotes, wrap the field in quotes and escape quotes as "". Save as UTF-8 (no BOM). One response per row.

## Why two sizes (30 vs 270)?

- 30 — fast trial runs to validate pipeline steps, schemas, and HIT setup.
- 270 — full evaluation set per stream used for EASL selection and analysis.

## Collection workflow (concise)

1) Prepare a sheet with columns: prompt_id, prompt, model, output_id, output.  
2) Use a clean profile/session for the LLM (new account or memory off).  
3) Prime once per chat with the base instruction from ../prompts/prompt_template.md.  
4) Send exactly one prompt per fresh chat; if the reply is meta (e.g., “I will write…”), resend.  
5) Copy the response into the output column; fill model and output_id.  
6) Start a new chat for the next prompt.  
7) Export to CSV when done (UTF-8).  
Video walkthrough: open output_collection.mp4 in this folder.

## Naming conventions

- Full sets: {stream}_raw.csv  → e.g., gender_raw.csv  
- Trial sets: {stream}_30_raw.csv  → e.g., powerdistance_30_raw.csv  
Streams: gender | worldview | powerdistance | bloctilt

## Quality checks (before commit)

- prompt_id exists in the matching prompts CSV.  
- prompt text matches that prompt_id (no drift).  
- output_id is unique per (prompt × model).  
- No multi-line cells unless quoted (CSV-safe).  
- Files open cleanly in Excel and with pandas (pd.read_csv).

## Making an EASL-ready merge CSV

If outputs and prompts were collected separately, create a single CSV with columns:
output_id, output, prompt_id, prompt

Join on prompt_id (Excel XLOOKUP or a pandas merge), verify row counts, and spot-check a few records. Save as {stream}_raw.csv for the full set or {stream}_30_raw.csv for the subset.

## Do / Don’t

Do:
- One prompt per fresh chat (prevents context bleed).  
- Keep the base instruction consistent across models.  
- Use the 30-row subsets for dry runs and CI sanity checks.

Don’t:
- Mass-paste many prompts in one chat (changes model behaviour).  
- Use a personal profile with memory/history that could bias outputs.
