# Statistical Foundations of EASL for Ctrl Bias
*EASL with pragmatic stopping, 1×6 HITs, and a lightweight validation plan.*

---

## Context
Sakaguchi & Van Durme use EASL to model each item’s latent score on **[0,1]** with a **Beta** distribution. EASL combines the efficiency of online ranking methods with the interpretability of direct assessment while enforcing bounded support.  

<details>
<summary><strong>Why the Beta distribution</strong></summary>
Sakaguchi & Van Durme explained that humans rate more efficiently when comparing paired items. However, they identified a key issue in the Pairwise Ranking model. They found that modelling scores with a normal distribution in pairwise ranking leaks probability mass outside [0,1].For human ratings bounded in [0,1], this means the model assigns non-zero probability to impossible scores (e.g., –0.2 or 1.3). This “leakage” results in inefficient use of annotations, since the model spreads mass where ratings can never exist.  By contrast, the Beta distribution is naturally bounded in [0,1], ensuring all probability mass stays inside the meaningful range while flexibly modeling uniform, skewed, or peaked shapes.
To address this, they proposed using the Beta distribution for bounded scalar labels. They then advanced further by introducing EASL where items can be directly annotated, and similar items (based on mode estimates) can be surfaced to maximise efficiency. This creates a hybrid approach combining the structure of ranking with the efficiency of scalar annotation.  
</details>

After running experiments comparing EASL to Direct Annotation, they report:  

> “In the commonly employed condition of 3-way redundant annotation, our approach on multiple tasks gives similar quality with just 2-way redundancy; this translates to a potential 50% increase in dataset size for the same cost.” (p. 2)

<details>
<summary><strong>Why this quote is important</strong></summary>

This quote is important for our approach. Firstly, because it indicates that 3-way redundancy (3 annotations per item) is a common approach in Direct Assessment (DA) and is therefore generally accepted. Secondly, Sakaguchi & Van Durme (2018) show that EASL typically achieves similar quality with ~2 annotations per item on average by allocating labels to high-uncertainty items. This will be used to defend our approach. More to come on that below.

</details>


Below are challenges or foundational issues that need addressing and to be defined for our project.

---

## 1. Confirm and document the rating update rule (Likert 1–5 → [0,1])

<details>
<summary><strong>Option A — Slider (continuous)</strong></summary>

Han et al. (2024) highlight several advantages of sliders for scalar annotation:

- Finer granularity: Sliders let annotators express subtle distinctions (e.g., 0.63 vs 0.68) rather than being forced into a discrete bucket.  
- Less clumping: Likert-style categories create artificial jumps (3 → 4), which can mask nuanced variation in judgments. Sliders smooth this out.  
- Annotator preference: In user studies, sliders are often reported as more natural for rating subjective attributes.  
- Compatibility with ranking: Continuous scores can later be transformed into pairwise preferences more easily.  

The main drawback is implementation complexity: we would need new UI, decide on resolution (e.g., 0.01 increments?), and adapt our update rules.

</details>

<details>
<summary><strong>Option B — Likert 1–5 (defensible, simple)</strong></summary>

- Simple, already supported by our current annotation interface.  
- Defensible: 1–5 Likert is widely used in human evaluation research.  
- Easy to integrate with EASL by mapping to [0,1]:  

$\[
s = \frac{r-1}{4} \quad \in \{0, 0.25, 0.5, 0.75, 1\}
\]$

This avoids scope creep while keeping results interpretable.

</details>

**Recommendation**: Keep Likert 1–5 now. The mapping is simple, compatible with EASL, and avoids scope creep. Map ratings to \([0,1]\) via:  

$$\
s = \frac{r-1}{4}
\$$

where $s$ is score [0,1] and $r$ is rating [1,5].

This will map 1→0, 2→0.25, 3→0.5, 4→0.75, 5→1.

---

## 2. Beta distribution math & how annotations update items

EASL parameterizes each item \(i\) as:

$$ S_i \sim \mathrm{Beta}(\alpha_i,\beta_i), \quad
\mu_i=\frac{\alpha_i}{\alpha_i+\beta_i}, \quad
\mathrm{Var}[S_i]=\frac{\alpha_i\beta_i}{(\alpha_i+\beta_i)^2(\alpha_i+\beta_i+1)}\$$

If $\(\alpha_i,\beta_i>1\)$, the mode is:

$$\mathrm{mode}(S_i)=\frac{\alpha_i-1}{\alpha_i+\beta_i-2}\$$

<details>
<summary><strong>Note on variance shrinkage</strong></summary>

The variance of a Beta distribution is:

