"""Figure 2 for the final poster - character accuracy vs value accuracy.

The point of the figure is the WEDGE between two curves: characters keep being
read correctly long after the numbers stop being right. The strip underneath
decomposes the value shortfall into the two failure modes, which must never be
pooled:

    misread  - a wrong NUMBER was emitted. Downstream sees a plausible value.
    not read - no value was emitted at all. Downstream sees a gap.

Experimental unit is the DOCUMENT (n = 10 synthetic reports, 13 analytes each).
Bands are +/-1 SD between documents, not confidence intervals.

Output is SVG with live text (svg.fonttype="none") so that LibreOffice can turn
it into an EMF that stays vector and keeps its text selectable in the PDF.
"""
from __future__ import annotations

import argparse
import glob
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
from matplotlib import font_manager as fm
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import PercentFormatter

# Carlito ships with LibreOffice and is metric-compatible with Calibri, which
# the poster text uses. Registering it here makes the chart and the poster the
# same typeface in the exported PDF.
for _f in glob.glob("/Applications/LibreOffice.app/Contents/Resources/"
                    "fonts/truetype/Carlito-*.ttf"):
    fm.fontManager.addfont(_f)

INK, INK2, MUTED = "#0b0b0b", "#52514e", "#8b8a85"
BLUE, RED, GREY = "#2f5597", "#b3251f", "#8b8a85"
SURFACE, GRID = "#ffffff", "#e4e3df"

plt.rcParams.update({
    "svg.fonttype": "none",
    "font.family": "Carlito",
    "font.size": 13,
    "axes.labelsize": 14,
    "xtick.labelsize": 13.5,
    "ytick.labelsize": 13,
    "legend.fontsize": 13,
    "axes.edgecolor": MUTED,
    "axes.linewidth": 0.9,
    "axes.facecolor": SURFACE,
    "figure.facecolor": SURFACE,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "xtick.color": INK2, "ytick.color": INK2,
    "axes.labelcolor": INK, "text.color": INK,
    "grid.color": GRID, "grid.linewidth": 0.7,
})

ORDER = [300, 200, 150, 120, 100, 85, 72]


def per_document(results: Path) -> pd.DataFrame:
    """Per-document rates at each resolution, then mean and SD across documents."""
    comb = pd.read_csv(results / "combined.csv")
    cer = pd.read_csv(results / "cer_by_doc.csv")

    val = (comb.groupby(["dpi", "document"])
           .apply(lambda x: pd.Series({
               "mis": (x.status == "corrupted").mean(),
               "unr": (~x.status.isin(["correct", "corrupted"])).mean()}),
               include_groups=False)
           .reset_index())
    val["ok"] = 1 - val.mis - val.unr

    chars = cer.rename(columns={"cer": "c"})[["dpi", "document", "c"]].copy()
    chars["char_ok"] = 1 - chars.c

    df = val.merge(chars[["dpi", "document", "char_ok"]], on=["dpi", "document"])
    g = df.groupby("dpi")
    out = pd.DataFrame({
        "ok": g.ok.mean(), "ok_sd": g.ok.std(ddof=1),
        "char": g.char_ok.mean(), "char_sd": g.char_ok.std(ddof=1),
        "mis": g.mis.mean(), "unr": g.unr.mean(),
        "n": g.ok.size(),
    }).reindex(ORDER)
    return out


# LibreOffice crops a fixed inset off every edge when it converts the SVG to
# EMF. Padding the canvas by more than that inset means only padding is lost.
PAD_MM = 11.0


