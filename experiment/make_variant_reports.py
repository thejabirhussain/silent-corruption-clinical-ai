"""Generate independent synthetic lab reports, each with its own ground truth.

Why this exists
---------------
The original study used ONE document. Repeating a resolution condition on it
adds nothing: rendering and OCR are deterministic, so a second run returns a
byte-identical result. The variance that matters is BETWEEN DOCUMENTS - whether
an OCR error occurs depends on which digits are on the page, and a report whose
potassium is 4.2 cannot produce the 5.8 -> 58 decimal error at all.

So the experimental unit is the document. This script produces N of them, each
with different values and slightly different typography, and writes the exact
ground truth beside each PDF. Document 0 reproduces the original report so the
earlier results remain comparable.

Patient data is synthetic throughout; the values are sampled per analyte from
plausible ranges and are NOT guaranteed to be clinically coherent as a panel.
That is a documented limitation: it is adequate for studying OCR of numerals,
not for studying clinical reasoning.

Usage:  python make_variant_reports.py --n 10 --outdir documents
"""
from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

import pymupdf as fitz

# (name, unit, printed reference range, sampling range, decimals)
ANALYTES = [
    ("Glucose (fasting)", "mg/dL",         "70 - 99",       (60, 420),    0),
    ("HbA1c",             "%",             "4.0 - 5.6",     (4.5, 13.5),  1),
    ("Hemoglobin",        "g/dL",          "12.0 - 15.5",   (6.5, 16.5),  1),
    ("Ferritin",          "ng/mL",         "15 - 200",      (5, 320),     0),
    ("WBC",               "10^9/L",        "4.5 - 11.0",    (2.5, 18.0),  1),
    ("Platelets",         "10^9/L",        "150 - 450",     (90, 520),    0),
    ("Sodium",            "mEq/L",         "135 - 145",     (126, 149),   0),
    ("Potassium",         "mEq/L",         "3.5 - 5.0",     (2.9, 6.4),   1),
    ("BUN",               "mg/dL",         "7 - 20",        (6, 78),      0),
    ("Creatinine",        "mg/dL",         "0.6 - 1.2",     (0.6, 6.4),   1),
    ("eGFR",              "mL/min/1.73m2", "> 60",          (8, 96),      0),
    ("Troponin I",        "ng/mL",         "0.00 - 0.04",   (0.01, 0.95), 2),
    ("LDL cholesterol",   "mg/dL",         "< 100",         (58, 205),    0),
]

# document 0 = the original report, so earlier results stay comparable
ORIGINAL = ["248", "9.2", "9.4", "9", "7.4", "262", "133", "5.8", "42",
            "2.1", "26", "0.07", "142"]

FLAG_RULES = {  # (low, high) used only to print the H/L column
    "Glucose (fasting)": (70, 99), "HbA1c": (4.0, 5.6), "Hemoglobin": (12.0, 15.5),
    "Ferritin": (15, 200), "WBC": (4.5, 11.0), "Platelets": (150, 450),
    "Sodium": (135, 145), "Potassium": (3.5, 5.0), "BUN": (7, 20),
    "Creatinine": (0.6, 1.2), "eGFR": (60, 1e9), "Troponin I": (0.0, 0.04),
    "LDL cholesterol": (0, 99),
}

NAMES = ["Maria Alvarez", "John Okafor", "Aisha Rahman", "Tomas Novak",
         "Grace Mbeki", "Peter Lindqvist", "Sana Qureshi", "Daniel Kim",
         "Elena Rossi", "Omar Haddad", "Ruth Campbell", "Hiroshi Tanaka"]


def sample_values(doc_i: int, rng: random.Random) -> list[str]:
    if doc_i == 0:
        return list(ORIGINAL)
    out = []
    for _name, _u, _r, (lo, hi), dp in ANALYTES:
        v = rng.uniform(lo, hi)
        out.append(f"{v:.{dp}f}" if dp else f"{int(round(v))}")
    return out


def flag_for(name: str, value: str) -> str:
    lo, hi = FLAG_RULES[name]
    v = float(value)
    return "L" if v < lo else ("H" if v > hi else "")


