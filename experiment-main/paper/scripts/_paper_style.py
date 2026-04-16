"""
Shared plotting helpers for paper/scripts/*.

Conventions:
    - Every figure emits both PDF and PNG to paper/figures/ at 300 DPI.
    - Font: serif family so figures blend with LaTeX output; 10 pt default.
    - Color palette: pulls from config.COLORS but extends with a
      darker variant per condition class. Decompositions use hatched variants.
    - Error bars: prefer multi-seed std from results/multiseed_aggregate.json
      when present; fall back to within-split bootstrap. Always note which.

All figure scripts should route their saves through save_fig() below.
"""
import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Add scripts/ to sys.path so config.py imports work from paper/scripts/
_THIS = os.path.dirname(os.path.abspath(__file__))
_SCRIPTS = os.path.abspath(os.path.join(_THIS, "..", "..", "scripts"))
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

from config import (  # noqa: E402
    ROOT, COLORS, LABELS,
    CRITICAL_ROLES, CONFORMIST_ROLES, ROLE_NAMES,
    N_RANDOM_VECTORS, CONDITIONS_REAL,
    EXPECTED_DIRECTION,
)

PAPER_FIG_DIR = os.path.join(ROOT, "paper", "figures")
PAPER_TBL_DIR = os.path.join(ROOT, "paper", "tables")
RESULTS_DIR   = os.path.join(ROOT, "results")
VECTORS_DIR   = os.path.join(ROOT, "vectors", "steering")

os.makedirs(PAPER_FIG_DIR, exist_ok=True)
os.makedirs(PAPER_TBL_DIR, exist_ok=True)

# Publication-leaning defaults
plt.rcParams.update({
    "figure.dpi": 150,
    "savefig.dpi": 300,
    "font.family": "serif",
    "font.size": 10,
    "axes.labelsize": 11,
    "axes.titlesize": 11,
    "legend.fontsize": 9,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "axes.grid": True,
    "grid.alpha": 0.25,
    "grid.linewidth": 0.4,
    "axes.axisbelow": True,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
})


# ---- Condition grouping -------------------------------------------------
def condition_class(cond: str) -> str:
    if cond == "assistant_axis":
        return "axis"
    if cond == "caa":
        return "caa"
    if cond in CRITICAL_ROLES:
        return "critical"
    if cond in CONFORMIST_ROLES:
        return "conformist"
    if cond.startswith("random_"):
        return "random"
    return "other"


def condition_order_for_paper():
    """Canonical ordering for bar charts and tables."""
    return (
        ["assistant_axis", "caa"]
        + list(CRITICAL_ROLES)
        + list(CONFORMIST_ROLES)
        + [f"random_{i}" for i in range(N_RANDOM_VECTORS)]
    )


def short_label(cond: str) -> str:
    return LABELS.get(cond, cond)


def condition_color(cond: str) -> str:
    return COLORS.get(cond, "#7f7f7f")


# ---- IO helpers ---------------------------------------------------------
def load_json(path):
    with open(path) as f:
        return json.load(f)


def maybe_load_json(path):
    if os.path.exists(path):
        return load_json(path)
    return None


def save_fig(fig, name: str, tight: bool = True):
    """Emit PDF + PNG at 300 DPI into paper/figures/{name}.{pdf,png}."""
    if tight:
        try:
            fig.tight_layout()
        except Exception:
            pass
    base = os.path.join(PAPER_FIG_DIR, name)
    fig.savefig(base + ".pdf", dpi=300, bbox_inches="tight")
    fig.savefig(base + ".png", dpi=300, bbox_inches="tight")
    print(f"  saved {base}.pdf + .png")


def write_csv(rows, header, name: str):
    import csv
    path = os.path.join(PAPER_TBL_DIR, f"{name}.csv")
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        for r in rows:
            w.writerow(r)
    print(f"  saved {path}")
    return path


# ---- Multi-seed aggregate ---------------------------------------------
def load_multiseed(split: str = "test"):
    """Return multi-seed aggregate for the given split, or None if unavailable.

    The aggregator writes per-split files: results/multiseed_aggregate_test.json
    and _tune.json. Falls back to the legacy no-suffix file if the split-specific
    one is absent.
    """
    for path in [
        f"{RESULTS_DIR}/multiseed_aggregate_{split}.json",
        f"{RESULTS_DIR}/multiseed_aggregate.json",
    ]:
        if os.path.exists(path):
            return load_json(path)
    return None


def error_bar_for(cond: str, split: str = "test"):
    """Return (mean, std, source) for a condition's best-logit, preferring
    multi-seed aggregate. Returns (None, None, None) if nothing available.
    """
    agg = load_multiseed(split)
    if agg and "per_condition" in agg:
        rec = agg["per_condition"].get(cond)
        if rec:
            return (rec.get("mean_logit"),
                    rec.get("std_logit", 0.0),
                    f"multiseed_n{rec.get('n_seeds', '?')}")
    return (None, None, None)


__all__ = [
    "PAPER_FIG_DIR", "PAPER_TBL_DIR", "RESULTS_DIR", "VECTORS_DIR",
    "plt", "load_json", "maybe_load_json", "save_fig", "write_csv",
    "condition_class", "condition_order_for_paper", "short_label",
    "condition_color", "load_multiseed", "error_bar_for",
    "CRITICAL_ROLES", "CONFORMIST_ROLES", "ROLE_NAMES",
    "CONDITIONS_REAL", "EXPECTED_DIRECTION",
]
