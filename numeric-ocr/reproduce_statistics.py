"""Reproduce every statistic reported in the manuscript from the released result tables.

Run from the numeric-ocr directory:

    python reproduce_statistics.py

Requires pandas, numpy and scipy. It reads only the per-reading CSV files in results/ and
the ground-truth JSON files in data/testset_b/, and prints each reported value next to the
value recomputed here. Nothing is written.
"""
from __future__ import annotations

import glob
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import wilcoxon, fisher_exact, beta

HERE = Path(__file__).resolve().parent
RES = HERE / "results"
EXP2 = HERE.parent / "experiment" / "results_multidoc" / "corruptions_classified.csv"


def line(c=""):
    print(("=" * 78) if not c else f"\n{c}\n" + "-" * len(c))


def per_document_accuracy(engine: str, testset: str = "B") -> pd.Series:
    """Exact value accuracy within each document. The document is the experimental unit."""
    d = pd.read_csv(RES / f"rows_{engine}_{testset}.csv")
    return d.groupby("doc").apply(lambda x: (x.status == "correct").mean(), include_groups=False)


def wilson_or_exact_ci(k: int, n: int) -> tuple[float, float]:
    """Clopper-Pearson exact binomial interval, in percent."""
    lo = 0.0 if k == 0 else beta.ppf(0.025, k, n - k + 1)
    hi = 1.0 if k == n else beta.ppf(0.975, k + 1, n - k)
    return 100 * lo, 100 * hi


# ---------------------------------------------------------------- engine comparisons
line("FIVE PAIRED ENGINE COMPARISONS (Test B, document as the unit, n = 20)")
COMPARISONS = [
    ("tess_fast", "tess_fast_rescale", "rescaling, stock model held fixed"),
    ("tess_best", "tess_best_rescale", "rescaling, tessdata_best held fixed"),
    ("labnum_rescale", "labnum2_rescale", "fine-tune v1 vs v2, preprocessing held fixed"),
    ("tess_best_rescale", "labnum_rescale", "fine-tuning v1 vs its base, preprocessing held fixed"),
    ("tess_best_rescale", "labnum2_rescale", "fine-tuning v2 vs its base, preprocessing held fixed"),
]
pvals = []
for a, b, why in COMPARISONS:
    x, y = per_document_accuracy(a), per_document_accuracy(b)
    assert list(x.index) == list(y.index), "documents must align for a paired test"
    _, p = wilcoxon(x, y)
    pvals.append(p)
    print(f"  {a:>18s} -> {b:<18s} {100*(y.mean()-x.mean()):+6.1f} pp   p = {p:.4f}   [{why}]")

k = len(COMPARISONS)
alpha = 0.05 / k
line(f"BONFERRONI, family of {k} post hoc tests, alpha = 0.05/{k} = {alpha:.3f}")
for (a, b, _), p in zip(COMPARISONS, pvals):
    print(f"  {a:>18s} -> {b:<18s} p = {p:.4f}   {'survives' if p < alpha else 'DOES NOT survive'}")

# ---------------------------------------------------------------- accuracy table
line("TEST B ACCURACY BY READER (mean of 20 per-document values, SD between documents)")
for e in ["tess_fast", "tess_best", "labnum_rescale", "labnum2_rescale",
          "rapidocr", "tess_fast_rescale", "tess_best_rescale"]:
    acc = per_document_accuracy(e)
    d = pd.read_csv(RES / f"rows_{e}_B.csv")
    w = int((d.status == "corrupted").sum())
    s = int(d["silent"].fillna(0).astype(bool).sum())
    print(f"  {e:<20s} {100*acc.mean():5.1f}%  SD {100*acc.std():4.1f}  "
          f"corrupted {w:4d}  silent {s:3d} ({100*s/max(w,1):4.1f}% of corruptions)")

# ---------------------------------------------------------------- typeface split
line("TEST B BY TYPEFACE (note: typeface is aliased with layout, see manuscript Limitations)")
font = {Path(p).stem: json.load(open(p))["font"]
        for p in glob.glob(str(HERE / "data" / "testset_b" / "report_*.json"))}