def build(doc_i: int, outdir: Path, rng: random.Random) -> dict:
    vals = sample_values(doc_i, rng)
    truth = [[n, float(v), u, r, flag_for(n, v)]
             for (n, u, r, _s, _d), v in zip(ANALYTES, vals)]

    rows = "".join(
        f"<tr><td>{n}</td><td class='num{' ab' if flag_for(n, v) else ''}'>{v}</td>"
        f"<td>{u}</td><td>{r}</td><td class='flag'>{flag_for(n, v)}</td></tr>"
        for (n, u, r, _s, _d), v in zip(ANALYTES, vals))

    # mild typographic variation across documents (layout is a nuisance factor)
    body_pt = [9.5, 9.0, 10.0, 9.5, 8.5][doc_i % 5]
    cell_pad = [2, 3, 2, 1, 3][doc_i % 5]
    name = NAMES[doc_i % len(NAMES)]

    HTML = f"""
<div class="banner">SYNTHETIC PATIENT RECORD &#8212; FOR DEMONSTRATION ONLY. NOT A REAL PERSON.</div>
<h1>Riverside General Hospital &#8212; Discharge Summary</h1>
<table class="demo">
<tr><td><b>Patient:</b> {name} (synthetic)</td><td><b>MRN:</b> DEMO-{240000+doc_i}</td></tr>
<tr><td><b>Age / Sex:</b> {52 + (doc_i*7) % 30}-year-old {'Female' if doc_i % 2 else 'Male'}</td>
    <td><b>Attending:</b> Internal Medicine</td></tr>
</table>
<h2>Laboratory Results (09/17/2026)</h2>
<table class="labs">
<tr><th>Test</th><th>Result</th><th>Units</th><th>Reference</th><th>Flag</th></tr>
{rows}
</table>
<h2>Vitals at Discharge</h2>
<p>BP 1{30+doc_i}/8{doc_i%10} mmHg, HR {68+doc_i}, SpO2 9{4+doc_i%5}% on room air.</p>
"""
    CSS = f"""
* {{ font-family: sans-serif; }}
body {{ font-size: {body_pt}pt; color: #1f1f1f; }}
.banner {{ background-color: #fde8e8; color: #9b1c1c; font-size: 8pt;
          font-weight: bold; padding: 4px; text-align: center; }}
h1 {{ font-size: 14pt; color: #000db5; margin: 8px 0 4px 0; }}
h2 {{ font-size: 10.5pt; color: #000db5; margin: 10px 0 3px 0;
     border-bottom: 1px solid #d0d4e8; }}
p {{ margin: 2px 0; line-height: 1.35; }}
table.demo td {{ padding: 2px 16px 2px 0; }}
table.labs {{ border-collapse: collapse; width: 100%; }}
table.labs th {{ background-color: #eef0ff; text-align: left;
                padding: 3px 6px; font-size: {body_pt - 0.5}pt; }}
table.labs td {{ border-bottom: 1px solid #e5e5e5; padding: {cell_pad}px 6px;
                font-size: {body_pt - 0.5}pt; }}
td.ab {{ font-weight: bold; }}
td.flag {{ color: #b91c1c; font-weight: bold; }}
"""
    pdf = outdir / f"doc{doc_i:02d}.pdf"
    story = fitz.Story(html=HTML, user_css=CSS)
    writer = fitz.DocumentWriter(str(pdf))
    mediabox = fitz.paper_rect("letter")
    where = mediabox + (48, 42, -48, -42)
    more = True
    while more:
        dev = writer.begin_page(mediabox)
        more, _ = story.place(where)
        story.draw(dev)
        writer.end_page()
    writer.close()

    (outdir / f"doc{doc_i:02d}_truth.json").write_text(json.dumps(truth, indent=1))
    pages = fitz.open(pdf).page_count
    return dict(doc=doc_i, pdf=str(pdf), pages=pages, body_pt=body_pt,
                patient=name)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=10)
    ap.add_argument("--outdir", default="documents")
    ap.add_argument("--seed", type=int, default=20261016)
    a = ap.parse_args()
    out = Path(a.outdir); out.mkdir(parents=True, exist_ok=True)
    rng = random.Random(a.seed)
    meta = [build(i, out, rng) for i in range(a.n)]
    (out / "index.json").write_text(json.dumps(
        dict(seed=a.seed, n=a.n, documents=meta), indent=2))
    for m in meta:
        print(f"  doc{m['doc']:02d}  pages={m['pages']}  body={m['body_pt']}pt  "
              f"{m['patient']}")
    print(f"\nwrote {a.n} documents + ground truth to {out}/")


if __name__ == "__main__":
    main()
