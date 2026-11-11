# Revision report — medRxiv manuscript

Prepared 10 November 2026. Manuscript: `medrxiv.tex` / `medrxiv.pdf`, 17 pages, 9,352 words,
10 references.

---

## 1. Change summary

### Statistical corrections

| Change | Before | After |
|---|---|---|
| **Odds ratio misread as risk ratio** | "more than five times as likely" (OR 5.68) | **Risk ratio 2.80, 95% CI 1.75–4.47**, risk difference 39.6 pp. OR retained once, labelled as overstating the effect |
| **Clustering ignored** | Fisher exact on 188 pooled corruptions | Pooled result kept, plus **document-level paired analysis**: 65.3% vs 22.3%, paired difference 43.0 pp, Wilcoxon p = 0.0078, 95% bootstrap CI 26.8–58.0, direction holds 8/8. Clustered analysis is now the primary |
| **Zero-error claim unqualified** | "100% of wrong values caught" | 193/193 with **exact 95% CI 98.1–100%**, and an explicit statement that zero observed failures bounds the undetected rate only to below ~2% |
| **No uncertainty in Experiment 3** | Bare percentages | Per-document means with between-document SD, paired Wilcoxon for every engine comparison |
| **Silent counts not normalised** | Raw counts | Share of that reader's corruptions |

### Evidence recovered

**The v1 fine-tune had no surviving result files.** The claim that Courier accuracy fell to 54%
existed only in a repository README. The model file survived, so v1 was **re-evaluated on
Test B for this manuscript**:

| | Times | Courier | Gap | Corrupted | Silent |
|---|---|---|---|---|---|
| v1 + rescale | 85.0% | **46.8%** | 38.2 | 482 | 288 |
| v2 + rescale | 85.3% | 66.3% | 19.0 | 268 | 101 |
| best + rescale | 83.4% | 84.4% | −1.0 | 89 | 29 |

The unverifiable 54% figure is removed. The verified 46.8% replaces it.

### Factual error corrected

The manuscript had compared the fine-tuned model's Courier accuracy (66.3%) against "the stock
model's 79.9%". **79.9% is stock + rescale, not stock.** True stock is 78.8%, and the correct
like-for-like baseline is tess_best + rescale at 84.4%. A per-typeface table now gives all
readers on both faces.

### Interpretation bounded

Every unqualified use of "safe" replaced with "reduced undetected errors in the conditions
tested". The introduction now states explicitly that no real patient record was processed, no
clinician assessed any output, and no clinical decision or outcome was simulated or measured.

### Reader independence qualified

The architectural basis for treating Tesseract and PP-OCR as independent is now stated (line
LSTM versus detector-plus-crop recogniser, different corpora, different characteristic
failures), together with the explicit admission that **statistical independence of their errors
is not established** and that both could fail identically on a sufficiently degraded page.

### Reproducibility made real

The repository previously contained only Experiments 1 and 2. The fine-tuning scripts, training
logs for both versions, both fine-tuned models, the held-out test set and its generator, the
evaluation and verification harnesses, and every per-reading result table have been published:
<https://github.com/thejabirhussain/silent-corruption-clinical-ai>

### Other

Clinical motivation and the synthetic/clinical boundary added to the introduction. Related work
expanded to four themed paragraphs and references from 4 to 10. Novelty stated explicitly
against Yu et al. (2026) and Wang et al. (2026), both of which stop at the extracted field.
Hardcoded versus document-printed reference ranges made explicit. Author contributions added.
Verification terminology defined. Review burden expressed in operational terms.

---

## 2. Verification report

Every numerical claim checked against the released result files. **59 of 59 verified.**

| Claim | Manuscript | Source | Result |
|---|---|---|---|
| Misread rate, 300–72 dpi (7 values) | Table 2 | `results_multidoc/by_resolution_decomposed.csv` | **Verified** |
| Character accuracy, 7 resolutions | Table 2 | `results_multidoc/cer_by_doc.csv` | **Verified** |
| 188 corruptions, 89 silent (47.3%) | Table 3 | `corruptions_classified.csv` | **Verified** |
| Abnormal 61.7% vs normal 22.1% silent | §4.4 | `corruptions_classified.csv` | **Verified** |
| Risk ratio 2.80 (CI 1.75–4.47) | §4.4 | computed, Katz log method | **Verified** |
| Clustered 65.3% vs 22.3%, p = 0.0078 | §4.4 | computed, 8 documents | **Verified** |
| 102 decimal shifts (54.3%) | §4.4 | `corruptions_classified.csv` | **Verified** |
| Plausibility 104/188 (55.3%) | §4.5 | `safeguard.csv` | **Verified** |
| Test B accuracy, 7 readers | Table 4 | `numeric-ocr/results/rows_*_B.csv` | **Verified** |
| Between-document SD, 6 readers | Table 4 | per-document aggregation | **Verified** |
| Corrupted and silent counts, 7 readers | Table 4 | `rows_*_B.csv` | **Verified** |
| Per-typeface accuracy, 7 readers | Table 5 | `rows_*_B.csv` + `testset_b/*.json` | **Verified** |
| Test A ≤150 dpi, 6 readers | Table 4 | `rows_*_A.csv` | **Verified** |
| Wilcoxon comparisons (4) | §5.3 | computed over 20 documents | **Verified** |
| Verification recall and review rate | Table 7 | `verify_tess_fast__rapidocr.csv` | **Verified** |
| Exact binomial CIs | Table 7 | computed, Clopper–Pearson | **Verified** |
| VLM matched comparison | Table 6 | `rows_vlm-*` restricted to shared cells | **Verified** |

