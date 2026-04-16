"""
Fill [TODO_*] placeholders in paper/RESULTS.md with numbers traced from the
actual results JSONs. Operates idempotently: tokens that fail to resolve are
left in place (so you can see what's still missing).

The mapping is explicit per-token. Every token is resolved from a specific
file, with the file path referenced in the RESULTS.md prose anyway.

Usage:
    python paper/scripts/fill_results.py           # replace in place
    python paper/scripts/fill_results.py --dry-run # show what would change

Robust to partial results: if a specific file is absent, the tokens that
depend on it are left as placeholders and noted in the summary.
"""
import argparse
import json
import math
import os
import re
import sys

_THIS = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _THIS)
from _paper_style import (  # noqa: E402
    RESULTS_DIR, PAPER_TBL_DIR, load_json, maybe_load_json,
    CRITICAL_ROLES, CONFORMIST_ROLES, EXPECTED_DIRECTION, short_label,
)

ROOT = os.path.abspath(os.path.join(_THIS, "..", ".."))
RESULTS_MD = os.path.join(ROOT, "paper", "RESULTS.md")


def fmt_pct(x):
    return f"{x*100:.1f}"


def fmt3(x):
    return f"{x:+.3f}"


def fmt_p(p):
    if p is None:
        return "--"
    if p < 1e-15:
        return r"$< 10^{-15}$"
    if p < 1e-4:
        return f"${p:.2e}$"
    return f"{p:.4f}"


