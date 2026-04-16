"""
Paper figure — cosine-similarity heatmap.

Restyle of the original fig5 with a canonical condition ordering (axis, CAA,
critical, conformist) and a single random control for reference. Omits the
full random 10x10 block.

Reads:
    results/vector_cosine_similarities.json
Writes:
    paper/figures/figure_5_cosine_heatmap.pdf + .png
"""
import os
import sys

import numpy as np

_THIS = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _THIS)
from _paper_style import (
    plt, RESULTS_DIR, load_json, save_fig, short_label,
)


def main():
    cos = load_json(f"{RESULTS_DIR}/vector_cosine_similarities.json")
    names = cos["names"]
    mat = np.array(cos["matrix"])

    # Canonical order
    from _paper_style import CRITICAL_ROLES, CONFORMIST_ROLES
    order = (["assistant_axis", "caa"]
             + list(CRITICAL_ROLES)
             + list(CONFORMIST_ROLES)
             + (["random_0"] if "random_0" in names else []))
    order = [n for n in order if n in names]
    idx = [names.index(n) for n in order]
    sub = mat[np.ix_(idx, idx)]

    fig, ax = plt.subplots(figsize=(8.5, 7))
    im = ax.imshow(sub, cmap="RdBu_r", vmin=-1, vmax=1)
    labels = [short_label(n) for n in order]
    ax.set_xticks(range(len(order)))
    ax.set_yticks(range(len(order)))
    ax.set_xticklabels(labels, rotation=35, ha="right")
    ax.set_yticklabels(labels)
    for i in range(len(order)):
        for j in range(len(order)):
            val = sub[i, j]
            ax.text(j, i, f"{val:+.2f}", ha="center", va="center",
                    color="white" if abs(val) > 0.55 else "black", fontsize=8)
    cbar = plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label("cosine similarity")
    ax.set_title("Figure 5 — Pairwise cosine similarity between steering vectors\n"
                 f"(Gemma 2 27B, residual stream, layer 22; from "
                 f"{os.path.basename(f'{RESULTS_DIR}/vector_cosine_similarities.json')})")

    save_fig(fig, "figure_5_cosine_heatmap")


if __name__ == "__main__":
    main()
