"""Controlled comparison: deterministic row parser vs the deployed LLM extractor.

Both extractors are given the EXACT SAME OCR text - the saved output of the
fault-injection runs in results/ocr/ - so the only thing that differs is the
extraction stage. The OCR stage, the source document and the ground truth are
held constant.

  A. deterministic baseline : find_lab_value() from ocr_fault_injection.py
  B. deployed component     : app.ingestion.clinical_parser.ClinicalParser
                              .parse_document(), i.e. an LLM call, run against
                              a LOCAL Ollama model so no credentials or paid
                              API are involved.

Reports, per analyte: exact-value accuracy, decimal-place and digit errors,
missing values, unit preservation, and name-value association. Per condition it
also counts labs the LLM emitted that correspond to no ground-truth analyte
(invented or vitals leakage), and records JSON parse failures rather than
dropping them.

The headline comparison is the 2x2: for each analyte, was the deterministic
parser right, and was the LLM right? That separates REPAIRS (LLM fixes an OCR
error) from INTRODUCED errors (LLM breaks a value the parser read correctly).

Usage (from poster-experiment/, with ollama serving):
    PYTHONPATH=../AI-CDSS/ai LLM_PROVIDER=ollama OLLAMA_MODEL=llama3.2:latest \
        python compare_extractors.py --conditions resolution --repeats 1
"""
from __future__ import annotations

import argparse
import difflib
import json
import re
import sys
import time
from pathlib import Path

import pandas as pd

from ocr_fault_injection import (LABS_TRUTH, find_lab_value,
                                 norm)

RES = ["baseline_300dpi", "dpi_200", "dpi_150", "dpi_120", "dpi_100",
       "dpi_85", "dpi_72"]
OTHER = ["jpeg_q15", "rotate_5.0", "blur_3.0", "noise_30", "photo_phone"]


def match_truth(name: str) -> str | None:
    """Map an LLM-returned test name onto one of the 13 ground-truth analytes."""
    n = norm(name)
    best, score = None, 0.0
    for t, *_ in LABS_TRUTH:
        r = difflib.SequenceMatcher(None, norm(t), n).ratio()
        if r > score:
            best, score = t, r
    return best if score >= 0.72 else None


def num(v) -> float | None:
    m = re.search(r"-?\d+(?:\.\d+)?", str(v))
    return float(m.group()) if m else None