$$\mathrm{Var}[S] = \frac{\alpha \beta}{(\alpha + \beta)^2 (\alpha + \beta + 1)}\$$

As more ratings are added:
- The numerator $\(\alpha \beta\)$ grows roughly linearly.  
- The denominator $(\alpha + \beta)^2(\alpha + \beta + 1)\$ grows much faster (quadratically and beyond).  

Because the denominator grows faster than the numerator, the variance always shrinks with more annotations.  

This explains why in all of the tables below, variance decreases steadily as \(n\) increases, with shrinkage being faster at the edges (all 1s or 5s) and slower near the center (all 3s).
</details>

<details>
<summary><strong>Mean and mode in our project</strong></summary>

Sakaguchi & Van Durme (2018) found that the mode works better than the mean for *active selection* because the mean is always biased toward 0.5 (neutral), while the mode more sharply reflects the most likely value.  

Other than for active selection, we will use the mean ($\mu_i\$) instead of the mode because:  
- The mean is always defined, even when $\(\alpha\)$ or $\(\beta\) ≤ 1$ (where the mode may not exist).  
- It’s easier to interpret when presenting how parameters evolve with small numbers of ratings.  
- It still illustrates the key point: variance shrinks faster at the edges and slower near neutral.  

For actual EASL item selection, the mode is used.  Empirically, they found the mode produced more efficient and accurate updates for scalar annotations.
</details>

Some examples of how ratings would update scores are shown below. These will be important later when discussing stopping rules.
<details>
<summary><strong>All 1s (s=0)</strong></summary>

| n    | α   | β   | $\mu\$ | Var    |
|:-----|----:|----:|----------:|-------:|
| init | 1.00 | 1.00 | 0.5000   | 0.0833 |
| 1    | 1.00 | 2.00 | 0.3333   | 0.0556 |
| 2    | 1.00 | 3.00 | 0.2500   | 0.0375 |
| 3    | 1.00 | 4.00 | 0.2000   | 0.0267 |
| 4    | 1.00 | 5.00 | 0.1667   | 0.0198 |
| 5    | 1.00 | 6.00 | 0.1429   | 0.0153 |

</details>

<details>
<summary><strong>All 2s (s=0.25)</strong></summary>

| n    | α   | β   | $\mu\$ | Var    |
|:-----|----:|----:|----------:|-------:|
| init | 1.00 | 1.00 | 0.5000   | 0.0833 |
| 1    | 1.25 | 1.75 | 0.4167   | 0.0608 |
| 2    | 1.50 | 2.50 | 0.3750   | 0.0469 |
| 3    | 1.75 | 3.25 | 0.3500   | 0.0379 |
| 4    | 2.00 | 4.00 | 0.3333   | 0.0317 |
| 5    | 2.25 | 4.75 | 0.3214   | 0.0273 |

</details>

<details>
<summary><strong>All 3s (s=0.5)</strong></summary>

| n    | α   | β   | $\mu\$ | Var    |
|:-----|----:|----:|----------:|-------:|
| init | 1.00 | 1.00 | 0.5000   | 0.0833 |
| 1    | 1.50 | 1.50 | 0.5000   | 0.0625 |
| 2    | 2.00 | 2.00 | 0.5000   | 0.0500 |
| 3    | 2.50 | 2.50 | 0.5000   | 0.0417 |
| 4    | 3.00 | 3.00 | 0.5000   | 0.0357 |
| 5    | 3.50 | 3.50 | 0.5000   | 0.0313 |

</details>

<details>
<summary><strong>All 4s (s=0.75)</strong></summary>

| n    | α   | β   | $\mu\$ | Var    |
|:-----|----:|----:|----------:|-------:|
| init | 1.00 | 1.00 | 0.5000   | 0.0833 |
| 1    | 1.75 | 1.25 | 0.5833   | 0.0608 |
| 2    | 2.50 | 1.50 | 0.6250   | 0.0469 |
| 3    | 3.25 | 1.75 | 0.6500   | 0.0379 |
| 4    | 4.00 | 2.00 | 0.6667   | 0.0317 |
| 5    | 4.75 | 2.25 | 0.6786   | 0.0273 |

</details>

<details>
<summary><strong>All 5s (s=1)</strong></summary>

| n    | α   | β   | $\mu\$ | Var    |
|:-----|----:|----:|----------:|-------:|
| init | 1.00 | 1.00 | 0.5000   | 0.0833 |
| 1    | 2.00 | 1.00 | 0.6667   | 0.0556 |
| 2    | 3.00 | 1.00 | 0.7500   | 0.0375 |
| 3    | 4.00 | 1.00 | 0.8000   | 0.0267 |
| 4    | 5.00 | 1.00 | 0.8333   | 0.0198 |
| 5    | 6.00 | 1.00 | 0.8571   | 0.0153 |