def build(d: pd.DataFrame, out: Path, width_mm: float) -> None:
    plot_w, plot_h = width_mm, width_mm * 0.60
    W, H = plot_w + 2 * PAD_MM, plot_h + 2 * PAD_MM
    fig = plt.figure(figsize=(W / 25.4, H / 25.4))

    # Margins in millimetres, measured from the padded canvas edge.
    left, right = PAD_MM + 26.2, PAD_MM + 0.7
    top, bottom = PAD_MM + 20.6, PAD_MM + 28.6
    gs = fig.add_gridspec(2, 1, height_ratios=[2.9, 1.35], hspace=0.28,
                          left=left / W, right=1 - right / W,
                          top=1 - top / H, bottom=bottom / H)
    ax = fig.add_subplot(gs[0])
    bx = fig.add_subplot(gs[1])

    x = np.arange(len(ORDER))
    char, ok = d.char.values, d.ok.values

    # The region between the curves is the finding. Neutral grey so that it is
    # never mistaken for one of the coloured uncertainty bands.
    ax.fill_between(x, ok, char, color="#9a9894", alpha=0.11, lw=0, zorder=1)

    for y, sd, col, lab, mk in (
            (char, d.char_sd.values, BLUE, "Characters read correctly  (OCR text)", "o"),
            (ok, d.ok_sd.values, RED, "Laboratory values read correctly", "s")):
        ax.fill_between(x, np.clip(y - sd, 0, 1), np.clip(y + sd, 0, 1),
                        color=col, alpha=0.17, lw=0, zorder=2)
        ax.plot(x, y, color=col, lw=2.7, marker=mk, ms=8.5, mew=0,
                label=lab, zorder=4, clip_on=False)

    # Call out the headline resolution.
    i = ORDER.index(100)
    ax.axvline(i, color=MUTED, lw=0.9, ls=(0, (4, 4)), zorder=0)
    ax.annotate("", xy=(i, char[i]), xytext=(i, ok[i]),
                arrowprops=dict(arrowstyle="<->", color=RED, lw=2.2,
                                shrinkA=2, shrinkB=2), zorder=5)
    halo = dict(facecolor="white", edgecolor="none", pad=2.0)
    ax.text(i - 0.18, 0.80, "31-point gap", ha="right",
            va="center", fontsize=15, color=RED, fontweight="bold",
            bbox=halo, zorder=6)
    ax.text(i + 0.14, char[i] + 0.035, "88.9% of characters",
            ha="left", va="bottom", fontsize=13, color=BLUE, fontweight="bold",
            bbox=halo, zorder=6)
    ax.text(i + 0.14, ok[i] - 0.035, "57.7% of values",
            ha="left", va="top", fontsize=13, color=RED, fontweight="bold",
            bbox=halo, zorder=6)

    ax.set_ylim(0, 1.05)
    ax.set_xlim(-0.38, len(ORDER) - 0.45)
    ax.set_yticks(np.arange(0, 1.01, 0.25))
    ax.yaxis.set_major_formatter(PercentFormatter(1.0))
    ax.set_xticks(x); ax.set_xticklabels([])
    ax.grid(axis="y", zorder=0); ax.set_axisbelow(True)
    ax.set_ylabel("Read correctly", labelpad=6)
    from matplotlib.patches import Patch
    h, l = ax.get_legend_handles_labels()
    patch = Patch(facecolor="#e0dfdb", edgecolor="none")
    h.append(patch)
    l.append("Gap between character and value accuracy")
    ax.legend(h, l, loc="lower left", frameon=False, handlelength=1.9,
              borderaxespad=0.15, labelspacing=0.45)
    ax.set_title("Character accuracy holds up long after the numbers stop being right",
                 fontsize=16.5, fontweight="bold", color=INK, loc="left", pad=23)
    ax.text(0, 1.022, "10 independent synthetic reports \u00d7 13 analytes at each "
            "resolution.  Bands = \u00b11 SD between documents.",
            transform=ax.transAxes, ha="left", va="bottom", fontsize=12.5,
            color=INK2)

    # Strip: how the value shortfall splits. Misread and not-read are different
    # failures and are kept apart here.
    mis, unr, okv = d.mis.values, d.unr.values, d.ok.values
    bx.bar(x, okv, width=0.64, color="#dde3ee")
    bx.bar(x, mis, width=0.64, bottom=okv, color=RED,
           label="Misread (wrong number emitted)")
    bx.bar(x, unr, width=0.64, bottom=okv + mis, color=GREY,
           label="Not read (no value emitted)")
    for j in range(len(x)):
        if mis[j] >= 0.11:
            bx.text(x[j], okv[j] + mis[j] / 2, f"{mis[j]*100:.0f}%", ha="center",
                    va="center", fontsize=12.5, color="white", fontweight="bold")
        if unr[j] >= 0.13:
            bx.text(x[j], okv[j] + mis[j] + unr[j] / 2, f"{unr[j]*100:.0f}%",
                    ha="center", va="center", fontsize=12.5, color="white",
                    fontweight="bold")
    bx.set_ylim(0, 1); bx.set_xlim(-0.38, len(ORDER) - 0.45)
    bx.set_xticks(x); bx.set_xticklabels([str(v) for v in ORDER])
    bx.set_yticks([]); bx.spines["left"].set_visible(False)
    bx.set_xlabel("Scan resolution (dpi)   \u00b7   image quality falls \u2192",
                  labelpad=6)
    from matplotlib.patches import Patch
    h, l = bx.get_legend_handles_labels()
    h = [Patch(facecolor="#dde3ee")] + h
    l = ["Correct"] + l
    # Anchored to the figure, not the axes, so it always clears the x-label.
    fig.legend(h, l, loc="lower center",
               bbox_to_anchor=(0.5, PAD_MM / H), ncol=3,
               frameon=False, handlelength=1.05, columnspacing=1.6,
               handletextpad=0.5, fontsize=11.5)

    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, format="svg")
    plt.close(fig)
    print(f"wrote {out}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default="results_multidoc")
    ap.add_argument("--out", default="figures/fig2_final.svg")
    ap.add_argument("--width-mm", type=float, default=236.0)
    a = ap.parse_args()
    d = per_document(Path(a.results))
    print(d.round(4).to_string())
    build(d, Path(a.out), a.width_mm)
