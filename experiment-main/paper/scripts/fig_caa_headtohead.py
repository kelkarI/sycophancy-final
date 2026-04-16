"""
Paper figure — Objective 2 headline (CAA head-to-head).

Compares, at each vector's tune-locked best coefficient on the test split:
    baseline (coef 0)
    assistant_axis
    CAA (sign-convention flipped coefficient)
    best critical role
    best conformist role (for contrast)

Bars are Δlogit vs baseline. Error bars from multi-seed aggregate when present,
else single-seed bootstrap widths from statistical_tests_test.json.

Also produces an efficiency companion panel:
    sycophancy_reduction / |coefficient| at the best coefficient, across
    assistant_axis / CAA / best role.

Reads:
    results/sycophancy_rates_test.json
    results/best_coefs_tune.json
    results/statistical_tests_test.json
    results/multiseed_aggregate_test.json  (optional)

Writes:
    paper/figures/figure_2_caa_headtohead.pdf + .png
    paper/tables/figure_2_caa_headtohead.csv
"""
import os
import sys

import numpy as np

_THIS = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _THIS)
from _paper_style import (
    plt, RESULTS_DIR, load_json, maybe_load_json, save_fig, write_csv,
    CRITICAL_ROLES, CONFORMIST_ROLES, condition_color, short_label,
    error_bar_for,
)


def main():
    rates = load_json(f"{RESULTS_DIR}/sycophancy_rates_test.json")
    best  = load_json(f"{RESULTS_DIR}/best_coefs_tune.json")["best_coefs"]

    baseline_logit = float(rates["assistant_axis"]["0.0"]["mean_syc_logit"])

    def delta_for(cond):
        coef = float(best.get(cond, 0.0))
        k = f"{coef}"
        cell = rates.get(cond, {}).get(k)
        if not cell:
            return None
        mean_logit, std_logit, src = error_bar_for(cond, "test")
        if mean_logit is None:
            mean_logit = cell["mean_syc_logit"]; std_logit = 0.0; src = "single-seed"
        return {
            "condition": cond,
            "coef": coef,
            "logit": mean_logit,
            "delta": mean_logit - baseline_logit,
            "std": std_logit,
            "source": src,
        }

    # Choose the best critical role: lowest mean_logit (most reduction)
    crit_deltas = [delta_for(c) for c in CRITICAL_ROLES]
    crit_deltas = [d for d in crit_deltas if d]
    if not crit_deltas:
        raise SystemExit("No critical role results found.")
    best_crit = min(crit_deltas, key=lambda d: d["logit"])
    # Best conformist: highest mean_logit (most increase)
    conf_deltas = [delta_for(c) for c in CONFORMIST_ROLES]
    conf_deltas = [d for d in conf_deltas if d]
    best_conf = max(conf_deltas, key=lambda d: d["logit"]) if conf_deltas else None

    axis_d = delta_for("assistant_axis")
    caa_d  = delta_for("caa")
    bars = [axis_d, caa_d, best_crit]
    if best_conf:
        bars.append(best_conf)

    # --- Layout: 2 panels ---
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.6), gridspec_kw={"width_ratios": [3, 2]})

    # Panel A: Δlogit bars
    labels = [short_label(d["condition"]) for d in bars]
    deltas = [d["delta"] for d in bars]
    stds   = [d["std"] for d in bars]
    colors = [condition_color(d["condition"]) for d in bars]
    x = np.arange(len(bars))
    ax1.bar(x, deltas, yerr=stds, color=colors, edgecolor="black",
            linewidth=0.6, capsize=3)
    for i, d in enumerate(bars):
        ax1.annotate(f"c={int(d['coef']):+d}", (x[i], d["delta"]),
                     ha="center",
                     va="bottom" if d["delta"] >= 0 else "top",
                     xytext=(0, 2 if d["delta"] >= 0 else -2),
                     textcoords="offset points", fontsize=7)
    ax1.axhline(0, color="black", lw=0.7)
    ax1.set_xticks(x)
    ax1.set_xticklabels(labels, rotation=20, ha="right")
    ax1.set_ylabel(r"$\Delta$ sycophancy logit vs baseline")
    ax1.set_title("Head-to-head: assistant axis, CAA, best role")

    # Panel B: efficiency — reduction per unit |coef|
    eff_rows = []
    for d in bars:
        if d["coef"] == 0:
            continue
        reduction = -d["delta"]  # positive = sycophancy went down
        eff = reduction / abs(d["coef"])
        eff_rows.append((d["condition"], eff, reduction, abs(d["coef"])))
    elabels = [short_label(r[0]) for r in eff_rows]
    evalues = [r[1] for r in eff_rows]
    ecolors = [condition_color(r[0]) for r in eff_rows]
    ex = np.arange(len(eff_rows))
    ax2.bar(ex, evalues, color=ecolors, edgecolor="black", linewidth=0.6)
    ax2.axhline(0, color="black", lw=0.7)
    ax2.set_xticks(ex)
    ax2.set_xticklabels(elabels, rotation=20, ha="right")
    ax2.set_ylabel(r"Reduction / |coefficient|  (×$10^{-4}$)")
    ax2.set_title("Efficiency per unit steering magnitude")
    # Rescale y labels for readability
    ticks = ax2.get_yticks()
    ax2.set_yticks(ticks)
    ax2.set_yticklabels([f"{t*1e4:.2f}" for t in ticks])

    fig.suptitle("Figure 2 — CAA head-to-head (test split, tune-locked coefs)",
                 y=1.02, fontsize=11)
    fig.text(0.01, -0.02,
             "Note: CAA points FROM honest TOWARD sycophantic, so its 'best' "
             "coefficient is negative by convention. Δlogit is reported after "
             "applying the sign; negative Δ = reduced sycophancy.",
             fontsize=7, color="#555555")

    save_fig(fig, "figure_2_caa_headtohead")

    rows = [
        [d["condition"], short_label(d["condition"]), d["coef"],
         baseline_logit, d["logit"], d["delta"], d["std"], d["source"]]
        for d in bars
    ]
    write_csv(
        rows,
        ["condition", "label", "coef_locked_from_tune",
         "baseline_logit", "best_logit_test", "delta_logit", "std_logit",
         "error_source"],
        "figure_2_caa_headtohead",
    )


if __name__ == "__main__":
    main()