</details>

<details>
<summary><strong>Examples</strong></summary>

| Ratings | α   | β   | $\mu\$ | Var    |
|:--------|----:|----:|----------:|-------:|
| 4 (0.75), 5 (1.0) | 2.75 | 1.25 | 0.6875 | 0.0430 |
| 4 (0.75), 3 (0.5) | 2.25 | 1.75 | 0.5625 | 0.0492 |
| 3 (0.5), 2 (0.25) | 1.75 | 2.25 | 0.4375 | 0.0492 |
| 1 (0), 2 (0.25)   | 1.25 | 2.75 | 0.3125 | 0.0430 |
| 1 (0), 3 (0.5)    | 1.50 | 2.50 | 0.3750 | 0.0469 |
| 2 (0.25), 4 (0.75)| 2.00 | 2.00 | 0.5000 | 0.0500 |
| 1 (0), 5 (1.0)    | 2.00 | 2.00 | 0.5000 | 0.0500 |

</details>

**Recommendation:** Initialise $\(\alpha_i=\beta_i=1\)$.  Each update will contain a score $\(s \in \{0,.25,.5,.75,1\}\)$. This score will be used to update $\alpha_i\$ and $\beta_i\$ as follows:

$$\\alpha_i \leftarrow \alpha_i + s, \qquad
\beta_i \leftarrow \beta_i + (1-s).
\$$

---

## 3. Defining stopping criteria

<details>
<summary><strong>Option 1: Stop by 95% confidence intervals</strong></summary>

- Conceptually clean: require 95% CIs to fall entirely within a bin to know, for example, that a 3 is truly a 3.  
- Example: for a neutral “3” (0.5), the bin is [0.375, 0.625] (width 0.25).  
- Using the CI formula (≈ 2 × 1.96 × √Var), we’d need variance ≤ 0.004 to fit.  
- This implies ~60 annotations per item for neutral scores.  
- Scaling up: 60 × 300 outputs × 4 streams = 72,000 labels.  
- Problem: far too conservative and infeasible for our budget.  

</details>

<details>
<summary><strong>Option 2: Posterior bin probabilities</strong></summary>

- Stop when posterior places high probability mass (e.g. 80%) inside the bin.  
- Example thresholds:  
  - Edge bins (1s or 5s): ~10–12 annotations to reach 80%.  
  - Middle bin (3s): ~20–24 annotations to reach 80%.  
- Scaling up: thousands of extra labels required.  
- Problem: still too demanding for practical use.  

</details>

<details>
<summary><strong>Option 3: Variance threshold</strong></summary>

- Stop once variance drops below some fixed τ (e.g. τ = 0.03).  
- Variance always shrinks with more labels, but:  
  - Shrinks slower in the middle (3s).  
  - Shrinks faster at the edges (1s, 5s).  
- Problem: threshold τ would be arbitrary, not grounded in literature, and leads to inconsistent stopping across items.  

</details>

<details>
<summary><strong>Option 4: Redundancy cap (practical, recommended)</strong></summary>

- This is what Sakaguchi & Van Durme (2018) themselves did.  
- Allow variance/uncertainty to guide which items get resurfaced.  
- But stop after a fixed cap of 2–3 annotations per item.  
- This avoids waiting for variance to shrink to an unrealistic level.  
- Budget-friendly and proven effective.  

</details>

### Recommendation

Remember: Sakaguchi noted that 3-way redundancy is common in Direct Assessment (DA), and they showed EASL with ~2-way redundancy can achieve similar quality.  I therefore propose:  
- Redundancy cap at 2 annotations per item.  
- For 270 outputs × 4 streams, that’s 540 per stream (~2,160 total). It sounds like a lot, but its 360 HTML pages. Feasible.  
- Variance/uncertainty will still guide resurfacing of items within those 540, but stopping is based on the cap, not variance.  
- We will still report variance afterwards as a diagnostic, but not use it to decide when to stop.  

---

## 4. HIT design (2×3 vs 1×6)

<details>
<summary><strong>Option A: 2×3 (one prompt + three model outputs)</strong></summary>

Why we liked it initially
- Shared context: Annotators compare responses to the *same prompt*, which simplifies bias judgments.
- Easy mental model: “One prompt, three answers” is intuitive and fast to read.
- Good for Round-1 triage: Quickly spots obviously extreme or problematic outputs.

