"""Figure 3 for the paper: corruption of an already-abnormal value is far more
likely to leave the abnormality flag unchanged.

The point is structural. An abnormality flag is a threshold quantisation, so a
value that already sits outside its reference range can be corrupted further
without crossing back over the threshold. Corruption of a normal value has to
cross one to go unnoticed, and usually does not.

Reads results_multidoc/safeguard.csv, which carries one row per analyte reading
with the truth flag (tf), the extracted flag (ef) and whether the reading was
silent (flag unchanged despite a wrong value).

Output is PDF for direct \\includegraphics.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from scipy.stats import fisher_exact

INK, INK2, MUTED = "#0b0b0b", "#52514e", "#8b8a85"
RED, PALE = "#b3251f", "#dde3ee"

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 9.5,
    "axes.labelsize": 9.5,
    "xtick.labelsize": 9,
    "ytick.labelsize": 10,
    "axes.edgecolor": MUTED,
    "axes.linewidth": 0.8,
    "axes.facecolor": "white",
    "figure.facecolor": "white",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "xtick.color": INK2, "ytick.color": INK2,
    "axes.labelcolor": INK, "text.color": INK,
    "pdf.fonttype": 42,
})


def load(results: Path) -> pd.DataFrame:
    s = pd.read_csv(results / "safeguard.csv")
    cor = s[s.status == "corrupted"].copy()
    cor["truth_abnormal"] = cor.tf.fillna("").astype(str).str.strip().ne("")
    return cor


def build(cor: pd.DataFrame, out: Path) -> None:
    rows = []
    for abnormal, label in [(True, "True value already\noutside reference range"),
                            (False, "True value within\nreference range")]:
        g = cor[cor.truth_abnormal == abnormal]
        silent = int(g.silent.sum())
        rows.append((label, silent, len(g) - silent, len(g)))

    tab = [[rows[0][1], rows[0][2]], [rows[1][1], rows[1][2]]]
    odds, p = fisher_exact(tab)

    fig, ax = plt.subplots(figsize=(6.4, 2.05))
    y = [1, 0]
    for i, (label, silent, seen, n) in enumerate(rows):
        frac = silent / n
        ax.barh(y[i], frac, height=0.52, color=RED)
        ax.barh(y[i], 1 - frac, left=frac, height=0.52, color=PALE)
        lab = f"{silent} of {n}  ({frac*100:.1f}%)"
        if frac >= 0.35:
            ax.text(frac / 2, y[i], lab, ha="center", va="center",
                    color="white", fontsize=10, fontweight="bold")
        else:
            # Too narrow to hold the label; set it just outside the bar.
            ax.text(frac + 0.015, y[i], lab, ha="left", va="center",
                    color=RED, fontsize=10, fontweight="bold")
        ax.text(1 - 0.015, y[i], f"{seen}", ha="right",
                va="center", color=INK2, fontsize=9.5)

    ax.set_yticks(y)
    ax.set_yticklabels([r[0] for r in rows])
    ax.set_xlim(0, 1)
    ax.set_xticks([0, 0.25, 0.5, 0.75, 1.0])
    ax.set_xticklabels(["0%", "25%", "50%", "75%", "100%"])
    ax.set_xlabel("Share of that group's corruptions")
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)

    handles = [plt.Rectangle((0, 0), 1, 1, color=RED),
               plt.Rectangle((0, 0), 1, 1, color=PALE)]
    ax.legend(handles,
              ["Flag unchanged (silent)", "Flag changed, error visible to the flagging layer"],
              loc="lower center", bbox_to_anchor=(0.5, -0.62), ncol=2,
              frameon=False, handlelength=1.1, handletextpad=0.5,
              columnspacing=1.4, fontsize=9)

    ax.text(1.0, 1.62, f"Fisher exact p = {p:.1e},  odds ratio {odds:.2f}",
            ha="right", va="bottom", fontsize=9, color=INK2,
            transform=ax.get_yaxis_transform(which="grid"))

    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, format="pdf", bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)
    print(f"wrote {out}")
    print(f"  abnormal: {rows[0][1]}/{rows[0][3]} = {rows[0][1]/rows[0][3]*100:.1f}% silent")
    print(f"  normal  : {rows[1][1]}/{rows[1][3]} = {rows[1][1]/rows[1][3]*100:.1f}% silent")
    print(f"  Fisher p = {p:.3g}, OR = {odds:.2f}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default="../../../poster-experiment/results_multidoc")
    ap.add_argument("--out", default="fig3_mechanism.pdf")
    a = ap.parse_args()
    build(load(Path(a.results)), Path(a.out))
