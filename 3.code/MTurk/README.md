# MTurk Integration

This folder contains all files and instructional materials required to create, upload, and manage Human Intelligence Tasks (HITs) on **Amazon Mechanical Turk (MTurk)** for bias annotation within the **Ctrl-BIAS EASL** pipeline.

It documents how to:
1. Prepare and upload HITs using MTurk Requesters,  
2. Build and customise HTML task templates for consistent layout and rating scales,  
3. Use the Excel/CSV workaround when MTurk is unavailable, and  
4. Manage qualifications for worker access.

---

## Folder Structure

| File / Folder | Description |
|----------------|-------------|
| **1.MTurkRequester-Setup.mp4** | Video walkthrough for setting up a Requester account. |
| **2.MTurk-HIT-Template.mp4** | Demonstrates how to create a reusable HIT Template **on MTurk** using HTML scripts from `MTurk_HTML_templates/`. |
| **MTurk_HTML_templates/** | Contains the HTML source files for bias-rating tasks (Gender, Worldview, Power Distance, Bloc Tilt). Each template defines the page layout, 1–5 rating scales, and attention checks. |
| **MTurk_addQualifications.py** | Script for assigning, checking, or removing custom MTurk qualifications to control who can access the HITs. |
| **MTurk_workaround/** | Offline fallback for annotation when MTurk servers are down — includes Excel (.xlsx) equivalents and guidance for manual rating. |

---

## How MTurk Fits into the EASL Workflow

The MTurk process sits between the **Generate** and **Update** stages of the EASL cycle.

```text
initialize → generate → [upload to MTurk → annotate → download] → update → repeat
```
---

## Set Up MTurk Requester Account

Use **1.MTurkRequester-Setup.mp4** as a visual guide.

It covers:
- Creating and verifying a Requester account  

**Watch:** [1.MTurkRequester-Setup.mp4](./1.MTurkRequester-Setup.mp4)

---

## Create and Customise HIT Templates

Use **2.MTurk-HIT-Template.mp4** to learn how to build the HTML template that displays your tasks.

This tutorial demonstrates:
- Opening the MTurk **HTML Question Editor**  
- Copy-pasting the correct HTML from `MTurk_HTML_templates/`  
- Ensuring each column from your CSV correctly maps to the displayed text and rating inputs  
- Previewing the interface to verify the 1–5 scale and prompt text formatting  
- Saving your template for reuse across bias streams  

Each HTML file (Gender, Power Distance, Worldview, Bloc Tilt) defines:
- A consistent layout for readability  
- A 1–5 rating scale for bias severity or direction  
- Guardrails and attention checks to maintain rater quality  

**Watch:** [2.MTurk-HIT-Template.mp4](./2.MTurk-HIT-Template.mp4)

---

## Launch the HITs

1. Log into the [MTurk Requester portal](https://requester.mturk.com).  
2. Go to **Create → New Project
3. Choose your saved template.  
4. Attach the generated CSV (`*_hit_1.csv`).  
5. Configure:
   - **Reward per HIT**  
   - **Number of assignments** (e.g., 2 raters per batch)  
   - **Time limit** and **auto-approval delay**  
6. Preview and launch the task.  

Once deployed, each HIT will appear to qualified workers with the correct bias-rating scale.

---

## Manage Qualifications (Optional)

Use the helper script to restrict tasks to specific worker groups.

```bash
python MTurk_addQualifications.py --add --qualification "CtrlBIAS"
```
## Retrieve and Integrate Results

When all assignments are completed:

1. **Download** the results CSV from the Requester portal.  
2. **Rename** it following the pattern:  gender_raw_result_1.csv
3. **Move** it into your dataset directory.  
4. **Fold** ratings back into the EASL model:

```bash
python main.py --operation update --model gender_raw_0.csv
```
This updates the posterior parameters (alpha, beta, mode, var) and produces gender_raw_1.csv.
Repeat the generate → upload → annotate → update loop until convergence.

---

## Workaround (Offline or MTurk Downtime)

If MTurk is unavailable, use the files in `MTurk_workaround/` to prepare and process ratings manually in Excel.

### Files

- **Master_Worksheet.xlsx** – main file with HITs (5 outputs per row)  
- **load_hits.py** – prepares annotation sheets from the master file  
- **autofit_sheets.py** – formats Excel sheets for readability  
- **resultstocsv.py** – combines all completed sheets into one CSV for EASL updates  

### Steps

1. Run these commands to create annotator sheets:
   ```bash
   python load_hits.py
   python autofit_sheets.py
   ```
2. Annotators open the generated Excel files and enter 1–5 ratings beside each output.

3. When done, collect the annotated file in the same folder.

4. Run:
```
python resultstocsv.py
```
This Produces a file such as gender_raw_result_1.csv

5. Feed the results back into EASL:
```
python main.py --operation update --model gender_raw_0.csv
```

---

## Further Video Walkthroughs

| Step | Description | Link |
|------|--------------|------|
| **3. Initialize & Generate HITs** | Demonstrates how to initialise a dataset, generate HIT CSVs, and prepare them for MTurk upload. | Watch on SharePoint](https://latrobeuni-my.sharepoint.com/:v:/g/personal/21702717_students_ltu_edu_au/EfNyv130khxAu6HY2DLojEUB4W2-2leEaf1I9s0n1NentQ?e=yFaN0t) |
| **4. Collect Ratings, Update, and Generate New HITs** | Shows how to download annotated results, update the dataset, and regenerate new HITs for further refinement. | [Watch on SharePoint](https://latrobeuni-my.sharepoint.com/:v:/r/personal/21702717_students_ltu_edu_au/Documents/Microsoft%20Teams%20Chat%20Files/4.CollectRatings-Update-NewHITs.mp4?csf=1&web=1&e=mqgYJx) |

---
