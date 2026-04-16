"""
Paper figure — PCA of steering vectors.

2D PCA over all unit-normed steering vectors, with markers distinguishing the
class (axis, CAA, critical, conformist, random) and annotations showing Δlogit
vs baseline (with multi-seed std when present).

Reads:
    vectors/steering/*_unit.pt
    results/sycophancy_rates_test.json
    results/best_coefs_tune.json
    results/multiseed_aggregate_test.json  (optional)
Writes:
    paper/figures/figure_6_pca_persona_space.pdf + .png
"""
import os
import sys

import numpy as np
import torch

_THIS = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _THIS)
from _paper_style import (
    plt, RESULTS_DIR, VECTORS_DIR, load_json, save_fig,
    CRITICAL_ROLES, CONFORMIST_ROLES, condition_color, short_label,
    error_bar_for, N_RANDOM_VECTORS,
)
try:
    from sklearn.decomposition import PCA
except ImportError:
    raise SystemExit("scikit-learn is required for the PCA figure")


MARKER_FOR = {
    "assistant_axis": ("o", 130, "axis"),
    "caa":            ("D", 130, "CAA"),
}


def class_marker(cond):
    if cond in MARKER_FOR:
        return MARKER_FOR[cond]
    if cond in CRITICAL_ROLES:
        return ("o", 95, "critical")
    if cond in CONFORMIST_ROLES:
        return ("s", 95, "conformist")
    if cond.startswith("random_"):
        return ("x", 70, "random")
    return ("o", 70, "other")


def main():
    rates = load_json(f"{RESULTS_DIR}/sycophancy_rates_test.json")
    best  = load_json(f"{RESULTS_DIR}/best_coefs_tune.json")["best_coefs"]
    baseline_logit = float(rates["assistant_axis"]["0.0"]["mean_syc_logit"])

    conds = (["assistant_axis", "caa"]
             + list(CRITICAL_ROLES) + list(CONFORMIST_ROLES)
             + [f"random_{i}" for i in range(min(N_RANDOM_VECTORS, 10))])

    vecs, labels_present = [], []
    for c in conds:
        p = f"{VECTORS_DIR}/{c}_unit.pt"
        if not os.path.exists(p):
            continue
        v = torch.load(p, weights_only=False, map_location="cpu").float().numpy()
        vecs.append(v)
        labels_present.append(c)
    if len(vecs) < 3:
        raise SystemExit("Too few vectors for PCA.")

    pca = PCA(n_components=2)
    coords = pca.fit_transform(np.stack(vecs))

    fig, ax = plt.subplots(figsize=(10, 7.2))
    legend_handles = {}
    for i, c in enumerate(labels_present):
        marker, size, cls = class_marker(c)
        col = condition_color(c)
        sc = ax.scatter(coords[i, 0], coords[i, 1], c=col, s=size,
                        marker=marker, edgecolors="black", linewidth=0.5,
                        zorder=5 if not c.startswith("random_") else 3)
        legend_handles.setdefault(cls, sc)

        # Annotation: Δlogit at best coef
        delta_txt = ""
        if c in best:
            k = f"{float(best[c])}"
            cell = rates.get(c, {}).get(k)
            if cell:
                m, s, _src = error_bar_for(c, "test")
                if m is None:
                    m = cell["mean_syc_logit"]; s = 0.0
                d = m - baseline_logit
                if s and s > 0:
                    delta_txt = f"  Δ={d:+.2f}±{s:.2f}"
                else:
                    delta_txt = f"  Δ={d:+.2f}"
        ax.annotate(f"{short_label(c)}{delta_txt}",
                    (coords[i, 0], coords[i, 1]),
                    xytext=(8, 6), textcoords="offset points",
                    fontsize=8, color="#333333")

    ax.axhline(0, color="black", lw=0.4, alpha=0.5)
    ax.axvline(0, color="black", lw=0.4, alpha=0.5)
    ax.set_xlabel(f"PC1 ({pca.explained_variance_ratio_[0]*100:.1f}% variance)")
    ax.set_ylabel(f"PC2 ({pca.explained_variance_ratio_[1]*100:.1f}% variance)")
    ax.set_title("Figure 6 — PCA of steering vectors in persona space\n"
                 "(annotations: Δ sycophancy logit vs baseline at tune-locked best coef)")
    ax.legend(legend_handles.values(), legend_handles.keys(),
              loc="best", frameon=True)

    save_fig(fig, "figure_6_pca_persona_space")


if __name__ == "__main__":
    main()
