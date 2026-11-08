"""Aggregate the multi-document resolution sweep, clustering by document.

The experimental unit is the DOCUMENT, not the analyte: the 13 analytes in a
report share a page, a font, a rendering pass and one OCR call, so they are not
independent. This script therefore computes a per-document proportion first and
then summarises ACROSS documents, reporting the between-document spread. That
is the uncertainty a reader should care about, and it is honest about n = 10
rather than implying n = 130.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

ORDER = ["baseline_300dpi", "dpi_200", "dpi_150", "dpi_120", "dpi_100",
         "dpi_85", "dpi_72"]
DPI = {"baseline_300dpi": 300, "dpi_200": 200, "dpi_150": 150, "dpi_120": 120,
       "dpi_100": 100, "dpi_85": 85, "dpi_72": 72}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="results_multidoc")
    ap.add_argument("--out", default="results_multidoc/combined.csv")
    a = ap.parse_args()

    frames = []
    for d in sorted(Path(a.root).glob("doc*")):
        f = d / "per_analyte.csv"
        if f.exists():
            t = pd.read_csv(f); t["document"] = d.name
            frames.append(t)
    df = pd.concat(frames, ignore_index=True)
    df.to_csv(a.out, index=False)
    ndoc = df.document.nunique()
    print(f"documents: {ndoc}   rows: {len(df)}   "
          f"= {ndoc} docs x {df.condition.nunique()} conditions x 13 analytes\n")

    # calibration: every document must be perfect at 300 dpi
    base = df[df.condition == "baseline_300dpi"]
    perdoc = base.groupby("document").apply(
        lambda g: (g.status == "correct").sum(), include_groups=False)
    print("CALIBRATION at 300 dpi (must be 13/13 for every document):")
    print("  " + "  ".join(f"{d[-2:]}:{v}" for d, v in perdoc.items()))
    print(f"  -> {'ALL PASS' if (perdoc == 13).all() else 'FAILURES PRESENT'}\n")

    # per-document proportion, then summarise across documents
    rows = []
    for cond in ORDER:
        g = df[df.condition == cond]
        per = g.groupby("document").apply(
            lambda x: pd.Series({
                "wrong": (x.status != "correct").sum() / len(x),
                "corrupted": (x.status == "corrupted").sum() / len(x),
                "silent": sum((x.status == "corrupted") &
                              (x.truth_flag.fillna("") ==
                               x.extracted_flag.fillna(""))) / max(1, (x.status == "corrupted").sum()),
            }), include_groups=False)
        w = per["wrong"]
        rows.append(dict(
            condition=cond, dpi=DPI[cond], n_docs=len(per),
            mean_wrong=w.mean(), sd=w.std(ddof=1),
            se=w.std(ddof=1) / len(per) ** 0.5,
            ci_lo=max(0, w.mean() - 1.96 * w.std(ddof=1) / len(per) ** 0.5),
            ci_hi=min(1, w.mean() + 1.96 * w.std(ddof=1) / len(per) ** 0.5),
            min_wrong=w.min(), max_wrong=w.max(),
            docs_with_any_error=int((w > 0).sum())))
    s = pd.DataFrame(rows)
    s.to_csv(Path(a.root) / "by_resolution.csv", index=False)

    print("VALUES WRONG, per document then averaged across documents")
    print(f"(n = {ndoc} documents; CI is a normal interval on the "
          f"between-document mean)\n")
    print(f"{'dpi':>5} {'mean':>7} {'sd':>7} {'95% CI':>16} {'range':>15} "
          f"{'docs w/ error':>14}")
    for _, r in s.iterrows():
        print(f"{r.dpi:5.0f} {100*r.mean_wrong:6.1f}% {100*r.sd:6.1f}% "
              f"  [{100*r.ci_lo:5.1f}, {100*r.ci_hi:5.1f}]"
              f"   [{100*r.min_wrong:4.0f}, {100*r.max_wrong:4.0f}]%"
              f"   {r.docs_with_any_error:>8d}/{r.n_docs}")

    # decomposition: a wrong number emitted (silent) vs no value at all (loud)
    dec = []
    for cond in ORDER:
        g = df[df.condition == cond]
        per = g.groupby("document").apply(lambda x: pd.Series({
            "cor": (x.status == "corrupted").mean(),
            "mis": (~x.status.isin(["correct", "corrupted"])).mean()}),
            include_groups=False)
        dec.append(dict(dpi=DPI[cond], cor=per.cor.mean(),
                        cor_sd=per.cor.std(ddof=1), mis=per.mis.mean(),
                        mis_sd=per.mis.std(ddof=1)))
    dd = pd.DataFrame(dec)
    dd.to_csv(Path(a.root) / "by_resolution_decomposed.csv", index=False)
    print("\nDECOMPOSED: misread (silent) vs not read (loud), per-document means")
    print(f"{'dpi':>5} {'misread':>10} {'SD':>6} {'not read':>10} {'SD':>6}")
    for _, r in dd.iterrows():
        print(f"{r.dpi:5.0f} {100*r.cor:9.1f}% {100*r.cor_sd:5.1f} "
              f"{100*r.mis:9.1f}% {100*r.mis_sd:5.1f}")
    peak = dd.loc[dd.cor.idxmax()]
    print(f"  misreading peaks at {peak.dpi:.0f} dpi ({100*peak.cor:.1f}%); below "
          f"that values increasingly fail to extract at all")

    print("\nSILENT CORRUPTION (flag unchanged), pooled over all documents")
    c = df[df.status == "corrupted"].copy()
    c["tf"] = c.truth_flag.fillna(""); c["ef"] = c.extracted_flag.fillna("")
    sil = (c.tf == c.ef)
    print(f"  corrupted values : {len(c)}")
    print(f"  flag unchanged   : {sil.sum()} = {100*sil.mean():.1f}%")
    perdoc_sil = c.groupby("document").apply(
        lambda x: (x.tf == x.ef).mean(), include_groups=False)
    print(f"  per-document rate: mean {100*perdoc_sil.mean():.1f}%, "
          f"sd {100*perdoc_sil.std(ddof=1):.1f}%, "
          f"range [{100*perdoc_sil.min():.0f}, {100*perdoc_sil.max():.0f}]%, "
          f"n={len(perdoc_sil)} docs")
    ds = c.decimal_shift.notna()
    print(f"  decimal shifts   : {ds.sum()}/{len(c)} = {100*ds.mean():.1f}%")


if __name__ == "__main__":
    main()
