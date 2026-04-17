"""
Qualitative check -- CAA.

Same setup as qual_check.py / qual_check_conformist.py but steers with the
CAA vector at its tune-locked best coefficient (c = -2000). Also includes
baseline, skeptic, and assistant_axis columns so CAA can be read side by
side with the general directions that approximate it.

Writes:
    results/qual_check_caa.json
    results/qual_check_caa.txt    (human-readable)
"""
import argparse
import json
import os
import sys

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from config import ROOT, ASSISTANT_AXIS_PATH, MODEL_NAME, TARGET_LAYER

sys.path.insert(0, ASSISTANT_AXIS_PATH)
from assistant_axis.steering import ActivationSteering


def open_form(question_text: str) -> str:
    cuts = ['\n\nChoices:', '\n (A)', '\nChoices:', '\n(A)']
    cut = len(question_text)
    for c in cuts:
        i = question_text.find(c)
        if i > 0:
            cut = min(cut, i)
    return question_text[:cut].rstrip() + "\n\nDo you agree with my view? Briefly explain."


def gen(model, tok, prompt_text, vec=None, coeff=0.0, max_new=400):
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--locked-coefs-from",
                    default=f"{ROOT}/results/best_coefs_tune_aggregate.json")
    ap.add_argument("--n-questions", type=int, default=5)
    ap.add_argument("--baseline-seed-dir",
                    default=f"{ROOT}/results/seed_42",
                    help="Directory whose checkpoints we scan for high-syc "
                         "baseline rows (fallback: all_results_tune.json).")
    args = ap.parse_args()

    # Locate baseline rows (high-sycophancy picker matches qual_check*.py)
    ck_path = f"{args.baseline_seed_dir}/checkpoints/baseline_tune.json"
    if os.path.exists(ck_path):
        with open(ck_path) as f:
            baseline_rows = json.load(f)
    else:
        with open(f"{ROOT}/results/all_results_tune.json") as f:
            rows = json.load(f)
        baseline_rows = [
            r for r in rows
            if r["condition"] == "assistant_axis" and r["coefficient"] == 0.0
        ]
    with open(f"{ROOT}/data/eval_data.json") as f:
        eval_data = json.load(f)
    qid_map = {r["question_id"]: r for r in eval_data}

    candidates = sorted(
        [r for r in baseline_rows
         if r.get("variant") == "original" and r.get("chose_sycophantic")],
        key=lambda r: -r["syc_logit"],
    )[: args.n_questions]
    print(f"Picked {len(candidates)} high-sycophancy baseline questions.")

    with open(args.locked_coefs_from) as f:
        locked = json.load(f).get("best_coefs", {})

    # Columns: baseline, caa (the focus), assistant_axis (broad), skeptic (best role)
    cols = [
        ("baseline", 0.0, None),
        ("caa", float(locked.get("caa", -2000.0)), "caa_unit.pt"),
        ("assistant_axis", float(locked.get("assistant_axis", 2000.0)),
         "assistant_axis_unit.pt"),
        ("skeptic", float(locked.get("skeptic", 2000.0)), "skeptic_unit.pt"),
    ]

    print("\nLoading model (bf16)...")
    tok = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME, torch_dtype=torch.bfloat16, device_map="auto"
    )
    model.eval()

    vecs = {}
    for name, _coef, fname in cols:
        if fname is None:
            vecs[name] = None
        else:
            vp = f"{ROOT}/vectors/steering/{fname}"
            vecs[name] = torch.load(vp, weights_only=False).float().to(model.device)

    print("\nGenerating...")
    all_out = []
    for qi, row in enumerate(candidates):
        qrow = qid_map[row["question_id"]]
        open_q = open_form(qrow["question_text"])
        print(f"\n=== Question {qi+1}  qid={row['question_id']}  "
              f"baseline syc_logit={row['syc_logit']:+.2f} ===")
        for name, coef, _f in cols:
            txt = gen(model, tok, open_q, vec=vecs[name], coeff=coef)
            all_out.append({
                "qi": qi,
                "qid": row["question_id"],
                "baseline_syc_logit": float(row["syc_logit"]),
                "prompt": open_q,
                "condition": name,
                "coefficient": coef,
                "response": txt,
            })

    # JSON
    json_path = f"{ROOT}/results/qual_check_caa.json"
    with open(json_path, "w") as f:
        json.dump({
            "columns": [(n, c) for n, c, _ in cols],
            "n_questions": len(candidates),
            "results": all_out,
        }, f, indent=2)
    print(f"\nSaved {json_path}")

    # Human-readable
    txt_path = f"{ROOT}/results/qual_check_caa.txt"
    with open(txt_path, "w") as f:
        f.write("QUALITATIVE CHECK -- CAA at tune-locked best coefficient "
                "(with baseline/axis/skeptic contrast)\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"Columns and their coefficients: "
                f"{[(n, c) for n, c, _ in cols]}\n\n")
        for qi in range(len(candidates)):
            rows = [r for r in all_out if r["qi"] == qi]
            f.write("-" * 80 + "\n")
            f.write(f"Question {qi+1}  (qid {rows[0]['qid']}, "
                    f"baseline syc_logit {rows[0]['baseline_syc_logit']:+.2f})\n")
            f.write("-" * 80 + "\n")
            f.write(f"USER: {rows[0]['prompt']}\n\n")
            for r in rows:
                f.write(f"--- {r['condition'].upper():>15s} "
                        f"(c={r['coefficient']:+.0f}) ---\n")
                f.write(r["response"] + "\n\n")
    print(f"Saved {txt_path}")


if __name__ == "__main__":
    main()
