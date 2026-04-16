"""
Paper supplementary — CAA train/eval leakage receipt.

Confirms that the CAA training datasets (sycophancy_on_nlp_survey,
sycophancy_on_political_typology_quiz) share no questions with the eval
dataset (sycophancy_on_philpapers2020). Hash-based exact-match check on the
normalised question text.

Writes:
    paper/tables/caa_leakage_receipt.json
    paper/tables/caa_leakage_receipt.csv   (human-readable summary)
"""
import csv
import hashlib
import json
import os
import sys

_THIS = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _THIS)
from _paper_style import PAPER_TBL_DIR  # noqa: E402
sys.path.insert(0, os.path.abspath(os.path.join(_THIS, "..", "..", "scripts")))
from config import ROOT, CAA_DATASETS, EVAL_DATASET  # noqa: E402


def hash_text(s):
    normal = " ".join(s.split())
    return hashlib.sha256(normal.encode("utf-8")).hexdigest()[:16]


def load_hashes(path):
    hashes = set()
    n = 0
    with open(path) as f:
        for line in f:
            d = json.loads(line)
            hashes.add(hash_text(d["question"]))
            n += 1
    return hashes, n


def main():
    sdir = f"{ROOT}/data/sycophancy"
    eval_path = f"{sdir}/{EVAL_DATASET}"
    caa_paths = [f"{sdir}/{n}" for n in CAA_DATASETS]

    missing = [p for p in [eval_path] + caa_paths if not os.path.exists(p)]
    if missing:
        print("ERROR: datasets not downloaded. Run scripts/fetch_external.py first.")
        for m in missing:
            print("  missing:", m)
        sys.exit(1)

    eval_hashes, n_eval = load_hashes(eval_path)
    per_set = []
    all_train_hashes = set()
    for p in caa_paths:
        h, n = load_hashes(p)
        overlap = len(h & eval_hashes)
        per_set.append((os.path.basename(p), n, overlap))
        all_train_hashes |= h
    union_overlap = len(all_train_hashes & eval_hashes)

    out = {
        "eval_dataset": EVAL_DATASET,
        "eval_n": n_eval,
        "train_datasets": [
            {"name": name, "n": n, "overlap_with_eval": o}
            for name, n, o in per_set
        ],
        "train_union_size": len(all_train_hashes),
        "train_union_overlap_with_eval": union_overlap,
        "hash": "sha256 first 16 hex of whitespace-normalised question text",
    }
    json_path = os.path.join(PAPER_TBL_DIR, "caa_leakage_receipt.json")
    with open(json_path, "w") as f:
        json.dump(out, f, indent=2)
    print(f"  saved {json_path}")
    csv_path = os.path.join(PAPER_TBL_DIR, "caa_leakage_receipt.csv")
    with open(csv_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["split", "dataset", "n_questions", "overlap_with_eval"])
        w.writerow(["eval", EVAL_DATASET, n_eval, "--"])
        for name, n, o in per_set:
            w.writerow(["train", name, n, o])
        w.writerow(["train (union)", "|union|", len(all_train_hashes), union_overlap])
    print(f"  saved {csv_path}")
    if union_overlap > 0:
        print(f"WARNING: {union_overlap} overlapping questions between CAA train and eval.")
    else:
        print("OK: zero CAA train/eval overlap by question-text hash.")


if __name__ == "__main__":
    main()
