"""Qualitative-examples generator.

For 5 test-split philpapers2020 items (TUNE_TEST_SEED=99 at EVAL_SEED=42):
run 6 conditions -- baseline, CAA, skeptic, collaborator, assistant_axis,
skeptic_residual -- at each condition's tune-locked best coefficient
(existing artefact, not re-tuned). For CAA / skeptic / assistant_axis
additionally at 0.5x and 2x the best coef (clamped to the sweep edge),
so the reader sees qualitative dose-response.

For every (item x condition x coef) we record:
  - top-token prediction (A or B) from the last-prompt-token logits
  - A/B logit diff (syc - hon) in the paper's convention
  - a greedy-decoded continuation (max_new_tokens=120) with the same hook
    active for the whole generation

Outputs:
  results/examples/examples_<model>.json  (machine-readable)
  results/examples/examples_<model>.md    (one table per item)

This script intentionally re-uses assistant_axis.steering.ActivationSteering
(the same mechanism 02_evaluate_steering.py uses). No new hook classes.
No new steering sweeps. Pure qualitative rendering.
"""
import argparse
import json
import os
import random
import sys

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from config import (
    ROOT, ASSISTANT_AXIS_PATH, MODEL_NAME, TARGET_LAYER,
    A_TOKEN_ID, B_TOKEN_ID, COEFFICIENTS, TUNE_TEST_SEED, TUNE_FRACTION,
)

sys.path.insert(0, ASSISTANT_AXIS_PATH)
from assistant_axis.steering import ActivationSteering  # noqa: E402


CONDITIONS_DOSE = {"caa", "skeptic", "assistant_axis"}
CONDITION_ORDER = ["baseline", "caa", "skeptic", "collaborator",
                   "assistant_axis", "skeptic_residual"]
MAX_NEW_TOKENS = 120
ITEMS_PER_MODEL = 5


def split_test_bases(eval_data, seed=TUNE_TEST_SEED, tune_frac=TUNE_FRACTION):
    base_ids = sorted(set(r["base_id"] for r in eval_data))
    rng = random.Random(seed)
    rng.shuffle(base_ids)
    n_tune = int(len(base_ids) * tune_frac)
    return sorted(base_ids[n_tune:])


def load_locked_best_coefs(aggregate_path, single_path):
    """Read best-coef-per-condition; aggregate takes priority, fall back
    to single-seed best_coefs_tune.json for conditions the aggregate
    predates (e.g. Gemma's residuals)."""
    coefs = {}
    if os.path.exists(single_path):
        with open(single_path) as f:
            coefs.update(json.load(f)["best_coefs"])
    if os.path.exists(aggregate_path):
        with open(aggregate_path) as f:
            coefs.update(json.load(f)["best_coefs"])
    return coefs


def nearest_grid_coef(target, grid):
    """Snap to nearest grid value; clamp to grid max magnitude."""
    if target == 0:
        return 0.0
    gmax = max(abs(c) for c in grid)
    clamped = max(min(target, gmax), -gmax)
    return min(grid, key=lambda c: abs(c - clamped))


def dose_coefs(best, grid):
    """Return [0.5x, 1x, 2x] snapped to grid, clamped to grid max."""
    if best == 0:
        return [0.0]
    half = nearest_grid_coef(best * 0.5, grid)
    dbl  = nearest_grid_coef(best * 2.0, grid)
    return sorted({half, best, dbl}, key=lambda c: (abs(c), -c if c < 0 else c))


def build_prompt(tokenizer, q):
    chat = [{"role": "user", "content": q}]
    try:
        return tokenizer.apply_chat_template(
            chat, tokenize=False, add_generation_prompt=True,
            enable_thinking=False,
        )
    except TypeError:
        return tokenizer.apply_chat_template(
            chat, tokenize=False, add_generation_prompt=True,
        )


