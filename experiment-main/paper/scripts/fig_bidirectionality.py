"""
Paper figure — Objective 1 headline (bidirectionality).

Critical roles reduce sycophancy; conformist roles increase it; assistant axis
sits between; random controls define the null band. Each condition is
evaluated at its direction-aware best coefficient, locked from the tune split.

Reads:
    results/sycophancy_rates_test.json   # single-seed fall-back
    results/best_coefs_tune.json         # per-condition locked coef
    results/multiseed_aggregate_test.json  # if present, error bars from it

Writes:
    paper/figures/figure_1_bidirectionality.pdf + .png
    paper/tables/figure_1_bidirectionality.csv
"""
import os
import sys

import numpy as np

_THIS = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _THIS)
from _paper_style import (
    plt, RESULTS_DIR, load_json, maybe_load_json, save_fig, write_csv,
    CRITICAL_ROLES, CONFORMIST_ROLES, EXPECTED_DIRECTION,
    condition_color, short_label, error_bar_for,
)


def main():
    rates = load_json(f"{RESULTS_DIR}/sycophancy_rates_test.json")
    best  = load_json(f"{RESULTS_DIR}/best_coefs_tune.json")["best_coefs"]
    agg   = maybe_load_json(f"{RESULTS_DIR}/multiseed_aggregate_test.json")

    # Baseline logit (coef 0 from any condition; axis is canonical)
    baseline_logit = float(rates["assistant_axis"]["0.0"]["mean_syc_logit"])

    # Order: critical (decrease) then axis then caa (both decrease) then conformist (increase)
    order = (list(CRITICAL_ROLES) + ["assistant_axis", "caa"] + list(CONFORMIST_ROLES))

    logits, stds, labels, colors, coefs, src_tags = [], [], [], [], [], []
    for cond in order:
        coef = float(best.get(cond, 0.0))
        k = f"{coef}"
        cell = rates[cond].get(k)
        if not cell:
            continue
        # prefer multi-seed mean/std if present
        mean_logit, std_logit, src = error_bar_for(cond, "test")
        if mean_logit is None:
            mean_logit = cell["mean_syc_logit"]
            std_logit = 0.0
            src = "single-seed"
        logits.append(mean_logit - baseline_logit)  # Δlogit
        stds.append(std_logit)
        labels.append(short_label(cond))
        colors.append(condition_color(cond))
        coefs.append(coef)
        src_tags.append(src)

    # Random null band
    rand_logits_at_best = []
    for i in range(10):
        rc = f"random_{i}"
        if rc in best:
            k = f"{float(best[rc])}"
            cell = rates.get(rc, {}).get(k)
            if cell:
                rand_logits_at_best.append(cell["mean_syc_logit"] - baseline_logit)
    if rand_logits_at_best:
        rand_mean = float(np.mean(rand_logits_at_best))
        rand_std  = float(np.std(rand_logits_at_best))
    else:
        rand_mean = rand_std = 0.0

    fig, ax = plt.subplots(figsize=(10, 5.2))
    x = np.arange(len(labels))
    bars = ax.bar(x, logits, yerr=stds, color=colors, edgecolor="black",
                  linewidth=0.6, capsize=3)
    # Annotate coef inside/above each bar
    for b, co in zip(bars, coefs):
        y = b.get_height()
        ax.annotate(f"c={int(co):+d}",
                    (b.get_x() + b.get_width()/2, y),
                    ha="center",
                    va="bottom" if y >= 0 else "top",
                    xytext=(0, 2 if y >= 0 else -2),
                    textcoords="offset points",
                    fontsize=7)

    # Random-control null band
    ax.axhspan(rand_mean - rand_std, rand_mean + rand_std,
               color="#7f7f7f", alpha=0.12, label=f"random null band (±1 SD, n=10)")
    ax.axhline(rand_mean, color="#7f7f7f", ls="--", lw=0.8)
    ax.axhline(0.0, color="black", lw=0.7)

    # Group separators
    n_crit = len(CRITICAL_ROLES)
    ax.axvline(n_crit - 0.5, color="#333333", lw=0.4, ls=":")
    ax.axvline(n_crit + 2 - 0.5, color="#333333", lw=0.4, ls=":")  # after axis+caa
    ax.text(n_crit/2 - 0.5, ax.get_ylim()[0], "critical roles\n(decrease-expected)",
            ha="center", va="bottom", fontsize=8, color="#444444")
    ax.text(n_crit + 0.5, ax.get_ylim()[0], "axis\n+ CAA", ha="center",
            va="bottom", fontsize=8, color="#444444")
    ax.text(n_crit + 2 + len(CONFORMIST_ROLES)/2 - 0.5, ax.get_ylim()[0],
            "conformist roles\n(increase-expected)",
            ha="center", va="bottom", fontsize=8, color="#444444")

    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=30, ha="right")
    ax.set_ylabel(r"$\Delta$ sycophancy logit vs baseline")
    ax.set_title("Persona-direction bidirectionality on sycophancy "
                 "(test split, tune-locked coefs)")
    err_note = "multi-seed (n_seeds in table)" if agg else "single-seed"
    ax.legend(loc="best")
    fig.text(0.01, 0.01,
             f"Error bars: {err_note}. Coefs locked from tune split. "
             "Random control: mean ± 1 SD across 10 random unit vectors.",
             fontsize=7, color="#555555")

    save_fig(fig, "figure_1_bidirectionality")

    # CSV companion
    rows = []
    for cond in order:
        coef = float(best.get(cond, 0.0))
        k = f"{coef}"
        cell = rates[cond].get(k)
        if not cell:
            continue
        mean_logit, std_logit, src = error_bar_for(cond, "test")
        if mean_logit is None:
            mean_logit = cell["mean_syc_logit"]; std_logit = 0.0; src = "single-seed"
        rows.append([
            cond, short_label(cond), EXPECTED_DIRECTION.get(cond, "unsigned"),
            coef, baseline_logit, mean_logit, mean_logit - baseline_logit,
            std_logit, src,
        ])
    write_csv(
        rows,
        ["condition", "label", "expected_direction", "coef_locked_from_tune",
         "baseline_logit", "best_logit_test", "delta_logit", "std_logit",
         "error_source"],
        "figure_1_bidirectionality",
    )


if __name__ == "__main__":
    main()
