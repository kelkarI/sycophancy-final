"""
Qualitative check — conformist roles.

Mirrors qual_check.py but steers with each of the 4 conformist roles
(peacekeeper, pacifist, collaborator, facilitator) at its tune-locked best
coefficient, plus baseline and skeptic for contrast.

Picks high-baseline-sycophancy questions from the per-seed checkpoint produced
during 02 so the starting condition is a question Gemma 2 27B would normally
answer sycophantically -- that's where behavioural differences between
conditions are most visible.

Writes:
    results/qual_check_conformist.json
    results/qual_check_conformist.txt   (human-readable)
"""
import argparse
import json
import os
import sys

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from config import (
    ROOT, ASSISTANT_AXIS_PATH, MODEL_NAME, TARGET_LAYER,
    CONFORMIST_ROLES,
)

sys.path.insert(0, ASSISTANT_AXIS_PATH)
from assistant_axis.steering import ActivationSteering


def open_form(question_text: str) -> str:
    cuts = ['\n\nChoices:', '\n (A)', '\nChoices:', '\n(A)']
    cut = len(question_text)
    for c in cuts:
        i = question_text.find(c)
        if i > 0:
            cut = min(cut, i)
    prefix = question_text[:cut].rstrip()
    return prefix + "\n\nDo you agree with my view? Briefly explain."


def gen(model, tok, prompt_text, vec=None, coeff=0.0, max_new=150):
    chat = [{"role": "user", "content": prompt_text}]
    p = tok.apply_chat_template(chat, tokenize=False, add_generation_prompt=True)
    inputs = tok(p, return_tensors="pt").to(model.device)
    if vec is None or abs(coeff) < 1e-9:
        with torch.no_grad():
            out = model.generate(**inputs, max_new_tokens=max_new, do_sample=False)
    else:
        with ActivationSteering(
            model, steering_vectors=[vec], coefficients=[coeff],
            layer_indices=[TARGET_LAYER], intervention_type="addition",
            positions="all",
        ):
            with torch.no_grad():
                out = model.generate(**inputs, max_new_tokens=max_new, do_sample=False)
    return tok.decode(out[0][inputs.input_ids.shape[1]:],
                      skip_special_tokens=True).strip()


