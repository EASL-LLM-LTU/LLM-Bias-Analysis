Let's get testing soon!
We need an end-to-end EASL + MTurk test run.  
Let's make sure we're on the same page.
The aim is to keep things simple, validate the pipeline, and identify issues before scaling up.  

# End-to-End Testing Prep

---

## CLARITY ITEM 1: Stopping Rule: MANUAL STOPPING

- Decision: No hard-coded stop in the code.  
- We will use an in-memory counter per stream:  
  - After each update (e.g., `9 HITs × 6 items = 54 ratings`), increment a counter.  
  - Print cumulative total per stream at the end of the run.  
  - Stop generating HITs once we reach **540 ratings per stream** (≈2 per item).  

1. After each update (e.g. processing a batch of `9 HITs × 6 items = 54 ratings`), increment a simple counter for that stream:  
   `ratings_count += 54`

2. At the end of each run, print the cumulative total for that stream. Example:  
   `[Update] 54 new ratings applied. Stream total = 324 / 540`

3. Once the counter reaches 540 per stream, we manually stop generating further HITs.

This approach keeps the cap at the project level (managed by us),  not as a strict enforcement in the code. It avoids complicating the pipeline  while still ensuring we don’t overshoot the annotation budget.


---

## CLARITY ITEM 2: HIT Design: 1x6 ONLY

- Current implementation supports the 1×6 layout (default `--item 6`) and the later-round selection logic (variance + optional embedding similarity).
- We do not enforce Round-1 grouping by `prompt_id` (i.e., 2 prompts × 3 outputs). Iteration 0 still builds random 1×6 groups.
- We **do not** implement prompt grouping (2×3):
- Technically, 2×3 grouping could be achieved by modifying `getNextK(iterNum==0)` to chunk items by `prompt_id` (ensuring three outputs per prompt, then pairing two prompts together), but after further investigation, grouping outputs by `prompt_id` risks bias.  
  - After beginning to look into grouping prompts and reviewing our actual data to check out the output_ids, I noticed high similarity between outputs across models (e.g., some GPT-4o and GPT-5 can produce near-identical phrasings).  .  
    - Example:  
      - *“Constant scrutiny is the only thing keeping the corrupt in check.”*  
      - *“Blind trust in power breeds stagnation, not progress.”*  
      - *“Blind trust breeds disasters; accountability accelerates real progress.”*  
  - If such near-duplicates from different models are surfaced together, annotators may unconsciously penalise or reward a model unfairly. For instance, the temptation may be, _"Oh it's easy to see which ones DeepSeek, and we want to report a finding thats interesting, so I'll mark DeepSeek as having more bias"_ 
- Recommendation: Keep it simple with randomised 1×6 HITs for all rounds.  
  - Maximises coverage.  
  - Avoids introducing annotator bias.  

---

## CLARITY ITEM 3: Batch Sizing

I have already partitioned our outputs into separate .csvs

Sample runs: 30 outputs per stream
Main runs: 270 outputs per stream

<img width="1361" height="503" alt="image" src="https://github.com/user-attachments/assets/46625a97-bc0c-49b3-a0ee-6f42468cb53b" />


### Test Run: --hits 5 for each stream.
- There are only 30 items per stream.
- 5 HITs x 6 items = 30.

### Full Run: 3 lots of --hits 15 for the first round; 5 lots of --hits 9 for subsequent

- **Iteration 0** 3 lots of `--hits 15` → 45 HITs × 6 = 270 annotations.  
  - Ensures every item is rated once.  
- **Beyond** 5 lots of `--hits 9` → 45 HITs × 6 = 270 annotations.  
  - ≈5 model updates per stream.  

---

## CLARITY ITEM #4: EASL Annotation Workflow

### How scores map bac
- **HIT CSV** (e.g., `gender_raw_hit_1.csv`) provides `Input.output_id1..6` (and prompts/outputs).
- **HTML form** needs prompt text and output text and ability to rate these.
- When you **download MTurk results**, the CSV includes:
  - `Input.output_id1..6` (the items shown in that HIT row)
  - `Answer.range1..6` (the scores the worker entered)
