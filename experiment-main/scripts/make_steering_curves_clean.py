"""Filtered steering-curve figure (kept conditions only).

The default `fig1_steering_curves.png` produced by 03_analysis.py plots
every condition in CONDITIONS_REAL (assistant_axis + 5 critical + 4
conformist + CAA + 3 residuals) on a single axis, which is unreadable.
This script re-draws the same sweep using only the "clean" subset used
in the sycophancy-clean-results paper package:

  critical   : skeptic, devils_advocate, judge
  conformist : peacekeeper, pacifist, collaborator
  targeted   : caa
  null       : random mean (n=10) with +/- std band
  reference  : baseline (coef = 0)

Reads `results/sycophancy_rates_test.json` (already aggregated across
seeds by run_multiseed.py), so values match the upstream fig1 exactly
for every kept condition.

Writes `figures/fig1_steering_curves_clean.png`.
"""
import json
import os
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from config import ROOT, TARGET_LAYER

FIG_DIR = Path(os.environ.get("EXPERIMENT_ROOT", ROOT)) / "figures"
RES_DIR = Path(os.environ.get("EXPERIMENT_ROOT", ROOT)) / "results"
if not RES_DIR.exists():
    RES_DIR = Path(__file__).resolve().parent.parent / "results"
    FIG_DIR = Path(__file__).resolve().parent.parent / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)

CRITICAL_KEPT   = ["skeptic", "devils_advocate", "judge"]
CONFORMIST_KEPT = ["peacekeeper", "pacifist", "collaborator"]
KEPT_ORDER      = ["caa"] + CRITICAL_KEPT + CONFORMIST_KEPT
N_RANDOM        = 10
RANDOM_CONDS    = [f"random_{i}" for i in range(N_RANDOM)]

# Colorblind-safe palette matching sycophancy-clean-results/scripts/_style.py:
# critical = blues, conformist = oranges, CAA = dark gray, random = light gray.
PALETTE = {
    "caa":             "#4d4d4d",
    "skeptic":         "#08519c",
    "devils_advocate": "#2171b5",
    "judge":           "#4292c6",
    "peacekeeper":     "#d94801",
    "pacifist":        "#f16913",
    "collaborator":    "#fd8d3c",
    "random":          "#bdbdbd",
}
LABELS = {
    "caa":             "CAA (targeted)",
    "skeptic":         "Skeptic",
    "devils_advocate": "Devil's Advocate",
    "judge":           "Judge",
    "peacekeeper":     "Peacekeeper",
    "pacifist":        "Pacifist",
    "collaborator":    "Collaborator",
}


def baseline_values(rates):
    cond = next(c for c in rates if not c.startswith("random_"))
    cell = rates[cond]["0.0"]
    return float(cell["mean_syc_logit"]), float(cell["binary_rate"])


def series(rates, cond, coeffs, metric):
    ys = []
    for c in coeffs:
        k = f"{c}" if c != 0.0 else "0.0"
        cell = rates[cond].get(k)
        if cell is None:
            ys.append(np.nan)
            continue
        ys.append(float(cell["binary_rate"]) * 100 if metric == "rate"
                  else float(cell["mean_syc_logit"]))
    return ys


def random_band(rates, coeffs, metric):
    means, stds = [], []
    for c in coeffs:
        k = f"{c}" if c != 0.0 else "0.0"
        vs = []
        for rc in RANDOM_CONDS:
            cell = rates.get(rc, {}).get(k)
            if cell is None:
                continue
            vs.append(float(cell["binary_rate"]) * 100 if metric == "rate"
                      else float(cell["mean_syc_logit"]))
        means.append(float(np.mean(vs)) if vs else np.nan)
        stds.append(float(np.std(vs)) if vs else 0.0)
    return means, stds


def plot_panel(ax, rates, metric, ylabel, title, put_legend):
    cond_any = next(c for c in rates if not c.startswith("random_"))
    coeffs = sorted((float(k) for k in rates[cond_any]))
    for c in KEPT_ORDER:
        if c not in rates:
            continue
        ax.plot(coeffs, series(rates, c, coeffs, metric),
                color=PALETTE[c], marker="o", markersize=4, lw=1.7,
                label=LABELS[c])
    rm, rs = random_band(rates, coeffs, metric)
    ax.plot(coeffs, rm, color=PALETTE["random"], ls="--", marker="s",
            markersize=3, lw=1.4, label=f"Random mean (n={N_RANDOM})")
    ax.fill_between(coeffs,
                    [m - s for m, s in zip(rm, rs)],
                    [m + s for m, s in zip(rm, rs)],
                    color=PALETTE["random"], alpha=0.22, linewidth=0)
    bl_logit, bl_rate = baseline_values(rates)
    ax.axhline(bl_rate * 100 if metric == "rate" else bl_logit,
               ls=":", color="black", alpha=0.8, lw=1.0,
               label="baseline = " + (f"{bl_rate*100:.1f}%" if metric == "rate"
                                      else f"{bl_logit:+.2f}"))
    ax.set_xlabel("Steering coefficient")
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.grid(True, alpha=0.3, linestyle=":")
    if put_legend:
        ax.legend(loc="best", fontsize=8, ncol=2, framealpha=0.9)


def main():
    rates_path = RES_DIR / "sycophancy_rates_test.json"
    rates = json.loads(rates_path.read_text())
    fig, (ax_a, ax_b) = plt.subplots(2, 1, figsize=(10, 9))
    plot_panel(ax_a, rates, "rate",
               "Sycophancy rate (%)",
               f"Binary sycophancy rate vs steering coefficient "
               f"(kept conditions, L{TARGET_LAYER}, test split)",
               put_legend=True)
    plot_panel(ax_b, rates, "logit",
               r"Mean sycophancy logit  $\log p(\mathrm{syc}) - \log p(\mathrm{hon})$",
               "Continuous sycophancy preference vs steering coefficient "
               "(kept conditions)",
               put_legend=False)
    plt.tight_layout()
    out = FIG_DIR / "fig1_steering_curves_clean.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"saved {out}")


if __name__ == "__main__":
    main()
