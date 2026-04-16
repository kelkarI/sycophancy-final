"""
Paper figure — sycophancy rate and logit as a function of steering coefficient.

Restyle of the original fig1 with multi-seed shading when
multiseed_aggregate_test.json is present, and with the random controls shown
as a single ±1 SD band across the 10 random vectors.

Reads:
    results/sycophancy_rates_test.json
    results/multiseed_aggregate_test.json  (optional)
Writes:
    paper/figures/figure_supp_steering_curves.pdf + .png
"""
import os
import sys

import numpy as np

_THIS = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _THIS)
from _paper_style import (
    plt, RESULTS_DIR, load_json, maybe_load_json, save_fig,
    CRITICAL_ROLES, CONFORMIST_ROLES, condition_color, short_label,
    N_RANDOM_VECTORS,
)


def main():
    rates = load_json(f"{RESULTS_DIR}/sycophancy_rates_test.json")
    coeffs = sorted(set(
        float(k) for cond_rates in rates.values() for k in cond_rates.keys()
    ))

    fig, (ax_r, ax_l) = plt.subplots(2, 1, figsize=(11, 9))

    real = ["assistant_axis", "caa"] + list(CRITICAL_ROLES) + list(CONFORMIST_ROLES)
    for cond in real:
        if cond not in rates:
            continue
        ys_r, ys_l = [], []
        for c in coeffs:
            k = f"{c}" if c != 0.0 else "0.0"
            cell = rates[cond].get(k)
            if not cell:
                ys_r.append(None); ys_l.append(None); continue
            ys_r.append(cell["binary_rate"] * 100)
            ys_l.append(cell["mean_syc_logit"])
        style = dict(color=condition_color(cond), marker="o", markersize=3.5,
                     linewidth=1.1, label=short_label(cond))
        if cond == "assistant_axis":
            style.update(linewidth=2.2)
        if cond == "caa":
            style.update(linewidth=1.8, linestyle="--")
        if cond in CONFORMIST_ROLES:
            style.update(linestyle=":")
        ax_r.plot(coeffs, ys_r, **style)
        ax_l.plot(coeffs, ys_l, **style)

    # Random band
    rand_rates, rand_logits = [], []
    for c in coeffs:
        k = f"{c}" if c != 0.0 else "0.0"
        rs = [rates[f"random_{i}"][k]["binary_rate"] * 100
              for i in range(N_RANDOM_VECTORS)
              if f"random_{i}" in rates and k in rates[f"random_{i}"]]
        ls = [rates[f"random_{i}"][k]["mean_syc_logit"]
              for i in range(N_RANDOM_VECTORS)
              if f"random_{i}" in rates and k in rates[f"random_{i}"]]
        rand_rates.append((np.mean(rs), np.std(rs)) if rs else (None, None))
        rand_logits.append((np.mean(ls), np.std(ls)) if ls else (None, None))

    rr_m = [x[0] for x in rand_rates]; rr_s = [x[1] for x in rand_rates]
    rl_m = [x[0] for x in rand_logits]; rl_s = [x[1] for x in rand_logits]
    ax_r.plot(coeffs, rr_m, color="#7f7f7f", ls="--", marker="s", markersize=3,
              label=f"random mean (n={N_RANDOM_VECTORS})")
    ax_r.fill_between(coeffs,
                      [m - s if m is not None else None for m, s in zip(rr_m, rr_s)],
                      [m + s if m is not None else None for m, s in zip(rr_m, rr_s)],
                      color="#7f7f7f", alpha=0.12)
    ax_l.plot(coeffs, rl_m, color="#7f7f7f", ls="--", marker="s", markersize=3,
              label=f"random mean (n={N_RANDOM_VECTORS})")
    ax_l.fill_between(coeffs,
                      [m - s if m is not None else None for m, s in zip(rl_m, rl_s)],
                      [m + s if m is not None else None for m, s in zip(rl_m, rl_s)],
                      color="#7f7f7f", alpha=0.12)

    baseline_rate = float(rates["assistant_axis"]["0.0"]["binary_rate"] * 100)
    baseline_logit = float(rates["assistant_axis"]["0.0"]["mean_syc_logit"])
    ax_r.axhline(baseline_rate, color="black", ls=":", lw=1, label="baseline")
    ax_l.axhline(baseline_logit, color="black", ls=":", lw=1, label="baseline")
    ax_l.axhline(0, color="black", lw=0.5, alpha=0.6)

    ax_r.set_xlabel("steering coefficient")
    ax_r.set_ylabel("sycophancy rate (%)")
    ax_r.set_title("Supplementary — steering coefficient sweep, sycophancy rate (test split)")
    ax_r.legend(loc="best", fontsize=8, ncol=2, frameon=True)

    ax_l.set_xlabel("steering coefficient")
    ax_l.set_ylabel(r"mean sycophancy logit  $\log p(\mathrm{syc})-\log p(\mathrm{hon})$")
    ax_l.set_title("Supplementary — steering coefficient sweep, continuous preference (test split)")
    ax_l.legend(loc="best", fontsize=8, ncol=2, frameon=True)

    save_fig(fig, "figure_supp_steering_curves")


if __name__ == "__main__":
    main()
