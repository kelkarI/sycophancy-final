"""
Paper figure — overcorrection taxonomy.

Per-condition stacked bar chart over the six response categories on the
structured true-vs-false claim probes:

    AGREE_CORRECT, DISAGREE_CORRECT  -> "correct" (stacked green shades)
    AGREE_WRONG                       -> sycophantic error (red)
    DISAGREE_WRONG                    -> overcorrection (orange)
    HEDGE                             -> grey
    REFUSE                            -> light grey

Two panels: TRUE claims and FALSE claims side by side. This is the figure that
distinguishes "reducing sycophancy" from "becoming incoherently contrarian."

Reads:
    results/over_correction_eval_test.json
    (falls back to _all or no-suffix if that is absent)

Writes:
    paper/figures/figure_4_overcorrection_taxonomy.pdf + .png
    paper/tables/figure_4_overcorrection_taxonomy.csv
"""
import os
import sys

import numpy as np

_THIS = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _THIS)
from _paper_style import (
    plt, RESULTS_DIR, load_json, maybe_load_json, save_fig, write_csv,
    condition_order_for_paper, short_label, condition_class,
)


def load_overcorrection():
    for name in [
        "over_correction_eval_test.json",
        "over_correction_eval_all.json",
        "over_correction_eval.json",
    ]:
        p = f"{RESULTS_DIR}/{name}"
        if os.path.exists(p):
            return load_json(p), name
    raise SystemExit("No over_correction_eval_*.json found; run "
                     "scripts/over_correction_check.py first.")


# Color scheme fixed per category
CAT_COLORS = {
    "AGREE_CORRECT":    "#2ca02c",
    "DISAGREE_CORRECT": "#1f9e1f",
    "HEDGE":            "#9e9e9e",
    "REFUSE":           "#cccccc",
    "AGREE_WRONG":      "#d62728",
    "DISAGREE_WRONG":   "#ff7f0e",
}
CAT_ORDER_TRUE  = ["AGREE_CORRECT", "DISAGREE_WRONG", "HEDGE", "REFUSE"]
CAT_ORDER_FALSE = ["DISAGREE_CORRECT", "AGREE_WRONG", "HEDGE", "REFUSE"]

CAT_LABELS = {
    "AGREE_CORRECT":    "agree (true claim) ✓",
    "DISAGREE_CORRECT": "disagree (false claim) ✓",
    "AGREE_WRONG":      "agree (false claim) — sycophantic error",
    "DISAGREE_WRONG":   "disagree (true claim) — overcorrection",
    "HEDGE":            "hedge",
    "REFUSE":           "refuse",
}


def split_results(per_probe):
    """Separate per-probe results into TRUE and FALSE, keyed by condition."""
    out = {"TRUE": {}, "FALSE": {}}
    for r in per_probe:
        key = "TRUE" if r["true_claim"] else "FALSE"
        cond = r["condition"]
        out[key].setdefault(cond, []).append(r["category"])
    return out


def stacked_panel(ax, per_cond_cats, conditions, cat_order, title):
    counts = {c: {cat: 0 for cat in cat_order} for c in conditions}
    for c in conditions:
        cats = per_cond_cats.get(c, [])
        for cat in cats:
            if cat in counts[c]:
                counts[c][cat] += 1
    n = len(conditions)
    x = np.arange(n)
    bottom = np.zeros(n)
    for cat in cat_order:
        vals = np.array([counts[c][cat] for c in conditions], dtype=float)
        ax.bar(x, vals, bottom=bottom,
               color=CAT_COLORS[cat], edgecolor="black", linewidth=0.4,
               label=CAT_LABELS[cat])
        bottom += vals
    ax.set_xticks(x)
    ax.set_xticklabels([short_label(c) for c in conditions], rotation=30, ha="right")
    ax.set_ylabel("# probes (out of 8)")
    ax.set_title(title)
    # Small counts for sycophantic error / overcorrection on top of each bar
    for i, c in enumerate(conditions):
        errs = counts[c].get("AGREE_WRONG", 0) + counts[c].get("DISAGREE_WRONG", 0)
        if errs > 0:
            ax.text(x[i], bottom[i] + 0.1, f"err={errs}", ha="center",
                    va="bottom", fontsize=7, color="#333333")


def main():
    data, src_name = load_overcorrection()
    per_probe = data["per_probe_results"]
    conds_present = [c for c in ["baseline"] + condition_order_for_paper()
                     if c in {r["condition"] for r in per_probe}]

    split = split_results(per_probe)

    fig, (axT, axF) = plt.subplots(1, 2, figsize=(14, 5.2), sharey=True)
    stacked_panel(axT, split["TRUE"],  conds_present, CAT_ORDER_TRUE,
                  "Claims that are TRUE (8 probes)")
    stacked_panel(axF, split["FALSE"], conds_present, CAT_ORDER_FALSE,
                  "Claims that are FALSE (8 probes)")
    axT.legend(loc="upper right", fontsize=7, frameon=True)
    axF.legend(loc="upper right", fontsize=7, frameon=True)

    fig.suptitle("Figure 4 — Overcorrection taxonomy under steering "
                 "(per-condition best coef, test split)",
                 y=1.02, fontsize=11)
    fig.text(0.01, -0.02,
             f"Source: {src_name}. Categories from keyword classifier on "
             "generated text; see over_correction_check.py for heuristics.",
             fontsize=7, color="#555555")

    save_fig(fig, "figure_4_overcorrection_taxonomy")

    # CSV: counts + rates
    rows = []
    for kind in ("TRUE", "FALSE"):
        for c in conds_present:
            cats = split[kind].get(c, [])
            row = [c, short_label(c), condition_class(c), kind, len(cats)]
            for cat in ["AGREE_CORRECT", "DISAGREE_CORRECT", "AGREE_WRONG",
                        "DISAGREE_WRONG", "HEDGE", "REFUSE"]:
                row.append(sum(1 for x in cats if x == cat))
            rows.append(row)
    write_csv(
        rows,
        ["condition", "label", "class", "claim_type", "n_probes",
         "n_AGREE_CORRECT", "n_DISAGREE_CORRECT",
         "n_AGREE_WRONG", "n_DISAGREE_WRONG", "n_HEDGE", "n_REFUSE"],
        "figure_4_overcorrection_taxonomy",
    )


if __name__ == "__main__":
    main()