- Save that file as `<stream>_result_<round>.csv` (e.g., `gender_raw_result_1.csv`).
- Run:  
  ```bash
  python driver.py --operation update --model gender_raw_0.csv

- Reads gender_raw_result_1.csv
- Matches Input.output_id{i} → model rows
- Updates α/β/mode/var
- Writes gender_raw_1.csv
- Next round:
  - Generate from gender_raw_1.csv → gender_raw_hit_2.csv
  - Collect results → gender_raw_result_2.csv
  - Update → gender_raw_2.csv
Because you don’t start the next round until the last one is finished, the filename convention alone guarantees “which round it belongs to.”

---


## CLARITY ITEM #5: HOW WORKERS CAN BE ASSIGNED / ITERATION PLAN

### Assignment for SAMPLE RUN – HELD-OUT PILOT

- Each stream: **30 outputs = 5 HITs × 6 items/HIT**  
- Balanced across the three of us keeps it simple for the pilot.


| Stream              | Hooman | Matt | Ethan |
|---------------------|--------|------|-------|
| **Gender bias**     | 5 HITs| 0 | 0 |
| **Worldview bias**  | 0  | 5 HITs | 0 |
| **Bloc-tilt bias**  | 0 | 0  | 5 HITs|
| **Power-distance**  | 0 | 5 HITs | 0 |

- We can then have the others three group members annotate each stream in the pilot so that we don't have raters rating the same items again for the subsequent round. Let's make sure it works before getting there though.

| Stream              | Sumeyye | Li Yin | Tessa |
|---------------------|--------|------|-------|
| **Gender bias**     | 5 HITs | 0 | 0 |
| **Worldview bias**  | 0  | 0 | 5 HITs|
| **Bloc-tilt bias**  | 5 HITs | 0  | 0|
| **Power-distance**  | 0 | 5 HITs| 0 |

---

### Assignment for FULL RUN / Iteration Plan

- Each annotator: **15 HITs × 6 items/HIT = 90 annotations per stream per run**  
- Total per run: 270 annotations (3 annotators × 90)  
- After Round 1, streams will be rotated so each annotator cover two domains. This will also ensure that items are rated by at least two different people rather than rated by the same person over and over again.
- Simpler solution than hard-coding to avoid worker_id duplication.


#### Iteration 0 — 15 HITs each (initial full pass)

| Stream              | Worker 1<br>(Sumeyye) | Worker 2<br>(Tessa) | Worker 3<br>(Hugo) | Worker 4<br>(Li Yin) | Worker 5<br>(Matt) | Worker 6<br>(Ethan) |
|---------------------|-----------------------|---------------------|--------------------|----------------------|--------------------|---------------------|
| **Gender bias**     | 15 HITs               | 15 HITs             | 15 HITs            | –                    | –                  | –                   |
| **Worldview bias**  | 15 HITs               | 15 HITs             | 15 HITs            | –                    | –                  | –                   |
| **Bloc-tilt bias**  | –                     | –                   | –                  | 15 HITs              | 15 HITs            | 15 HITs             |
| **Power-distance**  | –                     | –                   | –                  | 15 HITs              | 15 HITs            | 15 HITs             |



#### Iteration 1 — 9-HIT update blocks (with update after each block)

| Stream              | Worker 1<br>(Sumeyye) | Worker 2<br>(Tessa) | Worker 3<br>(Hugo) | Worker 4<br>(Li Yin) | Worker 5<br>(Matt) | Worker 6<br>(Ethan) |
|---------------------|-----------------------|---------------------|--------------------|----------------------|--------------------|---------------------|
| **Gender bias**     | –                     | –                   | –                  | 2 × 9 HITs          | 2 × 9 HITs        | 1 × 9 HITs         |
| **Worldview bias**  | –                     | –                   | –                  | 2 × 9 HITs          | 1 × 9 HITs        | 2 × 9 HITs         |
| **Bloc-tilt bias**  | 2 × 9 HITs           | 2 × 9 HITs         | 1 × 9 HITs        | –                    | –                  | –                   |
| **Power-distance**  | 2 × 9 HITs           | 1 × 9 HITs         | 2 × 9 HITs        | –                    | –                  | –                   |

### Iteration 1 Rhythm (per stream)

1. Generate HITs from `<stream>_1.csv` → `<stream>_hit_2.csv`.
2. Assign **first 9 HITs** to the designated worker; they complete them.
3. Download MTurk results → save as `<stream>_result_2.csv`.
4. Update model:
   ```bash
   python driver.py --operation update --model <stream>_1.csv
→ writes <stream>_2.csv.
5. Generate next 9 from the updated model, assign to the next worker, repeat.

This loop enforces: annotate → download → update → regenerate.
You never start the next chunk until the current chunk is applied, which is required for adaptive selection.

---

## PREPARATION FOR END-TO-END TESTING: QUESTIONS

**Ethan:**
  - Can your MTurk pages ingest the HIT CSVs to give the annotator 6 outputs to rate (with prompt text + output text visible per item)?
  - Can your MTurk ensure that all output IDs in each HIT csv are rated?  
  - Can your MTurk pages output annotator ratings back to a CSV?
<img width="1153" height="30" alt="image" src="https://github.com/user-attachments/assets/8517519f-74be-468a-b8f6-434a496fa323" />

  - What extra fields does MTurk add automatically to the output file? YOu mentioned this output file is not able to be edited, so what will it look like?  
    - Is `worker_id` included? (If yes, we could use it to track overlaps.)
  - Confirm MTurk ingestion/output works end-to-end.

**Hooman:**
   - If the MTurk pages cannot output a .csv file in our expected format, how can we edit our code to parse only the fields that are relevant to our updates

**General direction:**

**Step 1.** Let's make the required adjustments

**Step 2.** Let's run Round 0 of our **SAMPLE RUN - HELD OUT STREAM** with above info in mind, before the Sprint ends

**Step 3.** Should all go successfully, we can allocate the next round of HITs to the other 3 group members (to annotate the _held-out sample_ items after us).

**Step 4.**- Should all go successfully in the previous steps, we can then look to annotating the _main_ sets using the rotations in mind.