Why it becomes problematic later
- Redundancy: If a *single* output for a prompt is high-variance, 2×3 will keep surfacing its two low-variance neighbors from the same prompt — burning labels where uncertainty is already low.
- Coupled uncertainty: Selection is constrained by prompt, not by item-level uncertainty. You pay a “prompt tax”: two extra labels often go to items that don’t need them.
- Semantic matching is redundant: Because the three items already share a prompt, additional embedding-based grouping gives little marginal benefit.
</details>

<details>
<summary><strong>Option B: 1×6 (six items per HIT)</strong></summary>

Why it’s better overall
- Flexibility: Lets you mix items so that each HIT includes *more* high-uncertainty items, improving label efficiency.
- Still keep context: You can structure 1×6 as 2 prompts × 3 outputs each — you retain prompt coherence *and* gain pairing freedom.
- Fewer forced re-annotations: You’re not obliged to bring the same low-variance neighbors along every time a single item is uncertain.

How to structure
- Round-1: Use 1×6 as (Prompt A: 3 outputs) + (Prompt B: 3 outputs) — preserves context while covering more prompts per page.
- Later rounds: Keep the 2×3 layout *when it helps annotators compare across models for a given prompt*, otherwise feel free to mix prompts if it increases the count of high-variance items per HIT.
</details>

### Recommendation
- Use 1×6, composed as 2 prompts × 3 outputs in Round-1 (best balance of context and efficiency).  
- Group items by their `prompt_id` in Round 1 so that all outputs from the same prompt can be surfaced together. This ensures annotators always see matched responses side by side when needed.  
- In Round 2, continue with 1×6 but prioritise packing each HIT with as many high-variance items as possible.
- In summary, keep the 2×3 sub-structure (via `prompt_id` grouping) when it aids comparability; relax it when it causes redundancy.

---

## 5. Selecting / pairing items within HITs (Match-Quality Function)

Remember, part of the great thing about EASL is its match-quality function to decide which items to surface together so annotators can make comparative judgments.  

In the bounded EASL variant, for match-selection, the mode \(M\) of each Beta posterior is used instead of the mean by Sakaguchi & Van Durme:

$$\
q(\gamma,S_i,S_j)=\sqrt{\tfrac{2\gamma^2}{c^2}}\,
\exp\\Big(-\tfrac{(M_i-M_j)^2}{2c^2}\Big).
\$$

Here:
- $M_i$, $M_j$: modes of items $i$ and $j$.  
- $c$: scale parameter (tunes how strict similarity matching is).  
- $\gamma$: controls variance sensitivity (higher $\gamma$ = more emphasis on uncertainty).  

The question is, do we also want to surface outputs based on their semantic similarity?

<details>
<summary><strong>Option A: Scalar-only</strong></summary>

- Mechanics: Pair items based only on scalar stats (their Beta posteriors).  
- Items with high variance are preferentially matched with others of similar mode values.  
- This ensures annotators see comparisons that are meaningful: e.g., two outputs both likely “3”s, but one is uncertain. Raters can sharpen the estimate.  

Benefits:
- Mathematically faithful: Uses the same formulation as Sakaguchi & Van Durme.  
- Variance-driven efficiency: EASL targets exactly those items where extra ratings reduce uncertainty fastest.  
- Clarity: Grouping by `prompt_id` ensures outputs for the same prompt are judged side by side, which preserves context and avoids semantic mismatches in Round 1.
- Simplicity: Keeps implementation aligned with prior work and avoids introducing new parameters.  

</details>

<details>
<summary><strong>Option B: Blend scalar match-quality with embeddings</strong></summary>

Potential benefits:
- Semantic grouping: Ensures annotators compare outputs that are not only numerically similar but also semantically related.
- More nuanced comparisons: May help distinguish subtle biases if surface wording differs but meaning is close.  
- First-round utility: Could be used in Round-1 to cluster similar outputs when scalar stats are not yet stable.

</details>.

---

## 6. How do we evaluate performance?

<details>
<summary><strong>Compare the 3 models (substantive)</strong></summary>

Goal: See which LLM/LMM shows more/less bias.

- Compute per-model pooled Beta modes with CIs.

Why useful:
- Tells us which model is more biased.  
- Non-overlapping CIs = strong evidence of difference.
- Can discuss performance of our solution more vaguely without extra direct annotation.
- Sakaguchi & Van Durme have already validated that EASL outperforms DA, so we don't need to run another study on its efficiency.
</details>


---

## 7. Batch sizing & rounds

