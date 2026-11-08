"""Render the poster figures from the fault-injection results.

Outputs vector PDF (for print) and 300 dpi PNG (for drafts) sized for a
185 mm-wide panel on an A2 poster. Fonts are set in points so that the PDF,
placed at 185 mm, reads correctly at 1-1.5 m.

Usage: python make_figures.py --results results/ --outdir figures/
"""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import PercentFormatter

# Validated two-slot categorical palette (dataviz reference instance, light mode)
BLUE, RED = "#2a78d6", "#e34948"
INK, INK2, MUTED = "#0b0b0b", "#52514e", "#8b8a85"
SURFACE = "#fcfcfb"

PANEL_IN = 185 / 25.4   # one-column panel
FULL_IN = 392 / 25.4    # full content width (both columns)

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 13,
    "axes.labelsize": 14,
    "axes.titlesize": 15,
    "xtick.labelsize": 12.5,
    "ytick.labelsize": 12.5,
    "legend.fontsize": 12.5,
    "axes.edgecolor": MUTED,
    "axes.linewidth": 0.8,
    "axes.facecolor": SURFACE,
    "figure.facecolor": SURFACE,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "xtick.color": INK2, "ytick.color": INK2,
    "axes.labelcolor": INK, "text.color": INK,
    "grid.color": "#e4e3df", "grid.linewidth": 0.7,
    "pdf.fonttype": 42,
})


