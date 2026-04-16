"""
Paper supplementary — prompt-token vs response-token projection predictors.

The pooled Pearson r for response_projection vs syc_logit is already computed by
03_analysis.py and stored in results/statistical_tests_test.json under
axis_projection_response_token. This script materialises a small comparison
block and a two-panel scatter for the paper, and computes a bootstrap 95% CI on
the difference r_response - r_prompt.

Reads:
    results/axis_projections_test.json
    results/statistical_tests_test.json
Writes:
    paper/figures/figure_supp_projection_ablation.pdf + .png
    paper/tables/table_supp_projection_ablation.csv
"""
import os
import sys

import numpy as np
from scipy import stats

_THIS = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _THIS)
from _paper_style import (
    plt, RESULTS_DIR, PAPER_TBL_DIR, load_json, save_fig,
)


def main():
    # Prefer the dedicated response-capture output (02d_response_capture.py).
    # Fall back to the main-sweep projections file (which has response_projection
    # only if 02 was run without --skip-response-gen).
    import os as _os
    rp = f"{RESULTS_DIR}/axis_projections_response_test.json"
    if _os.path.exists(rp):
        proj = load_json(rp)
    else:
        proj = load_json(f"{RESULTS_DIR}/axis_projections_test.json")
    tests = load_json(f"{RESULTS_DIR}/statistical_tests_test.json")

    # Row-level pooled comparison on all real-condition rows, excluding the
    # baseline coef=0 cells (those would be duplicated across conditions).
    rows = [r for r in proj
            if r["coefficient"] != 0.0
            and r["condition"] in {"assistant_axis", "caa"} | set(r["condition"] for r in proj if not r["condition"].startswith("random_"))
            and not r["condition"].startswith("random_")]
    # Base-level aggregation per (cond, coef)
    from collections import defaultdict
    by_base = defaultdict(lambda: {"prompt": [], "resp": [], "logit": []})
    for r in rows:
        key = (r["condition"], r["coefficient"], r["base_id"])
        by_base[key]["prompt"].append(r["axis_projection"])
        rp = r.get("response_projection")
        if rp is not None and not (isinstance(rp, float) and rp != rp):
            by_base[key]["resp"].append(rp)
        by_base[key]["logit"].append(r["syc_logit"])

    p_proj, p_resp, p_logit = [], [], []
    for key, d in by_base.items():
        if not d["resp"]:
            continue
        p_proj.append(float(np.mean(d["prompt"])))
        p_resp.append(float(np.mean(d["resp"])))
        p_logit.append(float(np.mean(d["logit"])))
    p_proj = np.array(p_proj); p_resp = np.array(p_resp); p_logit = np.array(p_logit)
    n = len(p_logit)
    if n < 30:
        print(f"Insufficient data for projection ablation (n={n}).")
        return

    r_prompt, pp_prompt = stats.pearsonr(p_proj, p_logit)
    r_resp,  pp_resp  = stats.pearsonr(p_resp, p_logit)
    # Bootstrap CI on r_resp - r_prompt
    rng = np.random.default_rng(31)
    diffs = []
    idx = np.arange(n)
    for _ in range(2000):
        b = rng.choice(idx, size=n, replace=True)
        rr, _ = stats.pearsonr(p_resp[b], p_logit[b])
        rp, _ = stats.pearsonr(p_proj[b], p_logit[b])
        diffs.append(rr - rp)
    diffs = np.array(diffs)
    ci_lo, ci_hi = np.percentile(diffs, [2.5, 97.5])

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.6))
    for ax, x, r, p, ttl in [
        (ax1, p_proj, r_prompt, pp_prompt, "Prompt-last-token axis projection"),
        (ax2, p_resp, r_resp, pp_resp,    "Response-token mean axis projection"),
    ]:
        ax.scatter(x, p_logit, s=8, alpha=0.5, color="#555555")
        m, c0 = np.polyfit(x, p_logit, 1)
        xs = np.linspace(x.min(), x.max(), 50)
        ax.plot(xs, m*xs + c0, color="#d62728", lw=2,
                label=f"Pearson r = {r:+.3f} (p={p:.2e})")
        ax.axhline(0, color="black", lw=0.5, alpha=0.6)
        ax.set_xlabel(ttl)
        ax.set_ylabel("base-level mean syc_logit")
        ax.legend(loc="best")
        ax.set_title(ttl)
    fig.suptitle(f"Supplementary — projection-ablation scatter "
                 f"(n={n}; Δr = r_resp − r_prompt = {r_resp - r_prompt:+.3f}, "
                 f"95% CI [{ci_lo:+.3f}, {ci_hi:+.3f}])", y=1.02)
    save_fig(fig, "figure_supp_projection_ablation")

    import csv
    path = os.path.join(PAPER_TBL_DIR, "table_supp_projection_ablation.csv")
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["n", "r_prompt", "p_prompt", "r_response", "p_response",
                    "diff_r_response_minus_prompt", "ci_lo_95", "ci_hi_95"])
        w.writerow([n, r_prompt, pp_prompt, r_resp, pp_resp,
                    r_resp - r_prompt, ci_lo, ci_hi])
    print(f"  saved {path}")


if __name__ == "__main__":
    main()
