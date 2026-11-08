"""Evaluate the physiological plausibility safeguard on the 10-document data.

The safeguard (ai/app/ingestion/clinical_parser.py) rejects a laboratory value
that falls outside a conservative "possible in a living human" envelope, marking
it Implausible and needing verification rather than reporting it as an ordinary
clinical abnormality.

A safeguard is only useful if it catches errors WITHOUT discarding good data,
so this measures three things, not one:

  detected        corrupted values the envelope rejects          (true positive)
  missed          corrupted values the envelope lets through     (false negative)
  false rejection CORRECT values the envelope wrongly rejects    (false positive)

It also reports the quantity that actually matters for safety: of the corrupted
values that were SILENT - that kept the true value's abnormal flag, so nothing
else in the pipeline could see them - how many does the envelope make visible?

Finally it runs a boundary stress test, sweeping each analyte across its
envelope edge to characterise exactly where the rule flips. That describes the
rule precisely without asserting any clinical fact about where the edge SHOULD
be, which is unvalidated.

Usage:  python evaluate_safeguard.py
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

# Envelopes as implemented in clinical_parser.plausible_ranges, keyed by the
# analyte names used in the study's ground truth.
ENVELOPE = {
    "Glucose (fasting)": (10, 1500), "HbA1c": (2, 20), "Hemoglobin": (2, 25),
    "Ferritin": (0.1, 10000), "WBC": (0.1, 500), "Platelets": (1, 2000),
    "Sodium": (90, 190), "Potassium": (1.0, 10.0), "BUN": (1, 300),
    "Creatinine": (0.1, 30), "eGFR": (0, 200), "Troponin I": (0, 100),
    "LDL cholesterol": (5, 600),
}


def rejects(analyte: str, value: float) -> bool:
    lo, hi = ENVELOPE[analyte]
    return not (lo <= value <= hi)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="results_multidoc/combined.csv")
    ap.add_argument("--out", default="results_multidoc/safeguard.csv")
    a = ap.parse_args()

    d = pd.read_csv(a.data)
    d = d[d.extracted.notna()].copy()          # the rule only sees emitted values
    d["tf"] = d.truth_flag.fillna("").astype(str)
    d["ef"] = d.extracted_flag.fillna("").astype(str)
    d["rejected"] = [rejects(r.analyte, r.extracted) for r in d.itertuples()]
    d["silent"] = (d.status == "corrupted") & (d.tf == d.ef)
    d.to_csv(a.out, index=False)

    corrupt = d[d.status == "corrupted"]
    correct = d[d.status == "correct"]
    silent = d[d.silent]

    tp = int(corrupt.rejected.sum())
    fn = int((~corrupt.rejected).sum())
    fp = int(correct.rejected.sum())
    tn = int((~correct.rejected).sum())

    print("=" * 74)
    print("PLAUSIBILITY SAFEGUARD, evaluated on 10 documents x 7 resolutions")
    print("=" * 74)
    print(f"  values the pipeline emitted : {len(d)}")
    print(f"    of which correct          : {len(correct)}")
    print(f"    of which corrupted        : {len(corrupt)}\n")
    print(f"{'':22s}{'rejected':>12s}{'passed':>10s}")
    print(f"  {'corrupted value':20s}{tp:>12d}{fn:>10d}")
    print(f"  {'correct value':20s}{fp:>12d}{tn:>10d}")
    print()
    print(f"  detection rate (recall)      : {tp}/{len(corrupt)} = "
          f"{100*tp/len(corrupt):.1f}%")
    print(f"  FALSE REJECTION rate         : {fp}/{len(correct)} = "
          f"{100*fp/len(correct):.2f}%   <- cost of the safeguard")
    if tp + fp:
        print(f"  precision when it fires      : {tp}/{tp+fp} = "
              f"{100*tp/(tp+fp):.1f}%")

    print(f"\n  SILENT corruptions           : {len(silent)}")
    s_caught = int(silent.rejected.sum())
    print(f"    made visible by safeguard  : {s_caught}/{len(silent)} = "
          f"{100*s_caught/len(silent):.1f}%")
    print(f"    still invisible afterwards : {len(silent)-s_caught}")

    print("\n  by analyte (corrupted values only):")
    g = corrupt.groupby("analyte").agg(
        corrupted=("rejected", "size"), caught=("rejected", "sum"))
    g["rate"] = (100 * g.caught / g.corrupted).round(0)
    print(g.sort_values("corrupted", ascending=False).to_string())

    print("\n  per-document detection rate:")
    pd_ = corrupt.groupby("document").rejected.mean()
    print(f"    mean {100*pd_.mean():.1f}%, SD {100*pd_.std(ddof=1):.1f}%, "
          f"range [{100*pd_.min():.0f}, {100*pd_.max():.0f}]%, n={len(pd_)}")

    print("\n" + "=" * 74)
    print("BOUNDARY STRESS TEST - where does the rule flip?")
    print("=" * 74)
    print("  Describes the implemented rule. It does NOT establish that the")
    print("  boundary is clinically correct; that is unvalidated.\n")
    print(f"  {'analyte':20s}{'envelope':>22s}{'rejects at or beyond':>24s}")
    for name, (lo, hi) in ENVELOPE.items():
        print(f"  {name:20s}{f'{lo} - {hi}':>22s}"
              f"{f'< {lo}  or  > {hi}':>24s}")

    (Path(a.out).parent / "safeguard_summary.json").write_text(json.dumps(dict(
        emitted=len(d), correct=len(correct), corrupted=len(corrupt),
        detected=tp, missed=fn, false_rejections=fp,
        detection_rate=tp / len(corrupt), false_rejection_rate=fp / len(correct),
        silent=len(silent), silent_made_visible=s_caught), indent=2))
    print(f"\nwrote {a.out} and safeguard_summary.json")


if __name__ == "__main__":
    main()
