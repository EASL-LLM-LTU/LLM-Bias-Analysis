# Statistical Testing

This folder runs statistical comparisons between models to check for significant bias differences across streams  
(**Gender**, **Power Distance**, **Worldview**, **Bloc Tilt**).

---

## Script

**statistical_testing.py**  
- Uses `finalscores_allstreams.csv` as input (from the visualisation stage).  
- Runs:
  - Kruskal–Wallis tests (overall differences between models)  
  - Pairwise Mann–Whitney U tests (DeepSeek, GPT-4o, GPT-5)  
  - Holm–Bonferroni correction for multiple comparisons  
- Saves 5 CSV result files in the output directory.

---

## Outputs

| File | Purpose |
|------|----------|
| `overall_kruskal_summary.csv` | Overall test results for each stream |
| `posthoc_pairwise_holm_*.csv` | Pairwise comparisons for each bias stream |

---

## Example Use

```bash
pip install pandas numpy scipy
python statistical_testing.py
```