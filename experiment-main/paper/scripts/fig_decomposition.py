"""
Paper figure — Objective 3 headline (behavioural CAA decomposition).

For each of the 10 non-CAA real conditions, evaluate three steered versions
at the role's tune-locked best coefficient:

    (a) full role direction                                 -> Δlogit_full
    (b) unit-normalised CAA-aligned component of the role   -> Δlogit_caa
    (c) unit-normalised residual of the role                -> Δlogit_resid

Each is reported as Δ-from-baseline. The paper claim is: if (b) ≈ (a) and
(c) ≈ 0, the role's effect lives entirely along the CAA direction. If (c) ≈ (a)
and (b) ≈ 0, the role works through something orthogonal to CAA. Mixed cases
are interesting too.

PRECISION NOTE (carried from user guidance):
    We steer with the UNIT-NORMALISED CAA-aligned component and residual of
    each role, at matched coefficient. We do NOT preserve the original norms
    of the decomposition (which would trivially split the role's steering
    magnitude between the two pieces). This isolates the DIRECTION question
    from the MAGNITUDE question.

Reads:
    results/sycophancy_rates_test.json          -> full-role Δlogit
    results/best_coefs_tune.json                -> locked coefs
    results/decomposition_eval_test.json        -> component/residual rows
    vectors/steering/caa_decomposition.json     -> cos(role, CAA) for sort order

Writes:
    paper/figures/figure_3_decomposition.pdf + .png
    paper/tables/figure_3_decomposition.csv
"""
import os
import statistics as st
import sys

import numpy as np

_THIS = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _THIS)
from _paper_style import (
    plt, ROLE_NAMES, RESULTS_DIR, VECTORS_DIR,
    load_json, save_fig, write_csv,
    condition_color, short_label, error_bar_for,
)


def main():
    rates = load_json(f"{RESULTS_DIR}/sycophancy_rates_test.json")
    best  = load_json(f"{RESULTS_DIR}/best_coefs_tune.json")["best_coefs"]
    decomp = load_json(f"{VECTORS_DIR}/caa_decomposition.json")
    try:
        decomp_eval = load_json(f"{RESULTS_DIR}/decomposition_eval_test.json")
    except FileNotFoundError:
        raise SystemExit("decomposition_eval_test.json not found. Run "
                         "scripts/02c_evaluate_decomposition.py first.")
    per_row = decomp_eval["per_row"]

    baseline_logit = float(rates["assistant_axis"]["0.0"]["mean_syc_logit"])

    # Order conditions by |cos(role, CAA)| descending (most CAA-aligned first,
    # excluding caa itself). "assistant_axis" is a reference.
    targets = [c for c in ["assistant_axis"] + list(ROLE_NAMES)
               if c in decomp and c != "caa"]
    targets.sort(key=lambda c: -abs(decomp[c]["cosine_with_caa"]))

    def mean_syc_logit_at(cond_name):
        rs = [r["syc_logit"] for r in per_row if r["condition"] == cond_name]
        return float(st.mean(rs)) if rs else None

    rows = []
    for cond in targets:
        coef = float(best.get(cond, 0.0))
        k = f"{coef}"
        full_cell = rates.get(cond, {}).get(k)
        if not full_cell:
            continue
        # Prefer multi-seed for the "full" bar if available
        full_mean, full_std, full_src = error_bar_for(cond, "test")
        if full_mean is None:
            full_mean = full_cell["mean_syc_logit"]; full_std = 0.0; full_src = "single-seed"
        comp_mean = mean_syc_logit_at(f"{cond}_caa_component")
        resid_mean = mean_syc_logit_at(f"{cond}_residual")
        if comp_mean is None or resid_mean is None:
            continue
        rows.append({
            "cond": cond,
            "label": short_label(cond),
            "coef": coef,
            "cos_caa": float(decomp[cond]["cosine_with_caa"]),
            "full_delta":  full_mean - baseline_logit,
            "full_std":    full_std,
            "comp_delta":  comp_mean - baseline_logit,
            "resid_delta": resid_mean - baseline_logit,
            "error_source": full_src,
        })

    # --- Plot ---
    n = len(rows)
    fig, ax = plt.subplots(figsize=(max(8, 0.9 * n + 2), 5.2))
    x = np.arange(n)
    w = 0.26
    def color(shade, base):
        return base if shade == 0 else None
    full_vals = [r["full_delta"] for r in rows]
    comp_vals = [r["comp_delta"] for r in rows]
    resid_vals = [r["resid_delta"] for r in rows]
    base_colors = [condition_color(r["cond"]) for r in rows]
    ax.bar(x - w,   full_vals, width=w, yerr=[r["full_std"] for r in rows],
           color=base_colors, edgecolor="black", linewidth=0.6, capsize=2,
           label="full role direction")
    ax.bar(x,       comp_vals, width=w, color=base_colors, alpha=0.55,
           edgecolor="black", linewidth=0.6, hatch="////", label="CAA-aligned component (unit)")
    ax.bar(x + w,   resid_vals, width=w, color=base_colors, alpha=0.55,
           edgecolor="black", linewidth=0.6, hatch="....",  label="residual (unit)")

    for i, r in enumerate(rows):
        ax.annotate(f"cos={r['cos_caa']:+.2f}",
                    (x[i], min(r["full_delta"], r["comp_delta"], r["resid_delta"])),
                    ha="center", va="top",
                    xytext=(0, -10), textcoords="offset points",
                    fontsize=7, color="#444444")

    ax.axhline(0, color="black", lw=0.7)
    ax.set_xticks(x)
    ax.set_xticklabels([r["label"] for r in rows], rotation=20, ha="right")
    ax.set_ylabel(r"$\Delta$ sycophancy logit vs baseline")
    ax.set_title("Figure 3 — Behavioural CAA decomposition "
                 "(unit-normalised components at matched coef)")
    ax.legend(loc="best", ncol=3, frameon=True)
    fig.text(0.01, -0.02,
             "Each role is decomposed into its unit-normalised CAA-aligned component "
             "and unit-normalised residual (not the raw-norm components); both are "
             "steered at the role's tune-locked best coefficient. Roles ordered by "
             "|cos(role, CAA)| descending.",
             fontsize=7, color="#555555")

    save_fig(fig, "figure_3_decomposition")

    csv_rows = []
    for r in rows:
        # Fraction of full Δlogit carried by each piece (sign-consistent).
        # Guard against divide-by-near-zero.
        denom = r["full_delta"]
        frac_comp = r["comp_delta"] / denom if abs(denom) > 1e-6 else float("nan")
        frac_resid = r["resid_delta"] / denom if abs(denom) > 1e-6 else float("nan")
        csv_rows.append([
            r["cond"], r["label"], r["coef"], r["cos_caa"],
            r["full_delta"], r["comp_delta"], r["resid_delta"],
            frac_comp, frac_resid, r["error_source"],
        ])
    write_csv(
        csv_rows,
        ["condition", "label", "coef_locked_from_tune", "cosine_role_caa",
         "delta_full", "delta_caa_component", "delta_residual",
         "fraction_from_caa_component", "fraction_from_residual",
         "error_source"],
        "figure_3_decomposition",
    )


if __name__ == "__main__":
    main()