def load_best_coefs(path):
    with open(path) as f:
        return json.load(f).get("best_coefs", {})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--locked-coefs-from",
                    default=f"{ROOT}/results/best_coefs_tune_aggregate.json")
    ap.add_argument("--n-questions", type=int, default=5)
    ap.add_argument("--baseline-seed-dir",
                    default=f"{ROOT}/results/seed_42",
                    help="Directory containing the per-seed checkpoints to "
                         "pull high-syc baseline rows from.")
    ap.add_argument(
        "--facilitator-coef-override", type=float, default=2000.0,
        help="Facilitator's tune-locked coef is -5000 (degradation regime "
             "with meaningless generations). Override with +2000 so the "
             "qualitative comparison is fair. Set to 0 to disable override.",
    )
    args = ap.parse_args()

    # Pull high-sycophancy baseline rows from seed_42 (or user-specified dir).
    # We use the tune-seed all_results since baseline.json per seed may not
    # be in the seed dir. Fall back to a scan of all_results_tune.json.
    baseline_rows = []
    # Try per-seed checkpoint first
    ck_path = f"{args.baseline_seed_dir}/checkpoints/baseline_tune.json"
    if not os.path.exists(ck_path):
        # Fallback: scan all_results_tune.json for a canonical baseline
        ar = f"{ROOT}/results/all_results_tune.json"
        with open(ar) as f:
            rows = json.load(f)
        baseline_rows = [
            r for r in rows
            if r["condition"] == "assistant_axis" and r["coefficient"] == 0.0
        ]
    else:
        with open(ck_path) as f:
            baseline_rows = json.load(f)

    with open(f"{ROOT}/data/eval_data.json") as f:
        eval_data = json.load(f)
    qid_map = {r["question_id"]: r for r in eval_data}

    # Pick high-syc "original" variant rows where the model chose syc
    candidates = sorted(
        [r for r in baseline_rows
         if r.get("variant") == "original" and r.get("chose_sycophantic")],
        key=lambda r: -r["syc_logit"],
    )[: args.n_questions]
    print(f"Picked {len(candidates)} high-sycophancy baseline questions "
          f"(syc_logit range: "
          f"{candidates[0]['syc_logit']:.2f}..{candidates[-1]['syc_logit']:.2f})")

    # Load coefs
    locked = load_best_coefs(args.locked_coefs_from)
    coefs = {c: float(locked.get(c, 0.0)) for c in CONFORMIST_ROLES}
    if args.facilitator_coef_override != 0 and "facilitator" in coefs:
        orig = coefs["facilitator"]
        coefs["facilitator"] = args.facilitator_coef_override
        print(f"Facilitator coef overridden: {orig} -> "
              f"{args.facilitator_coef_override} (see --help).")
    # Add skeptic at locked tune coef for contrast
    coefs["skeptic"] = float(locked.get("skeptic", 2000.0))

    print("\nLoading model (bf16)...")
    tok = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME, torch_dtype=torch.bfloat16, device_map="auto"
    )
    model.eval()

    vecs = {}
    for c in list(CONFORMIST_ROLES) + ["skeptic"]:
        vp = f"{ROOT}/vectors/steering/{c}_unit.pt"
        vecs[c] = torch.load(vp, weights_only=False).float().to(model.device)

    print("\nGenerating...")
    all_out = []
    for qi, row in enumerate(candidates):
        qrow = qid_map[row["question_id"]]
        open_q = open_form(qrow["question_text"])
        print(f"\n=== Question {qi+1}  qid={row['question_id']}  "
              f"baseline syc_logit={row['syc_logit']:+.2f} ===")

        # baseline
        baseline_text = gen(model, tok, open_q)
        all_out.append({
            "qi": qi, "qid": row["question_id"],
            "baseline_syc_logit": float(row["syc_logit"]),
            "prompt": open_q,
            "condition": "baseline", "coefficient": 0.0,
            "response": baseline_text,
        })

        # each conformist + skeptic contrast
        order = list(CONFORMIST_ROLES) + ["skeptic"]
        for cond in order:
            c = coefs[cond]
            txt = gen(model, tok, open_q, vec=vecs[cond], coeff=c)
            all_out.append({
                "qi": qi, "qid": row["question_id"],
                "baseline_syc_logit": float(row["syc_logit"]),
                "prompt": open_q,
                "condition": cond, "coefficient": c,
                "response": txt,
            })

    # JSON
    json_path = f"{ROOT}/results/qual_check_conformist.json"
    with open(json_path, "w") as f:
        json.dump({
            "coefficients": coefs,
            "n_questions": len(candidates),
            "results": all_out,
        }, f, indent=2)
    print(f"\nSaved {json_path}")

    # Human-readable
    txt_path = f"{ROOT}/results/qual_check_conformist.txt"
    with open(txt_path, "w") as f:
        f.write("QUALITATIVE CHECK -- CONFORMIST ROLES vs BASELINE vs SKEPTIC\n")
        f.write("=" * 72 + "\n\n")
        f.write(f"Operating coefficients: {coefs}\n\n")
        for qi in range(len(candidates)):
            rows = [r for r in all_out if r["qi"] == qi]
            f.write("-" * 72 + "\n")
            f.write(f"Question {qi+1}  (qid {rows[0]['qid']}, "
                    f"baseline syc_logit {rows[0]['baseline_syc_logit']:+.2f})\n")
            f.write("-" * 72 + "\n")
            f.write(f"USER: {rows[0]['prompt']}\n\n")
            for r in rows:
                f.write(f"--- {r['condition'].upper():>13s} "
                        f"(c={r['coefficient']:+.0f}) ---\n")
                f.write(r["response"] + "\n\n")
    print(f"Saved {txt_path}")


if __name__ == "__main__":
    main()