def fig_resolution(res: Path, out: Path) -> None:
    """Figure 2 - character errors vs the TWO kinds of value failure.

    A value can fail in two very different ways and they must not be pooled:
      misread  - a wrong NUMBER is emitted. Silent: downstream sees a value.
      not read - no value is emitted at all. Loud: any caller can see the gap.
    Only the first is the subject of this poster.

    All three series are fractions on one 0-1 axis; never a dual axis. Bands
    are +/-1 SD BETWEEN DOCUMENTS (n = 10), the document being the
    experimental unit.
    """
    v = pd.read_csv(Path("results_multidoc/by_resolution_decomposed.csv"))
    c = pd.read_csv(Path("results_multidoc/cer_by_doc.csv"))
    cer = c.groupby("dpi").cer.agg(["mean", "std"]).reset_index().sort_values("dpi")
    v = v.sort_values("dpi")
    dpi = v.dpi.to_numpy()
    cm, cs = cer["mean"].to_numpy(), cer["std"].to_numpy()

    fig, ax = plt.subplots(figsize=(PANEL_IN, PANEL_IN * 0.62))
    ax.set_axisbelow(True); ax.yaxis.grid(True)

    ax.fill_between(dpi, np.clip(v.cor - v.cor_sd, 0, 1), v.cor + v.cor_sd,
                    color=RED, alpha=0.16, lw=0)
    ax.fill_between(dpi, np.clip(cm - cs, 0, 1), cm + cs,
                    color=BLUE, alpha=0.14, lw=0)
    ax.plot(dpi, v.cor, "-o", color=RED, lw=2.2, ms=8, mec=SURFACE, mew=1.5,
            label="Values MISREAD  (a wrong number was emitted)",
            zorder=4, clip_on=False)
    ax.plot(dpi, v.mis, "--s", color="#8b8a85", lw=1.8, ms=7, mec=SURFACE,
            mew=1.2, label="Values NOT READ  (no value was emitted)",
            zorder=3, clip_on=False)
    ax.plot(dpi, cm, "-o", color=BLUE, lw=2.0, ms=8, mec=SURFACE, mew=1.5,
            label="Characters read incorrectly (OCR text)", zorder=3,
            clip_on=False)

    ax.invert_xaxis(); ax.set_xscale("log")
    ax.set_xticks(dpi); ax.set_xticklabels([str(int(x)) for x in dpi])
    ax.minorticks_off()
    ax.set_xlabel("Scan resolution (dpi)  \u2014  degradation increases \u2192")
    ax.set_ylabel("Rate")
    ax.set_ylim(-0.03, 0.92)
    ax.yaxis.set_major_formatter(PercentFormatter(1.0))

    i = list(dpi).index(100)
    ax.annotate(f"At 100 dpi: {v.cor.iloc[i]:.0%} of values misread,\n"
                f"while {1-cm[i]:.0%} of characters are still correct",
                xy=(dpi[i], v.cor.iloc[i]), xycoords="data",
                xytext=(0.03, 0.50), textcoords="axes fraction",
                ha="left", va="center", color=INK, fontsize=12,
                fontweight="bold", linespacing=1.4,
                arrowprops=dict(arrowstyle="-", color=RED, lw=1.2, shrinkB=7))
    j = list(dpi).index(85)
    ax.annotate("misreading stops rising here:\nbelow this, values vanish instead",
                xy=(dpi[j], v.cor.iloc[j]), xycoords="data",
                xytext=(0.30, 0.235), textcoords="axes fraction",
                ha="left", va="center", color=INK2, fontsize=10.5,
                linespacing=1.35,
                arrowprops=dict(arrowstyle="-", color=INK2, lw=1.0, shrinkB=6))

    ax.legend(loc="upper left", frameon=False, handlelength=2.1, fontsize=11.5)
    ax.set_title("OCR text quality does not predict value-level safety\n"
                 "10 independent reports; band = \u00b11 SD between documents",
                 loc="left", pad=10, fontweight="bold", fontsize=13.5,
                 linespacing=1.5)
    fig.tight_layout()
    fig.savefig(out / "fig2_resolution.pdf", bbox_inches="tight")
    fig.savefig(out / "fig2_resolution.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def fig_factors(res: Path, out: Path) -> None:
    """Figure 2b - small multiples. One series per panel, so no legend needed."""
    s = pd.read_csv(res / "summary.csv")
    fams = [("blur", "Blur (\u03c3, px)"),
            ("jpeg", "JPEG quality \u2193"),
            ("rotation", "Rotation (\u00b0)"),
            ("noise", "Noise (\u03c3)")]
    fig, axes = plt.subplots(1, 4, figsize=(PANEL_IN, PANEL_IN * 0.36),
                             sharey=True)
    for ax, (fam, lab) in zip(axes, fams):
        f = s[s.family == fam].sort_values("level")
        x = f.level.to_numpy()
        y = 1.0 - f.value_acc_mean.to_numpy()
        if fam == "jpeg":
            ax.invert_xaxis()
        ax.set_axisbelow(True)
        ax.yaxis.grid(True)
        ax.plot(x, y, "-o", color=RED, lw=2.0, ms=7, mec=SURFACE, mew=1.4,
                clip_on=False, zorder=3)
        ax.set_xlabel(lab, fontsize=11.5)
        ax.tick_params(labelsize=11)
        ax.set_ylim(-0.02, 1.02)
    axes[0].set_ylabel("Values wrong", fontsize=12)
    axes[0].yaxis.set_major_formatter(PercentFormatter(1.0))
    fig.suptitle("All four held at 300 dpi: each is harmless until a cliff",
                 x=0.005, ha="left", fontsize=12.5, fontweight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.84), w_pad=1.8)
    fig.savefig(out / "fig2b_factors.pdf", bbox_inches="tight")
    fig.savefig(out / "fig2b_factors.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def fig_taxonomy(res: Path, out: Path) -> None:
    """Figure 3 - what the flagging layer does with a corrupted value.

    Laid out for a full-width poster band: one flat bar, legend in a single
    row of four so the figure stays short.
    """
    from matplotlib.patches import Patch

    c = pd.read_csv(Path("results_multidoc/corruptions_classified.csv"))
    order = ["Silent (flag unchanged)",
             "False alarm (normal -> flagged)",
             "Flag changed (wrong direction/severity)",
             "Missed alarm (abnormal -> normal)"]
    short = ["Flag unchanged",
             "Normal read as abnormal",
             "Flag inverted: low \u2192 high",
             "Abnormal read as normal"]
    n = len(c)
    counts = [int((c.klass == k).sum()) for k in order]
    shades = ["#b3251f", "#d4584e", "#e8938c", "#f3c4bf"]

    fig, ax = plt.subplots(figsize=(FULL_IN, FULL_IN * 0.165))
    left = 0.0
    for v, sh in zip(counts, shades):
        ax.barh(0, v, left=left, height=0.5, color=sh,
                edgecolor=SURFACE, linewidth=2)
        if v / n > 0.09:
            ax.text(left + v / 2, 0, str(v), ha="center", va="center",
                    color="white" if sh in shades[:2] else INK,
                    fontsize=17, fontweight="bold")
        left += v
    ax.set_xlim(0, n); ax.set_ylim(-0.38, 0.38); ax.axis("off")

    handles = [Patch(facecolor=sh, edgecolor=SURFACE, label=f"{lbl}  ({v})")
               for sh, lbl, v in zip(shades, short, counts)]
    ax.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, -0.12),
              ncol=4, frameon=False, fontsize=13, handlelength=1.1,
              handleheight=1.1, columnspacing=2.2, borderpad=0)
    ax.set_title(f"{counts[0]} of {n} corrupted values ({counts[0]/n:.0%}) kept the "
                 f"true value's flag \u2014 the flagging layer cannot distinguish them\n"
                 f"10 documents; per-document rate 48% (SD 13%, range 23\u201364%)",
                 loc="left", pad=9, fontweight="bold", fontsize=14,
                 linespacing=1.5)
    fig.tight_layout()
    fig.savefig(out / "fig3_taxonomy.pdf", bbox_inches="tight")
    fig.savefig(out / "fig3_taxonomy.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default="results")
    ap.add_argument("--outdir", default="figures")
    a = ap.parse_args()
    res, out = Path(a.results), Path(a.outdir)
    out.mkdir(parents=True, exist_ok=True)
    fig_resolution(res, out)
    fig_factors(res, out)
    fig_taxonomy(res, out)
    fig_architecture(out)
    print(f"wrote figures to {out}/")




# --------------------------------------------------------------------------
# Figure 1 - architecture. Appended as a separate entry point so the data
# figures and the diagram can be rebuilt independently.
# --------------------------------------------------------------------------
def fig_architecture(out: Path) -> None:
    """Figure 1 - the measured pipeline, laid out left to right.

    Horizontal so it can run full width across the poster: vision enters at
    the left, language leaves at the right, and the missing plausibility check
    sits visibly in the gap.
    """
    from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle

    fig, ax = plt.subplots(figsize=(FULL_IN, FULL_IN * 0.295))
    ax.set_xlim(0, 100); ax.set_ylim(23, 100); ax.axis("off")

    stages = [
        ("Patient document\nPDF scan or photo", "#dbe7f7"),
        ("OCR\nTesseract 5.5", "#dbe7f7"),
        ("Extracted values\n13 analytes", "#f0f0ee"),
        ("Abnormal-value flagging\n17 hardcoded ranges", "#f0f0ee"),
        ("Generated clinical\nrecommendation", "#fae0dd"),
    ]
    prov = [
        "synthetic input",
        "production config",
        "BOTH measured",
        "production logic",
        "production prompt",
    ]
    prov_col = ["#8b8a85", "#1b7f4f", "#1b7f4f", "#1b7f4f", "#1b7f4f"]
    notes = [
        None,
        "89% of characters still correct at 100 dpi\n\u2014 but 32% of values MISREAD (10 reports)",
        "decimal points are the first casualty:\n\u201c12.0 - 15.5\u201d is read as \u201c120-155\u201d",
        "ranges are not age- or sex-aware;\n47% of misreads keep the true flag",
        "\u201cQuote patient values EXACTLY\nas listed\u201d \u2014 core/prompts.py",
    ]
    n = len(stages)
    L, R = 1.5, 98.5
    gapw = 4.2
    bw = (R - L - gapw * (n - 1)) / n
    yc, bh = 60.0, 23.0

    centres = []
    for i, ((label, fc), note) in enumerate(zip(stages, notes)):
        x = L + i * (bw + gapw)
        centres.append(x + bw / 2)
        ax.add_patch(FancyBboxPatch((x, yc - bh / 2), bw, bh,
                     boxstyle="round,pad=0,rounding_size=1.1",
                     facecolor=fc, edgecolor="#9aa0a6", linewidth=1.0))
        ax.text(x + bw / 2, yc, label, ha="center", va="center",
                fontsize=13, color=INK, linespacing=1.35)
        ax.text(x + bw / 2, yc - bh / 2 - 3.0, prov[i], ha="center", va="top",
                fontsize=9.5, color=prov_col[i], fontweight="bold")
        if note:
            ax.text(x + bw / 2, yc - bh / 2 - 9.5, note, ha="center", va="top",
                    fontsize=10.5, color=INK2, linespacing=1.35)

    for i in range(n - 1):
        x0 = L + i * (bw + gapw) + bw
        ax.add_patch(FancyArrowPatch((x0 + 0.3, yc), (x0 + gapw - 0.3, yc),
                     arrowstyle="-|>", mutation_scale=14,
                     color="#6f7479", lw=1.4, shrinkA=0, shrinkB=0))

    # the gap: between flagging and generation nothing checks plausibility
    xg = L + 3 * (bw + gapw) + bw
    ax.add_patch(Rectangle((xg - bw * 0.46, yc + bh / 2 + 3.0), bw * 0.92, 10.5,
                 facecolor="#fff2f1", edgecolor=RED, linewidth=1.4,
                 linestyle=(0, (4, 2.4)), zorder=4))
    ax.text(xg, yc + bh / 2 + 8.2,
            "plausibility check added:\ncatches 55%, misses 45%",
            ha="center", va="center", fontsize=10.5, color=RED,
            fontweight="bold", zorder=5, linespacing=1.25)
    ax.plot([xg, xg], [yc + bh / 2, yc + bh / 2 + 3.0], color=RED, lw=1.2, zorder=5)

    # Paper build: headline removed; the caption carries the worked example.
    ax.text(0, 26.5, "Green = stage exercised with the application's own code. "
            "\u201cBOTH measured\u201d: the deployed LLM extractor was compared "
            "against a deterministic parser on identical OCR text.",
            ha="left", va="top", fontsize=9.8, color=INK2, style="italic")
    ax.text(L, 89.5, "VISION", fontsize=11, color="#2a78d6",
            fontweight="bold", ha="left", va="center")
    ax.text(R, 89.5, "LANGUAGE", fontsize=11, color=RED,
            fontweight="bold", ha="right", va="center")

    fig.tight_layout(pad=0.2)
    fig.savefig(out / "fig1_architecture.pdf", bbox_inches="tight")
    fig.savefig(out / "fig1_architecture.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    main()
