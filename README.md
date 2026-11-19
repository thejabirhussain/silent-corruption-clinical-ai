# Character accuracy conceals numerical error

Silent value corruption in a clinical document pipeline, and what actually prevents it.

[![DOI](https://img.shields.io/badge/DOI-10.21203%2Frs.3.rs--11720966%2Fv1-blue)](https://doi.org/10.21203/rs.3.rs-11720966/v1)
[![Preprint](https://img.shields.io/badge/preprint-Research%20Square-orange)](https://www.researchsquare.com/article/rs-11720966/v1)
[![License: CC BY 4.0](https://img.shields.io/badge/license-CC%20BY%204.0-lightgrey)](https://creativecommons.org/licenses/by/4.0/)

**Posted 19 November 2026 on Research Square.** This is a preprint: it has a DOI and is
citable, but **it has not been peer reviewed by a journal.**

> Shaik, M. J. H. (2026). *Character accuracy conceals numerical error: silent value
> corruption in a clinical document pipeline, and what actually prevents it.*
> Research Square. https://doi.org/10.21203/rs.3.rs-11720966/v1

```bibtex
@article{shaik2026character,
  title   = {Character accuracy conceals numerical error: silent value corruption
             in a clinical document pipeline, and what actually prevents it},
  author  = {Shaik, Mohammed Jabir Hussain},
  year    = {2026},
  journal = {Research Square},
  note    = {Preprint, not peer reviewed},
  doi     = {10.21203/rs.3.rs-11720966/v1},
  url     = {https://doi.org/10.21203/rs.3.rs-11720966/v1}
}
```

Clinical decision support systems increasingly read patient data from document
images, so optical character recognition sits between the page and every
inference made downstream. Accuracy for that stage is almost always reported at
**character level**, and a laboratory value is not a character.

## What was measured

The image-to-value path of a retrieval-based clinical decision support
prototype, under controlled image degradation. Synthetic reports carrying exact
machine-readable ground truth for 13 analytes, with the **document** as the
experimental unit, across 10 independent reports and 7 scan resolutions.

## Findings

At **100 dpi**, character accuracy was still **88.9%** while:

| | |
|---|---|
| Laboratory values misread | **32.3%** |
| Values not read at all | **10.0%** |
| Corrupted values carrying the **same abnormality flag** as the truth | **89 of 188 (47.3%)** |

Nearly half of all corruptions were therefore invisible to the alerting layer.
The reading was wrong, and the alert looked right.

## The mechanism

Abnormality flags are threshold quantisations of a continuous value. Corrupting
a value that was **already outside** its reference range is far more likely to
leave the flag unchanged than corrupting a normal value:

**61.7% against 22.1%, risk ratio 2.80, 95% CI 1.75 to 4.47.** The effect holds with the
document as the unit of analysis: paired difference 43.0 percentage points, p = 0.0078.

So the errors that survive undetected are concentrated precisely in the
abnormal results, which are the ones that matter clinically. A character-level
accuracy figure cannot see any of this.

## What actually prevents it

Fine-tuning the recogniser did not help. It read the document it was tuned for perfectly at
low resolution, but against its own base model under identical preprocessing it **lost 8.1
percentage points** on held-out reports (unadjusted p = 0.031; this comparison does not
survive correction for multiple testing). That aggregate also conceals a reversal: the
fine-tuned model was the most accurate reader on one half of the held-out set and the least
accurate on the other.

Two things did work. **Upscaling the page before recognition** was the largest single gain,
taking low-resolution accuracy from 60.0% to 98.5% (+11.0 points on held-out data for the
same base model, p = 0.0001). And **requiring agreement between two independently built
readers** caught **193 of 193** corruptions on held-out data, at a 19.8% review rate.

A vision-language model transcribed legible pages accurately but, on degraded pages,
produced fluent values that were never printed, and moved them toward the normal range.

## Layout

| Path | Contents |
|---|---|
| `medrxiv.tex`, `medrxiv.pdf` | **The posted paper** — the version of record behind the DOI |
| `main.tex`, `main.pdf` | Superseded earlier draft, different title and statistics. Kept for history; do not cite |
| `anon.tex`, `anon.pdf` | Anonymised version for double-blind review |
| `figures/` | Figures and the scripts that generate them |
| `experiment/ocr_fault_injection.py` | Controlled image degradation and OCR |
| `experiment/analyse_multidoc.py` | Across-document analysis |
| `experiment/compare_extractors.py` | Extractor comparison |
| `experiment/evaluate_safeguard.py` | Safeguard evaluation |
| `experiment/llm_propagation.py`, `llm_repeat.py` | Propagation of corrupted values downstream |
| `experiment/results*/` | Per-document outputs, tables and summaries |

Generated page images and raw OCR dumps are not tracked, since they are
reproducible from `make_variant_reports.py` and `ocr_fault_injection.py`.

## Status

**Posted preprint**, Research Square, 19 November 2026, version 1,
DOI [10.21203/rs.3.rs-11720966/v1](https://doi.org/10.21203/rs.3.rs-11720966/v1),
CC BY 4.0. Not peer reviewed by a journal; not under review at one.

Earlier presented as a poster at the Vision and Language Symposium, Queen's University
Belfast, October 2026.

All findings come from synthetic documents and bound no claim about performance in
deployment.

## Author

Mohammed Jabir Hussain Shaik, School of Electronics, Electrical Engineering and
Computer Science, Queen's University Belfast.
`mshaik01@qub.ac.uk`