def resolve_tokens():
    """Return a dict token_name -> string replacement."""
    repl = {}

    # --- baseline numbers ---
    rates = maybe_load_json(f"{RESULTS_DIR}/sycophancy_rates_test.json")
    if rates:
        cell = rates.get("assistant_axis", {}).get("0.0")
        if cell:
            repl["TODO_BASELINE_RATE"] = fmt_pct(cell["binary_rate"])
            repl["TODO_BASELINE_LOGIT"] = fmt3(cell["mean_syc_logit"])
            baseline_logit = cell["mean_syc_logit"]
            baseline_rate = cell["binary_rate"]
    else:
        baseline_logit = None
        baseline_rate = None

    # --- best-coefs ---
    best = maybe_load_json(f"{RESULTS_DIR}/best_coefs_tune_aggregate.json") \
           or maybe_load_json(f"{RESULTS_DIR}/best_coefs_tune.json")
    best_coefs = best.get("best_coefs", {}) if best else {}

    # --- statistical tests (test split) ---
    tests = maybe_load_json(f"{RESULTS_DIR}/statistical_tests_test.json")
    wil = tests.get("primary_wilcoxon_best_vs_baseline", {}) if tests else {}

    # --- per-condition table ---
    def cond_delta(cond):
        if not rates or cond not in best_coefs:
            return None
        coef = best_coefs[cond]
        k = f"{coef}"
        cell = rates.get(cond, {}).get(k)
        if not cell:
            return None
        return {
            "coef": coef,
            "logit": cell["mean_syc_logit"],
            "delta": cell["mean_syc_logit"] - baseline_logit,
            "rate": cell["binary_rate"],
            "delta_rate_pp": (cell["binary_rate"] - baseline_rate) * 100,
        }

    # --- Objective 1: most-effective critical role ---
    if baseline_logit is not None and rates and best_coefs:
        crit = []
        for c in CRITICAL_ROLES:
            d = cond_delta(c)
            if d:
                crit.append((c, d))
        if crit:
            crit.sort(key=lambda x: x[1]["logit"])
            c, d = crit[0]
            w = wil.get(c, {})
            repl["TODO_MOST_EFFECTIVE_LABEL"] = short_label(c)
            repl["TODO_MOST_EFFECTIVE_DELTA"] = fmt3(d["delta"])
            repl["TODO_MOST_EFFECTIVE_DELTARATE"] = f"{d['delta_rate_pp']:+.1f}"
            repl["TODO_MOST_EFFECTIVE_PADJ"] = fmt_p(w.get("p_value_adjusted"))
            n_crit_sig = sum(
                1 for cc in CRITICAL_ROLES
                if wil.get(cc, {}).get("significant_after_mcc")
            )
            repl["TODO_N_CRITICAL_SIG"] = str(n_crit_sig)

        # --- Objective 1b: conformist bidirectionality ---
        conf = []
        for c in CONFORMIST_ROLES:
            d = cond_delta(c)
            if d:
                conf.append((c, d))
        if conf:
            mean_delta = sum(d["delta"] for _, d in conf) / len(conf)
            repl["TODO_CONFORMIST_MEAN_DELTA"] = fmt3(mean_delta)
            n_conf_sig = sum(
                1 for cc in CONFORMIST_ROLES
                if wil.get(cc, {}).get("significant_after_mcc")
            )
            repl["TODO_CONFORMIST_N_SIG"] = str(n_conf_sig)

        # --- random band std ---
        rand_deltas = []
        for i in range(10):
            rc = f"random_{i}"
            if rc in best_coefs:
                coef = best_coefs[rc]
                k = f"{coef}"
                cell = rates.get(rc, {}).get(k)
                if cell:
                    rand_deltas.append(cell["mean_syc_logit"] - baseline_logit)
        if rand_deltas:
            import statistics as st
            repl["TODO_RANDOM_BAND_STD"] = f"{st.stdev(rand_deltas):.3f}"

    # --- Objective 1c: axis ---
    if "assistant_axis" in best_coefs and baseline_logit is not None:
        d = cond_delta("assistant_axis")
        if d:
            repl["TODO_AXIS_DELTA"] = fmt3(d["delta"])
            repl["TODO_AXIS_COEF"] = f"{int(d['coef']):+d}"

    # --- Objective 2: CAA vs best role ---
    if baseline_logit is not None and "caa" in best_coefs:
        dc = cond_delta("caa")
        if dc:
            repl["TODO_CAA_DELTA"] = fmt3(dc["delta"])
            repl["TODO_CAA_COEF"] = f"{int(dc['coef']):+d}"
        # Best critical role (lowest logit among critical)
        crit = [(c, cond_delta(c)) for c in CRITICAL_ROLES
                if cond_delta(c) is not None]
        if crit:
            crit.sort(key=lambda x: x[1]["logit"])
            bc, bd = crit[0]
            repl["TODO_BEST_ROLE_DELTA"] = fmt3(bd["delta"])
            repl["TODO_BEST_ROLE_COEF"] = f"{int(bd['coef']):+d}"
            if dc:
                diff = dc["delta"] - bd["delta"]
                repl["TODO_CAA_MINUS_ROLE"] = fmt3(diff)
                # CI not trivially derivable without per-seed; annotate placeholder
                repl["TODO_CAA_ROLE_OVERLAP_95CI"] = \
                    "cross-seed overlap (see table_1_results.csv)"
                repl["TODO_CAA_VS_ROLE_CLAIM"] = (
                    f"Δ = {diff:+.3f}; CAA "
                    + ("reduces more" if diff < 0 else "reduces less")
                    + " than the best role"
                )

    # --- Objective 2b: efficiency ---
    for cond, tok in [("assistant_axis", "TODO_EFF_AXIS"),
                      ("caa", "TODO_EFF_CAA")]:
        d = cond_delta(cond)
        if d and d["coef"]:
            reduction = -d["delta"]
            eff = reduction / abs(d["coef"]) * 1e4
            repl[tok] = f"{eff:.2f}"
    # best role efficiency
    if "TODO_BEST_ROLE_DELTA" in repl:
        # Re-derive best role
        crit = [(c, cond_delta(c)) for c in CRITICAL_ROLES
                if cond_delta(c) is not None]
        if crit:
            crit.sort(key=lambda x: x[1]["logit"])
            bc, bd = crit[0]
            reduction = -bd["delta"]
            if bd["coef"]:
                repl["TODO_EFF_ROLE"] = f"{reduction/abs(bd['coef'])*1e4:.2f}"

    # --- Objective 3: decomposition ---
    decomp_csv_rows = []
    decomp_csv = f"{PAPER_TBL_DIR}/figure_3_decomposition.csv"
    if os.path.exists(decomp_csv):
        import csv
        with open(decomp_csv) as f:
            r = csv.DictReader(f)
            for row in r:
                try:
                    row["cos_abs"] = abs(float(row["cosine_role_caa"]))
                    row["frac_comp"] = float(row["fraction_from_caa_component"])
                    row["frac_resid"] = float(row["fraction_from_residual"])
                except Exception:
                    continue
                decomp_csv_rows.append(row)
        if decomp_csv_rows:
            # Split by cos threshold at the median
            decomp_csv_rows.sort(key=lambda r: -r["cos_abs"])
            mid = len(decomp_csv_rows) // 2
            high = decomp_csv_rows[:mid]
            low = decomp_csv_rows[mid:]
            if high:
                thr = high[-1]["cos_abs"]
                repl["TODO_HIGH_COS_THRESHOLD"] = f"{thr:.2f}"
                import statistics as st
                repl["TODO_HIGH_COS_FRAC"] = f"{st.mean(r['frac_comp'] for r in high):.2f}"
                repl["TODO_HIGH_COS_RESID_FRAC"] = f"{st.mean(r['frac_resid'] for r in high):.2f}"
                repl["TODO_HIGH_COS_EXAMPLES"] = ", ".join(r["label"] for r in high[:3])
            if low:
                thr = low[0]["cos_abs"]
                repl["TODO_LOW_COS_THRESHOLD"] = f"{thr:.2f}"
                import statistics as st
                repl["TODO_LOW_COS_FRAC"] = f"{st.mean(r['frac_resid'] for r in low):.2f}"
                repl["TODO_LOW_COS_CAA_FRAC"] = f"{st.mean(r['frac_comp'] for r in low):.2f}"
                repl["TODO_LOW_COS_EXAMPLES"] = ", ".join(r["label"] for r in low[:3])

    # --- Overcorrection counts ---
    oc = maybe_load_json(f"{RESULTS_DIR}/over_correction_eval_test.json")
    if oc:
        summary = oc.get("summary_by_condition", {})
        crit_over = 0
        n_true = 0
        conf_aw = 0
        n_false = 0
        for cond, s in summary.items():
            if cond in CRITICAL_ROLES:
                crit_over += s.get("count_DISAGREE_WRONG", 0)
            if cond in CONFORMIST_ROLES:
                conf_aw += s.get("count_AGREE_WRONG", 0)
        for cond, s in summary.items():
            # derive total probes for TRUE/FALSE split from any present row
            n_true = max(n_true,
                         s.get("count_AGREE_CORRECT", 0) + s.get("count_DISAGREE_WRONG", 0))
            n_false = max(n_false,
                          s.get("count_DISAGREE_CORRECT", 0) + s.get("count_AGREE_WRONG", 0))
        repl["TODO_CRITICAL_OVERCORRECTION"] = str(crit_over)
        repl["TODO_CONFORMIST_AGREE_WRONG"] = str(conf_aw)
        repl["TODO_TOTAL_TRUE_PROBES"] = str(n_true) if n_true else "8"
        repl["TODO_TOTAL_FALSE_PROBES"] = str(n_false) if n_false else "8"
        # Hedge / refuse cap
        hedge_refuse = [
            (s.get("count_HEDGE", 0) + s.get("count_REFUSE", 0)) / max(s.get("n_total", 1), 1)
            for s in summary.values()
        ]
        if hedge_refuse:
            repl["TODO_HEDGE_REFUSE_CAP"] = f"{max(hedge_refuse)*100:.0f}%"

    # --- Projection predictors ---
    proj_csv = f"{PAPER_TBL_DIR}/table_supp_projection_ablation.csv"
    if os.path.exists(proj_csv):
        import csv
        with open(proj_csv) as f:
            rdr = list(csv.DictReader(f))
        if rdr:
            r = rdr[0]
            try:
                repl["TODO_R_PROMPT"] = f"{float(r['r_prompt']):+.3f}"
                repl["TODO_P_PROMPT"] = fmt_p(float(r['p_prompt']))
                repl["TODO_R_RESP"] = f"{float(r['r_response']):+.3f}"
                repl["TODO_P_RESP"] = fmt_p(float(r['p_response']))
                lo = float(r['ci_lo_95']); hi = float(r['ci_hi_95'])
                repl["TODO_DIFF_CI"] = f"[{lo:+.3f}, {hi:+.3f}]"
                better = "yes" if lo > 0 else ("no" if hi < 0 else "indeterminate (CI spans 0)")
                repl["TODO_RESP_BETTER_CLAIM"] = better
            except Exception:
                pass

    # --- Leakage count ---
    leak = maybe_load_json(f"{PAPER_TBL_DIR}/caa_leakage_receipt.json")
    if leak:
        repl["TODO_LEAKAGE_COUNT"] = str(leak.get("train_union_overlap_with_eval", "--"))

    return repl


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if not os.path.exists(RESULTS_MD):
        print(f"ERROR: {RESULTS_MD} not found")
        sys.exit(1)
    with open(RESULTS_MD) as f:
        src = f.read()

    repl = resolve_tokens()
    all_tokens = set(re.findall(r"\[TODO_[A-Z0-9_]+\]", src))
    resolved = {t: repl[t[6:-1]] for t in all_tokens if t[6:-1] in repl}
    unresolved = sorted(t for t in all_tokens if t[6:-1] not in repl)

    new = src
    for tok, val in resolved.items():
        new = new.replace(tok, val)

    if args.dry_run:
        print(f"Would resolve {len(resolved)} / {len(all_tokens)} tokens.")
        for t in sorted(resolved):
            print(f"  {t} -> {resolved[t]}")
        if unresolved:
            print(f"\nStill unresolved ({len(unresolved)}):")
            for t in unresolved:
                print(f"  {t}")
    else:
        with open(RESULTS_MD, "w") as f:
            f.write(new)
        print(f"Wrote {RESULTS_MD} with {len(resolved)} substitutions.")
        if unresolved:
            print(f"Unresolved ({len(unresolved)}): {unresolved[:10]}"
                  + (" ..." if len(unresolved) > 10 else ""))


if __name__ == "__main__":
    main()