for e in ["tess_fast", "tess_best", "labnum_rescale", "labnum2_rescale",
          "rapidocr", "tess_fast_rescale", "tess_best_rescale"]:
    d = pd.read_csv(RES / f"rows_{e}_B.csv")
    d["font"] = d.doc.map(font)
    g = d.groupby("font").apply(lambda x: 100 * (x.status == "correct").mean(), include_groups=False)
    print(f"  {e:<20s} Times {g.get('Times', float('nan')):5.1f}%   Courier {g.get('Courier', float('nan')):5.1f}%")

# ---------------------------------------------------------------- split-decimal mechanism
line("SPLIT-DECIMAL SIGNATURE IN THE OCR OUTPUT (digits separated by spaces around a point)")
for e in ["tess_best_rescale", "labnum_rescale", "labnum2_rescale", "tess_fast_rescale"]:
    d = pd.read_csv(RES / f"rows_{e}_B.csv")
    d["font"] = d.doc.map(font)
    bad = d[d.status == "corrupted"]
    sig = bad.line.astype(str).str.contains(r"\d\s+\.\s+\d", regex=True, na=False)
    print(f"  {e:<20s} corrupted {len(bad):4d}   with signature: "
          f"Courier {int(sig[bad.font=='Courier'].sum()):3d}   Times {int(sig[bad.font=='Times'].sum()):3d}")

# ---------------------------------------------------------------- Experiment 2 mechanism
if EXP2.exists():
    line("EXPERIMENT 2: SILENT CORRUPTION OF ABNORMAL VS NORMAL VALUES")
    d = pd.read_csv(EXP2)
    d["silent"] = d.klass == "Silent (flag unchanged)"
    d["abn"] = d.truth_flag.notna() & (d.truth_flag.astype(str).str.strip() != "") \
        & (d.truth_flag.astype(str) != "nan")
    a, n = d[d.abn], d[~d.abn]
    ka, na_, kn, nn_ = a.silent.sum(), len(a), n.silent.sum(), len(n)
    print(f"  pooled: abnormal {100*ka/na_:.1f}% ({ka}/{na_})   normal {100*kn/nn_:.1f}% ({kn}/{nn_})")
    rr = (ka / na_) / (kn / nn_)
    se = np.sqrt(1 / ka - 1 / na_ + 1 / kn - 1 / nn_)
    print(f"  risk ratio {rr:.2f}  (95% CI {np.exp(np.log(rr)-1.96*se):.2f}-{np.exp(np.log(rr)+1.96*se):.2f})")
    orr, pf = fisher_exact([[ka, na_ - ka], [kn, nn_ - kn]])
    print(f"  odds ratio {orr:.2f}, Fisher exact p = {pf:.2e}  (reported as context only)")

    rows = [(doc, g[g.abn].silent.mean(), g[~g.abn].silent.mean())
            for doc, g in d.groupby("document")
            if len(g[g.abn]) and len(g[~g.abn])]
    t = pd.DataFrame(rows, columns=["doc", "abn", "norm"])
    _, pw = wilcoxon(t.abn, t.norm)
    diff = t.abn - t.norm
    rng = np.random.default_rng(7)
    bs = [diff.values[rng.integers(0, len(t), len(t))].mean() for _ in range(10000)]
    print(f"  clustered ({len(t)} documents with both groups): "
          f"{100*t.abn.mean():.1f}% vs {100*t.norm.mean():.1f}%, "
          f"paired diff {100*diff.mean():+.1f} pp, Wilcoxon p = {pw:.4f}")
    print(f"  95% bootstrap CI over documents: "
          f"{100*np.percentile(bs,2.5):+.1f} to {100*np.percentile(bs,97.5):+.1f} pp")

# ---------------------------------------------------------------- verification
line("VERIFICATION ABLATION (primary tess_fast, secondary rapidocr)")
v = pd.read_csv(RES / "verify_tess_fast__rapidocr.csv")
for _, r in v[v.testset == "B"].iterrows():
    lo, hi = wilson_or_exact_ci(int(r.caught), int(r.corrupted))
    print(f"  {r.policy:<28s} {int(r.caught):3d}/{int(r.corrupted)} = {r['recall_%']:5.1f}%  "
          f"95% CI {lo:5.1f}-{hi:5.1f}   false alarms {r['false_alarm_%']:4.1f}%  "
          f"review {r['review_rate_%']:5.1f}%")

line()
print("Done. Every figure above is computed from the released result tables.")