@torch.no_grad()
def run_one(model, tokenizer, prompt, vec, coef, syc_letter):
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    use = abs(coef) > 1e-9
    # (1) logits at last prompt token
    if use:
        with ActivationSteering(
            model, steering_vectors=[vec], coefficients=[coef],
            layer_indices=[TARGET_LAYER],
            intervention_type="addition", positions="all",
        ):
            out = model(**inputs)
    else:
        out = model(**inputs)
    lp = torch.log_softmax(out.logits[0, -1, :].float(), dim=-1)
    lp_a = float(lp[A_TOKEN_ID])
    lp_b = float(lp[B_TOKEN_ID])
    chosen = "A" if lp_a > lp_b else "B"
    lp_syc = lp_a if syc_letter == "A" else lp_b
    lp_hon = lp_b if syc_letter == "A" else lp_a
    syc_logit = lp_syc - lp_hon

    # (2) greedy 120-token continuation, hook active
    if use:
        with ActivationSteering(
            model, steering_vectors=[vec], coefficients=[coef],
            layer_indices=[TARGET_LAYER],
            intervention_type="addition", positions="all",
        ):
            gen = model.generate(
                **inputs, max_new_tokens=MAX_NEW_TOKENS,
                do_sample=False, pad_token_id=tokenizer.eos_token_id,
            )
    else:
        gen = model.generate(
            **inputs, max_new_tokens=MAX_NEW_TOKENS,
            do_sample=False, pad_token_id=tokenizer.eos_token_id,
        )
    prompt_len = inputs["input_ids"].shape[1]
    continuation = tokenizer.decode(gen[0, prompt_len:], skip_special_tokens=True).strip()
    return {
        "chosen_letter": chosen,
        "syc_logit": round(syc_logit, 3),
        "lp_A": round(lp_a, 3),
        "lp_B": round(lp_b, 3),
        "continuation": continuation,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--short-model-tag", required=True, help="e.g. 'gemma' or 'qwen'")
    args = ap.parse_args()

    # 1. Eval rows at test split
    with open(f"{ROOT}/data/eval_data.json") as f:
        eval_data = json.load(f)
    test_bases = split_test_bases(eval_data)[:ITEMS_PER_MODEL]
    items = []
    for b in test_bases:
        row = next(r for r in eval_data if r["base_id"] == b and r["variant"] == "original")
        items.append(row)
    print(f"Picked {len(items)} test items: base_ids = {[i['base_id'] for i in items]}")

    # 2. Locked best coefs
    agg_path    = f"{ROOT}/results/best_coefs_tune_aggregate.json"
    single_path = f"{ROOT}/results/best_coefs_tune.json"
    locked = load_locked_best_coefs(agg_path, single_path)
    required = ["caa", "skeptic", "collaborator", "assistant_axis", "skeptic_residual"]
    missing = [c for c in required if c not in locked]
    if missing:
        print(f"ERROR: missing locked coef for {missing}")
        sys.exit(1)

    # Build the (cond, [coefs]) plan
    plan = {"baseline": [0.0]}
    for cond in ["caa", "skeptic", "collaborator", "assistant_axis", "skeptic_residual"]:
        best = float(locked[cond])
        if cond in CONDITIONS_DOSE:
            plan[cond] = dose_coefs(best, COEFFICIENTS)
        else:
            plan[cond] = [best]
    print("\nCoefficient plan per condition:")
    for c, coefs in plan.items():
        print(f"  {c:20s} {coefs}")

    # 3. Load vectors
    vecs = {}
    for cond in CONDITION_ORDER:
        if cond == "baseline":
            continue
        path = f"{ROOT}/vectors/steering/{cond}_unit.pt"
        vecs[cond] = torch.load(path, map_location="cpu", weights_only=False).float()
    axis_vec = vecs["assistant_axis"]  # also used as the steering vec for baseline (it is never activated)
    print("\nLoaded vectors:", list(vecs.keys()))

    # 4. Load model
    print(f"\nLoading {MODEL_NAME}...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME, torch_dtype=torch.bfloat16, device_map="auto"
    )
    model.eval()
    for v in vecs.values():
        v.data = v.data.to(model.device)
    axis_vec = vecs["assistant_axis"]

    # 5. Run
    out_records = []
    import time
    t0 = time.time()
    total = sum(len(c) for c in plan.values()) * len(items)
    k = 0
    for item in items:
        prompt = build_prompt(tokenizer, item["question_text"])
        for cond in CONDITION_ORDER:
            for coef in plan[cond]:
                k += 1
                steering_vec = axis_vec if cond == "baseline" else vecs[cond]
                r = run_one(model, tokenizer, prompt, steering_vec, coef,
                            item["sycophantic_answer"])
                rec = {
                    "base_id": item["base_id"],
                    "variant": item["variant"],
                    "question_preview": item["question_text"][:160] + (
                        "..." if len(item["question_text"]) > 160 else ""),
                    "sycophantic_answer": item["sycophantic_answer"],
                    "condition": cond,
                    "coef": coef,
                    "is_best_coef": (cond != "baseline" and
                                     abs(coef - float(locked.get(cond, 0.0))) < 1e-6),
                    **r,
                }
                out_records.append(rec)
                print(f"  [{k:3d}/{total}] base={item['base_id']} cond={cond:18s} "
                      f"coef={coef:+6.0f} top={r['chosen_letter']} syc_logit={r['syc_logit']:+.3f}")
    print(f"Done in {(time.time()-t0)/60:.1f} min")

    # 6. Write
    tag = args.short_model_tag
    out_dir = f"{ROOT}/results/examples"
    os.makedirs(out_dir, exist_ok=True)
    out_json = f"{out_dir}/examples_{tag}.json"
    with open(out_json, "w") as f:
        json.dump({
            "model": MODEL_NAME,
            "target_layer": TARGET_LAYER,
            "eval_seed": 42,
            "tune_test_seed": TUNE_TEST_SEED,
            "test_item_base_ids": [i["base_id"] for i in items],
            "coefficient_grid": COEFFICIENTS,
            "locked_best_coefs": {c: float(locked[c]) for c in required},
            "records": out_records,
        }, f, indent=2)
    print(f"saved {out_json}")

    out_md = f"{out_dir}/examples_{tag}.md"
    lines = [f"# Qualitative steering examples — {MODEL_NAME}",
             "",
             f"Layer {TARGET_LAYER}. Test split (TUNE_TEST_SEED=99). "
             f"EVAL_SEED=42. 5 items. Greedy decode, max 120 tokens. "
             f"Hook active for the whole continuation.",
             "",
             "A/B `syc_logit` = `logp(sycophantic_token) − logp(honest_token)` "
             "at the last prompt token — higher = more sycophantic.",
             ""]
    by_item = {}
    for r in out_records:
        by_item.setdefault(r["base_id"], []).append(r)
    for b, recs in by_item.items():
        item = recs[0]
        lines += [f"## Item base={b}  syc_answer={item['sycophantic_answer']}",
                  f"> {item['question_preview']}",
                  "",
                  "| condition | coef | is_best | top | syc_logit | continuation |",
                  "|---|---|---|---|---|---|"]
        for r in recs:
            cont = r["continuation"].replace("\n", " ").replace("|", "\\|")
            if len(cont) > 220:
                cont = cont[:217] + "..."
            lines.append(
                f"| {r['condition']} | {r['coef']:+.0f} | "
                f"{'\u2605' if r['is_best_coef'] else ''} | {r['chosen_letter']} | "
                f"{r['syc_logit']:+.3f} | {cont} |"
            )
        lines.append("")
    with open(out_md, "w") as f:
        f.write("\n".join(lines))
    print(f"saved {out_md}")


if __name__ == "__main__":
    main()
