# Statistical audit

All figures recomputed from the released per-reading result tables. Source files are under
`numeric-ocr/results/` and `experiment/results_multidoc/` in the repository.

---

## 1. CRITICAL: the fine-tuning comparison was confounded

**The error.** The manuscript reported that fine-tuning was "no better than the stock model on
held-out reports (p = 0.63)". That comparison was `tess_fast` (no rescaling) against
`labnum2_rescale` (rescaled). It varies **two** things at once and cannot isolate fine-tuning.

**Recomputed, holding preprocessing fixed and comparing against the model the fine-tune was
built from:**

| Comparison | Mean difference | Wilcoxon p | Isolates fine-tuning? |
|---|---|---|---|
| `tess_fast` → `labnum2_rescale` *(as published)* | +0.8 pp | 0.6274 | **No** |
| `tess_best_rescale` → `labnum2_rescale` | **−8.1 pp** | **0.0311** | **Yes** |
| `tess_best_rescale` → `labnum_rescale` (v1) | **−18.0 pp** | **0.0198** | **Yes** |
| `labnum_rescale` → `labnum2_rescale` (v1 → v2) | +9.8 pp | 0.0015 | Yes, between versions |

**Effect of rescaling alone, model held fixed:**

| Comparison | Mean difference | Wilcoxon p |
|---|---|---|
| `tess_fast` → `tess_fast_rescale` | +6.5 pp | 0.0012 |
| `tess_best` → `tess_best_rescale` | **+11.0 pp** | 0.0001 |

**Consequence for the paper.** The corrected finding is stronger, not weaker: fine-tuning does
not merely fail to help, it significantly degrades held-out accuracy relative to its own base
model. The manuscript previously also stated rescaling improved `tessdata_best` "by 9.0 points
relative to stock"; that mixed baselines and is now reported as 11.0 points within-model.

Method: paired Wilcoxon signed-rank over the 20 held-out documents, accuracy computed per
document. n = 20 pairs for every test.

---

## 2. Dataset accounting

**The error.** The abstract stated four experiments "covered 2,820 values". 2,820 is
832 + 1,988, which is the number of readings **per recognition approach in Experiment 3**. It is
not a union across the four experiments.

Verified from the result tables:

| Set | Readings | Documents | Conditions | Relationship |
|---|---|---|---|---|
| Experiment 1 | 832 | 1 (`maria`) | 32 named, 64 runs with seeds | — |
| Experiment 2 | 910 | 10 | 7 resolutions | Distinct documents |
| Experiment 3, Test A | 832 | 1 (`maria`) | same 64 runs | **Same observations as Experiment 1**, re-read by each of 7 approaches |
| Experiment 3, Test B | 1,988 | 20 | 7 | New, held out |
| Experiment 4 | — | — | — | **Reuses** the extracted values from Test A and Test B |

Corrected in the abstract and in §5.1, which now states that Test A reuses Experiment 1's
observations and that the totals must not be added.

---

## 3. The magnitude check caught nothing, and the null row was missing

Verified from `verify_tess_fast__rapidocr.csv`:

| Policy | Caught (Test A) | Caught (Test B) |
|---|---|---|
| plausibility | 14 | 99 |
| + precision | 35 | 158 |
| **+ precision + magnitude** | **35** | **158** |
| + structure | 36 | 168 |
| + cross-engine agreement | 43 | 193 |

The magnitude check added **zero** on both test sets. Table 8 previously omitted that row, which
presented a selective ablation. The row is restored and the null result is stated in the text.

---

## 4. Claims re-verified and unchanged

| Claim | Recomputed | Status |
|---|---|---|
| Silent share, abnormal vs normal: 61.7% vs 22.1% | 74/120 and 15/68 | **Verified** |
| Risk ratio 2.80, 95% CI 1.75–4.47 | Katz log method, SE 0.2386 | **Verified** |
| Odds ratio 5.68 (reported only as context) | 5.68 | **Verified** |
| Clustered paired difference 43.0 pp, p = 0.0078 | 8 documents with both groups, Wilcoxon | **Verified** |
| Bootstrap CI 26.8 to 58.0 pp | 10,000 resamples over documents | **Verified** |
| 188 corruptions, 89 silent (47.3%) | `corruptions_classified.csv` | **Verified** |
| Misread rates 300→72 dpi | `by_resolution_decomposed.csv` | **Verified** |
| Per-typeface accuracy, all readers | `rows_*_B.csv` + `testset_b/*.json` | **Verified** |
| Verification recall and review rates | `verify_tess_fast__rapidocr.csv` | **Verified** |
| Exact binomial CIs including 193/193 → 98.1–100% | Clopper–Pearson | **Verified** |
| Test A ≤150 dpi figures, 6 readers | `rows_*_A.csv`, n = 65 | **Verified** |

---

## 5. Statistical limitations stated in the manuscript

- The pooled risk ratio uses reading-level observations that cluster within documents. The
  document-level paired analysis is reported alongside it and is the primary basis for the
  claim.
- Confidence intervals on verification recall are exact binomial on pooled corruptions and do
  not account for clustering; they are presented as descriptive.
- **Multiplicity, corrected after a second audit pass.** The manuscript reports **five** paired
  engine comparisons, not four. No analysis plan was prespecified; all five were chosen after
  the result tables existed, during verification of this manuscript, and are post hoc. Taking
  all five as one family, Bonferroni α = 0.05/5 = **0.010**:

  | Comparison | p | Survives α = 0.010 |
  |---|---|---|
  | `tess_best` → `tess_best_rescale` | 0.0001 | Yes |
  | `tess_fast` → `tess_fast_rescale` | 0.0012 | Yes |
  | `labnum_rescale` → `labnum2_rescale` | 0.0015 | Yes |
  | `tess_best_rescale` → `labnum_rescale` | 0.020 | **No** |
  | `tess_best_rescale` → `labnum2_rescale` | 0.031 | **No** |

  **Consequence:** the manuscript no longer describes fine-tuning as significantly worse than
  its base model. The direction is reported as supported, corroborated across both model
  versions and by the per-typeface breakdown; the inferential claim is reported as not
  established at this sample size. All p-values for the two non-surviving comparisons are
  labelled "unadjusted" wherever they appear.
- The Test A low-resolution column rests on n = 65 readings from one document and is identified
  as such in the text.
