# How this works

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