- **Per stream:** 90 prompts × 3 outputs = 270 items.  
- **HITs:** 6 items/HIT → 45 HITs per round.  
- **Budget:** 540 labels/stream → ≈2 rounds (90 HITs).
- **# HITs before updates:** Across 90 HITs, aim for 8-10 updates, so update after 5 HITs (after 30 items are rated)  
- **All streams:** 4 × 540 = 2,160 labels (≈360 HITs).

---

## 8. Quality checks (budget-friendly)


Because annotation is done by our 6-person team, we keep QA lean and transparent:

- Unique annotators: Every rating is tied to a `worker_id`. We avoid duplicate ratings on the same item where possible. To be coded in.  
- Timing floor: HITs completed *unrealistically fast* (e.g., <15s for 6 items) are flagged for review.  
- Audit log: For every update, we log `(alpha, beta, mode, variance, worker_id, hit_id, timestamp)` to enable traceability.  

### Why this is sufficient
- Worker IDs let us later compute inter-rater agreement (IRA) on overlapping items. Even without a gold set, IRA tells us whether annotators apply the bias scale consistently.  
- Speed checks catch careless labeling. Combined with IRA, this balances process quality (workers aren’t rushing) with content quality (workers broadly agree).  
- Audit logging guarantees reproducibility: we can always reconstruct how a score was built.

<details>
<summary><strong>Other QA options that could be considered (but are likely not in scope)</strong></summary>

- Gold items (pre-labeled): Inserting known-answer items to check accuracy.  
  - Why not: Requires trusted gold data we don’t have, adds overhead.  

- Dual assignment: Forcing every item to be seen by 2 different workers.  
  - Why not: Doubles labeling cost; unnecessary with such a small, trusted team.  

- Automated outlier detection: Statistical models to flag annotators whose distributions differ significantly.  
  - Why not: Overkill for a 6-person team; meaningful with hundreds of annotators, not here.  

- Live agreement monitoring: Recalculate Krippendorff’s α or Fleiss’ κ during collection.  
  - Why not: Too heavy to run in real time; post-hoc analysis with `worker_id` is sufficient.

</details>

`worker_id` supports IRA by comparing ratings from different annotators on the same items:  
- If IRA is high, our scale is working and team judgment is consistent.  
- If IRA is low, it may indicate ambiguity in the task definition or bias categories.  

Speed & agreement both matter because:
- Speed filters protect against low-effort or inattentive annotation.  
- Agreement analysis confirms that even if people take “enough time,” they interpret the scale in a consistent way.  
- Together, they form a budget-friendly but solid QA framework.

---

## 9. Final report vs setup now

| Final report will include | Set up now |
|---|---|
| Stopping rule (budget-limited 540/stream) | Fix budget in config. of Python code; counters for labels used |
| HIT design (1×6, grouped by prompt for the first round) | Config. 1 × 6 HITs in HTML code, with option to group by prompt_ID |
| Selection method (match-quality with mode) | Implement $q.$ (pair-matching) with mode; prioritise high-variance items |
| Model comparisons w/ pooled Beta modes | Continue with EASL pipeline |
| QA summary (timing floor, audit logs) | Log worker_id, times, per-item variance/labels; edit code + .csvs unless MTurk handles |
| Cost/scalability summary | Simple tracker for HIT count and total labels, can multiply by costings for outsourced annotators later|

---

## 10. Procedural flow

1. **Seed:** For each item, set (α,β)=(1,1).  
2. **Round 1 (1×6 by prompt):** 1×6 of 45 HITs
3. **Update:** After each label, apply α+=s, β+=(1-s); recompute mode/variance; log.  
4. **Selection:** Rank items by variance; deliver HITS 1×6, paired by the Match-Quality formula, 5 HITs per batch before next update
5. **Stop:** When stream hits 540 labels.  
6. **Analysis:** Model distributions, differences.  
7. **Report:** Summarise results and tie back to literature.

---

## Appendix — Match-quality formulae

**Unbounded (TrueSkill):**

$$\
q(\gamma,S_i,S_j)=\sqrt{\tfrac{2\gamma^2}{c^2}}\,\exp\Big(-\tfrac{(\mu_i-\mu_j)^2}{2c^2}\Big).
\$$

**Bounded (EASL):**

$$\
q(\gamma,S_i,S_j)=\sqrt{\tfrac{2\gamma^2}{c^2}}\,\exp\Big(-\tfrac{(M_i-M_j)^2}{2c^2}\Big).
\$$

---
**Efficiency:** EASL achieves DA-level agreement with fewer labels by targeting high-variance items.  