---

## 3. Outstanding issues

**Requires author input**

1. **AI-use disclosure accuracy.** The statement says an LLM assistant helped draft and edit the
   text and assisted with code, and that design, metrics, analysis and interpretation are the
   author's. Confirm this describes what happened.
2. **Prototype authorship.** The AI-CDSS was submitted to a conference with five co-authors. If
   any of them contributed to the extraction path measured here, an acknowledgement is needed.
3. **Repository name.** The URL supplied in the review request,
   `silent-corruption-clinical-released`, does not exist. The manuscript cites the real
   repository, `silent-corruption-clinical-ai`.

**Cannot be verified without further work**

4. **Reproduction not independently tested.** The code and data are published and the numbers
   were recomputed from the released result tables, but a clean-machine run from the README has
   not been performed. The manuscript does not claim it has.
5. **Published versions of preprints.** All 10 references were checked against arXiv or the
   publisher. Whether any arXiv preprint has since appeared in a journal was not checked.
6. **VLM generalisation.** One 3B model, on a subset of conditions, Test B covering three
   conditions none of which is poor-fax. Stated in the manuscript.

---

## 4. medRxiv submission checklist

| Requirement | Status |
|---|---|
| Health-related research with methods and data | Clinical document pipeline, measured. **Met** |
| Article type: research article with new data | **Met** |
| Subject category | Health Informatics |
| Not posted on another preprint server | **Met.** Not on arXiv or TechRxiv |
| Single PDF with text and figures | **Met**, 17 pages |
| LaTeX converted to PDF before submission | **Met** |
| Ethics statement | **Met.** Synthetic data, no human subjects, no approval required |
| Funding statement | **Met.** None |
| Competing interests | **Met.** None |
| Author contributions | **Met** |
| AI-use disclosure | **Met**, pending author confirmation |
| Data availability | **Met.** Public repository with code, data, models, results |
| No participant identifying information | **Met.** No real patient data at any stage |
| Clinical trial registration | Not applicable |
| All co-authors consent | **Author to confirm** (sole author) |
| Corresponding author details | Author to supply at submission |

**Note:** the manuscript PDF is already public in the repository. medRxiv's rule concerns other
*preprint servers*; a project repository is not one, and authors routinely publish code
alongside. Low risk, but it exists.

---

## 5. Final consistency pass (10 November)

Issues found and corrected after the main revision:

| Issue | Where | Fix |
|---|---|---|
| **Mislabelled baseline survived in the abstract** | Abstract | "66.3% against 79.9% for the stock model" — 79.9% is stock **+ rescale**. Corrected to "84.4% for the same base model with rescaling alone", matching the body |
| Unbounded safety claim | Abstract, §6 | "No single reader was safe everywhere" → "No reader avoided undetected errors across all conditions" |
| Memorisation claim contradicted the limitation | §5.1 | Now states the generator is shared and cross-references Limitations |
| Experiment numbering invisible | §5, §6 headings | Retitled "Experiment 3: ..." and "Experiment 4: ..." so the labels used in the text map to sections |
| URL overflowed the margin by 3 cm | Data availability | `xurl` package added |

Verified clean: all 10 citations resolve, no uncited references, 4 figures present and
referenced, 8 tables, no remaining overclaim language. Two residual overfull lines of 2 mm and
4 mm, cosmetic only.

**Final state:** 17 pages, 9,374 words, 4 figures, 8 tables, 10 references.

---

## 6. Reviewer-perspective revision (11 November)

| Issue | Fix |
|---|---|
| Abstract 524 words, unstructured | Restructured as **Background / Methods / Results / Conclusions**, now **401 words** |
| Contributions misordered | Clustering contribution moved beside the mechanism it qualifies |
| Contribution overclaimed | "eliminates undetected wrong values" → "left no undetected wrong value in either test set" |
| Novelty untested against the flag literature | New related-work paragraph positioning against **Kilickaya et al., PLoS ONE 2014;9(9):e107930** on false-positive alerts from standard reference ranges. Verified via PMC. This paper is the complementary failure |
| No actionable guidance for practitioners | New section, "What follows for a system that reads clinical documents" — five implications, explicitly framed as implications rather than validated interventions |
| Vague cross-reference in taxonomy | Split-decimal mechanism now described in full with a pointer to Table 5 |

**State:** 18 pages, 9,777 words, 4 figures, 8 tables, 11 references, abstract 401 words.