def decimal_shift(truth: float, got: float) -> int | None:
    if truth == 0 or got == 0:
        return None
    for k in (-3, -2, -1, 1, 2, 3):
        if abs(got - truth * 10 ** k) < 1e-6 * max(1.0, abs(truth * 10 ** k)):
            return k
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default="results")
    ap.add_argument("--outdir", default="results_extractor")
    ap.add_argument("--conditions", default="resolution",
                    choices=["resolution", "all"])
    ap.add_argument("--repeats", type=int, default=1,
                    help="LLM calls per condition, to measure its own variability")
    a = ap.parse_args()

    from app.ingestion.clinical_parser import ClinicalParser

    conds = RES if a.conditions == "resolution" else RES + OTHER
    ocr_dir = Path(a.results) / "ocr"
    out = Path(a.outdir); out.mkdir(parents=True, exist_ok=True)

    parser = ClinicalParser()
    provider = type(parser.llm_provider).__name__
    model = getattr(parser.llm_provider, "model_name", "?")
    print(f"extractor B: {provider} / {model}", flush=True)

    rows, percond = [], []
    for cond in conds:
        f = ocr_dir / f"{cond}_s0.txt"
        if not f.exists():
            print(f"  SKIP {cond}: no saved OCR text"); continue
        text = f.read_text()

        for rep in range(a.repeats):
            t0 = time.time()
            err = None
            try:
                parsed = parser.parse_document(text)
                labs = parsed.get("labs", []) or []
            except Exception as e:                    # record, never drop
                labs, err = [], f"{type(e).__name__}: {e}"
            elapsed = time.time() - t0

            # map LLM output onto ground truth
            llm_by_truth: dict[str, dict] = {}
            extras = 0
            for l in labs:
                t = match_truth(str(l.get("test_name", "")))
                if t is None:
                    extras += 1
                elif t not in llm_by_truth:           # first mention wins
                    llm_by_truth[t] = l

            n_ok = n_bad = n_miss = n_unit = n_shift = 0
            for name, tval, tunit, _rng, _flag in LABS_TRUTH:
                det, _line, _why = find_lab_value(text, name)
                l = llm_by_truth.get(name)
                got = num(l.get("value")) if l else None
                unit_ok = (l is not None and l.get("unit") is not None
                           and norm(str(l.get("unit"))) == norm(tunit))

                if got is None:
                    st = "missing"; n_miss += 1
                elif abs(got - tval) < 1e-9:
                    st = "correct"; n_ok += 1
                else:
                    st = "corrupted"; n_bad += 1
                n_unit += bool(unit_ok)
                sh = decimal_shift(tval, got) if got is not None else None
                if sh:
                    n_shift += 1

                det_ok = det is not None and abs(det - tval) < 1e-9
                llm_ok = st == "correct"
                rows.append(dict(
                    condition=cond, repeat=rep, analyte=name, truth=tval,
                    det_value=det, det_correct=det_ok,
                    llm_value=got, llm_status=st, llm_correct=llm_ok,
                    llm_name=(l or {}).get("test_name"),
                    llm_unit=(l or {}).get("unit"), unit_preserved=unit_ok,
                    llm_flag=(l or {}).get("flag"), decimal_shift=sh,
                    outcome=("both_correct" if det_ok and llm_ok else
                             "llm_repaired" if llm_ok and not det_ok else
                             "llm_introduced" if det_ok and not llm_ok else
                             "both_wrong"),
                    error=err))

            percond.append(dict(condition=cond, repeat=rep, labs_returned=len(labs),
                                extra_labs=extras, correct=n_ok, corrupted=n_bad,
                                missing=n_miss, units_preserved=n_unit,
                                decimal_shifts=n_shift, seconds=round(elapsed, 1),
                                error=err))
            print(f"  {cond:16s} rep{rep}  labs={len(labs):2d} extra={extras} "
                  f"correct={n_ok:2d}/13 corrupt={n_bad:2d} miss={n_miss:2d} "
                  f"units={n_unit:2d}/13  {elapsed:.0f}s"
                  + (f"  ERROR {err}" if err else ""), flush=True)

    df = pd.DataFrame(rows); pc = pd.DataFrame(percond)
    df.to_csv(out / "per_analyte_llm.csv", index=False)
    pc.to_csv(out / "per_condition_llm.csv", index=False)
    (out / "metadata.json").write_text(json.dumps(
        dict(provider=provider, model=model, conditions=conds,
             repeats=a.repeats, temperature=0.0,
             prompt_source="app.ingestion.clinical_parser.parse_document",
             ocr_source=str(ocr_dir)), indent=2))

    print("\n" + "=" * 72)
    print("2x2 OUTCOME (deterministic parser vs deployed LLM extractor)")
    print("=" * 72)
    print(df.outcome.value_counts().to_string())
    print(f"\n  deterministic correct : {df.det_correct.sum():3d} / {len(df)}")
    print(f"  LLM correct           : {df.llm_correct.sum():3d} / {len(df)}")
    print(f"  units preserved (LLM) : {df.unit_preserved.sum():3d} / {len(df)}")
    print(f"  extra/invented labs   : {pc.extra_labs.sum()}")
    print(f"  JSON/API failures     : {pc.error.notna().sum()} of {len(pc)} calls")
    print(f"\nwrote {out}/per_analyte_llm.csv, per_condition_llm.csv")
    return 0


if __name__ == "__main__":
    sys.exit(main())
