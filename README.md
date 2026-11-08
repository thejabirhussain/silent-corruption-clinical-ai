# Character accuracy conceals numerical error

Measuring silent value corruption in a clinical document pipeline.

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

**61.7% against 22.1%, Fisher exact p = 1.6e-07, odds ratio 5.68.**

So the errors that survive undetected are concentrated precisely in the
abnormal results, which are the ones that matter clinically. A character-level
accuracy figure cannot see any of this.

## Layout

| Path | Contents |
|---|---|
| `main.tex`, `main.pdf` | The paper |
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

Preprint. Presented as a poster at the Vision and Language Symposium, Queen's
University Belfast, October 2026.

## Author

Mohammed Jabir Hussain Shaik, School of Electronics, Electrical Engineering and
Computer Science, Queen's University Belfast.
`mshaik01@qub.ac.uk`
