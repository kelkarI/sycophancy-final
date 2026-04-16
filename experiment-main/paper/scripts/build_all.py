"""
Run every paper figure + table script in dependency order.

Assumes the GPU pipeline (02b, 01, 02 tune/test, 02c decomp, overcorrection,
03 tune/test) and the multi-seed runs have completed. CPU-only.

Usage:
    python paper/scripts/build_all.py           # rebuild everything
    python paper/scripts/build_all.py --skip-multiseed
"""
import argparse
import subprocess
import sys
import os

THIS = os.path.dirname(os.path.abspath(__file__))

STEPS = [
    # Name,                           args
    ("aggregate_multiseed.py",        ["--split", "tune"]),
    ("aggregate_multiseed.py",        ["--split", "test"]),
    ("fig_bidirectionality.py",       []),
    ("fig_caa_headtohead.py",         []),
    ("fig_decomposition.py",          []),
    ("fig_overcorrection_taxonomy.py",[]),
    ("fig_cosine_heatmap.py",         []),
    ("fig_pca_persona_space.py",      []),
    ("fig_steering_curves.py",        []),
    ("projection_ablation.py",        []),
    ("verify_caa_leakage.py",         []),
    ("results_table.py",              []),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-multiseed", action="store_true")
    args = ap.parse_args()
    failed = []
    for name, extra in STEPS:
        if args.skip_multiseed and name == "aggregate_multiseed.py":
            continue
        cmd = [sys.executable, os.path.join(THIS, name)] + extra
        print(f"\n---\n$ {' '.join(cmd)}")
        r = subprocess.run(cmd)
        if r.returncode != 0:
            print(f"  FAILED (rc={r.returncode}): {name}")
            failed.append(name)
    print("\n" + ("=" * 40))
    print("Build summary:")
    print(f"  Total steps: {len(STEPS)}")
    print(f"  Failed:      {len(failed)}")
    if failed:
        print("  ->", failed)
        sys.exit(1)


if __name__ == "__main__":
    main()
