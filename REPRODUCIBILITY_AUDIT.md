# Reproducibility audit

Repository: https://github.com/thejabirhussain/silent-corruption-clinical-ai

## What is published

| Component | Present | Path |
|---|---|---|
| Document generator and ground truth | Yes | `experiment/make_variant_reports.py`, `numeric-ocr/make_testset_b.py` |
| Held-out test set, 20 reports with truth files | Yes | `numeric-ocr/data/testset_b/` |
| Degradation and OCR harness | Yes | `experiment/ocr_fault_injection.py` |
| Fine-tuning script | Yes | `numeric-ocr/finetune_tesseract.sh` |
| Training-line generator | Yes | `numeric-ocr/make_train_lines.py` |
| Training logs, both versions | Yes | `numeric-ocr/models/finetune_run.log`, `finetune_v2.log` |
| Fine-tuned models, 15 MB each | Yes | `numeric-ocr/models/labnum.traineddata`, `labnum2.traineddata` |
| Evaluation harness | Yes | `numeric-ocr/evaluate.py` |
| Verification implementation | Yes | `numeric-ocr/verify.py` |
| Per-reading result tables | Yes | `numeric-ocr/results/rows_*.csv`, `verify_*.csv` |
| Experiment 1–2 outputs | Yes | `experiment/results*/` |
| Figure generation | Partial — see below | `experiment/make_figures.py` |
| README with reproduction commands | Yes | `numeric-ocr/README.md` |

Not redistributed, obtained from their own sources: stock Tesseract models (`tessdata`,
`tessdata_best`), PP-OCR via `rapidocr_onnxruntime`, Qwen2.5-VL via Ollama. Stated in the
manuscript.

## What was reproduced during this audit

| Result | Reproduced | Method |
|---|---|---|
| Table 4, Test B accuracy, all readers | **Yes** | Recomputed per document from `rows_*_B.csv` |
| Table 4, between-document SDs | **Yes** | Recomputed |
| Table 4, corrupted and silent counts | **Yes** | Recomputed |
| Table 5, per-typeface accuracy | **Yes** | Recomputed, joined to `testset_b/*.json` font field |
| Table 4, Test A ≤150 dpi column | **Yes** | Recomputed from `rows_*_A.csv`, n = 65 |
| Table 8, verification ablation | **Yes** | Read from `verify_tess_fast__rapidocr.csv` |
| All Wilcoxon comparisons | **Yes** | Recomputed from per-document accuracies |
| Risk ratio and CIs | **Yes** | Recomputed, Katz log method and Clopper–Pearson |
| Tables 1–4 of Experiments 1–2 | **Yes** | Recomputed from `results_multidoc/` |
| **Fine-tuned v1 on Test B** | **Re-run from scratch** | Result files had not been retained; `evaluate.py --engine labnum_rescale --testset B` was executed and the output added to the repository |
| Figure 4 | **Regenerated** | From the result tables, during this audit |

## What could not be independently verified

1. **A clean-machine run from the README has not been performed.** All reproduction in this
   audit recomputed published numbers from the released result tables, and re-ran one engine
   evaluation. The full pipeline from document generation through fine-tuning to evaluation has
   not been executed end to end on a fresh environment. The manuscript does not claim it has.

2. **Figures 1–3 are from the original study and their generation scripts
   (`experiment/make_figures.py`, `make_fig2_final.py`) were not re-executed during this audit.**
   Their content was checked against the result tables and matches.

3. **The fine-tuning run itself was not repeated.** The released models are the artefacts of the
   original training runs. Training is stochastic and a rerun would not be bit-identical.

## Sensitive content check

No real patient data, credentials, API keys or tokens are present in the repository. All
documents are synthetic and generated programmatically. Verified by inspection of the published
file list and the `.gitignore`, which excludes the training-line corpora and the third-party
`eng_best.traineddata`.
