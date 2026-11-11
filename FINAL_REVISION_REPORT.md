# Final revision report

Manuscript: `medrxiv_final_submission.pdf` (source `medrxiv.tex`).
Backup of the pre-audit version: `medrxiv_backup_20261111.tex`.

Severity key: **Critical** changes a reported finding · **Major** changes an interpretation ·
**Minor** clarity or presentation.

---

## Critical

### C1. Confounded fine-tuning comparison
**Where:** Abstract, §5.4, Discussion, Conclusion, Contributions, Recommendations.
**Issue:** The claim "no better than the stock model (p = 0.63)" compared an unrescaled stock
model against a rescaled fine-tuned model, varying two interventions at once.
**Change:** Replaced throughout with the within-base comparison: fine-tuned v2 + rescale against
`tessdata_best` + rescale, **−8.1 pp, p = 0.031**. Version 1 added at −18.0 pp, p = 0.020.
**Effect on findings:** The conclusion is strengthened. Fine-tuning does not merely fail to
help; it significantly degrades held-out accuracy relative to the model it was built from.
**Verified:** Yes, recomputed from `rows_*_B.csv`, 20 paired documents.

### C2. Rescaling effect reported against the wrong baseline
**Where:** §5.4.
**Issue:** "rescaling improves `tessdata_best` by 9.0 points relative to stock" mixed baselines.
**Change:** Now 11.0 points within-model (p = 0.0001).
**Verified:** Yes.

### C3. Selective verification ablation
**Where:** Table 8, §6.
**Issue:** The magnitude check caught zero additional errors on both test sets, and its row was
omitted from the table.
**Change:** Row restored; the null result is stated explicitly in the text.
**Verified:** Yes, `verify_tess_fast__rapidocr.csv`.

---

## Major

### M1. Dataset totals added across overlapping sets
**Where:** Abstract, §5.1.
**Issue:** "four experiments covered 2,820 values". 2,820 is 832 + 1,988, the readings per
recognition approach in Experiment 3. Test A **is** Experiment 1's document re-read, and
Experiment 2's 910 readings are not included.
**Change:** Abstract now itemises each experiment's size and states the reuse. §5.1 states that
Test A reuses Experiment 1's observations and that the totals must not be added.
**Verified:** Yes, document and condition counts read from the result tables.

### M2. No treatment of multiple comparisons
**Where:** Limitations.
**Change:** Added. Four paired engine comparisons are reported. Under Bonferroni α = 0.0125 the
rescaling results and the v1-to-v2 comparison survive; the two fine-tuning-versus-base
comparisons do not. Direction is consistent, magnitude is less firmly established.

### M3. Clustering not acknowledged for verification intervals
**Where:** Limitations.
**Change:** Added. The binomial intervals on verification recall and the pooled risk ratio use
reading-level observations that cluster within documents; they are descriptive. The
document-level paired analysis is the basis for the mechanism claim.

---

### C4. Comparison-family count and overstated significance
**Where:** Abstract, §5.4, Discussion, Recommendations, Conclusion, Limitations.
**Issue:** The Limitations said "four paired engine comparisons" while five p-values were
reported, and the Bonferroni threshold was computed from the wrong family size. Three places in
the manuscript described fine-tuning as "significantly worse" while the same Limitations
paragraph stated that those comparisons did not survive correction.
**Change:** Family corrected to five, α = 0.010. Disclosed that no analysis plan was
prespecified and that all five tests are post hoc. Every "significantly worse" removed and
replaced with a statement of the observed difference plus an explicit note that it does not
survive correction. The two affected p-values are labelled "unadjusted" throughout.
**Effect on findings:** The claim is weakened. Direction supported, significance not established.
**Verified:** Yes, p-values recomputed from `rows_*_B.csv` over 20 paired documents.

---

## Minor

| ID | Where | Change |
|---|---|---|
| m1 | Table 4 | Fine-tuned v1 row added; caption states the correct baseline for isolating fine-tuning |
| m2 | Figure 4 | Regenerated with v1 included and the like-for-like comparison annotated |
| m3 | §5.1 | Test A / Test B paragraph indentation aligned |
| m4 | Abstract | Trimmed 402 → 354 words, restructured with colons to match medRxiv convention |
| m5 | AI disclosure | Reduced from ~250 to 63 words, matching the 43-word median of real disclosures |
| m6 | Discussion | Removed duplication with the recommendations section |
| m7 | Throughout | "safe" replaced with bounded phrasing about undetected errors |
| m8 | Related work | Positioning added against Kilickaya et al. on alert fatigue |
| m9 | §5.5 | Split-decimal mechanism described in full rather than "as described above" |

---

## Prior-round corrections, retained

- Odds ratio 5.68 reinterpreted as risk ratio 2.80 (95% CI 1.75–4.47)
- Document-level clustered analysis added alongside the pooled Fisher test
- Zero-error claim qualified with its exact binomial interval
- Fine-tuned v1 re-evaluated because its result files had not been kept
- Mislabelled Courier baseline corrected (79.9% was stock + rescale, not stock)
- Repository populated with the mitigation study so the data-availability claim is true
