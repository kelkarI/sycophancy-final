# General Persona Directions vs CAA on Sycophancy — Gemma 2 27B

This repository contains the full code, data pipeline, results, and paper
artefacts for a sycophancy-steering study on **Gemma 2 27B Instruct**. We ask
whether general persona directions (skeptic, devil's advocate, scientist,
judge, contrarian; plus four conformist personas) extracted from open-ended
role-playing can steer the model away from sycophancy as effectively as the
targeted **Contrastive Activation Addition (CAA, Rimsky et al. 2024)** vector
trained on sycophancy-specific data.

## Three findings

1. **Role-direction steering is bidirectional on sycophancy.** Critical roles
   reduce sycophancy (all 5 significant after Holm across 5 tune / 3 test
   seeds); conformist roles trend toward increasing it (3 of 4 at positive
   best-coef; 1 of 4 reaches significance under Holm at n = 150 test bases).
   Random controls form a narrow null band (± ≈ 0.16 Δlogit).
2. **A general persona direction matches a targeted CAA vector.** CAA at
   c = −2000 yields Δlogit = −0.87 on held-out test; Skeptic at c = +2000
   yields Δlogit = −0.72 — ~83 % of CAA's reduction on a vector that was
   **not** trained from sycophancy data. Training sets are disjoint (zero
   question-text overlap confirmed by hash receipt).
3. **The reduction lives in the CAA-orthogonal direction.** Every critical
   and conformist role is near-orthogonal to CAA in embedding space
   (|cos(role, CAA)| ≤ 0.17; most ≤ 0.09). Behaviourally, when we steer with
   the unit-normalised CAA-aligned component and residual of each role at
   matched coefficient, the **residual alone recovers the full role effect**
   while the CAA-aligned piece opposes the role's reduction direction. Role
   sycophancy-reduction operates through a mechanism orthogonal to the
   targeted CAA direction.

Full write-up with file-traced numbers: `experiment-main/paper/RESULTS.md`.
Methods: `experiment-main/paper/METHODS.md`. Limitations:
`experiment-main/paper/LIMITATIONS.md`.

## Directory layout

```
.
├── README.md                           (you are here)
├── experiment-main/                    the experiment itself
│   ├── scripts/                        pipeline code (00_setup, 00b, 01,
│   │                                   02, 02b, 02c, 02d, 03, 
│   │                                   over_correction_check, qual_check,
│   │                                   run_multiseed, fetch_external, ...)
│   ├── paper/
│   │   ├── figures/                    8 publication figures (PDF + PNG, 300 DPI)
│   │   ├── tables/                     CSV + LaTeX tables
│   │   ├── scripts/                    figure/table generators + fill_results
│   │   ├── RESULTS.md                  skeleton with numbers traced to files
│   │   ├── METHODS.md                  model, layer, sweep, stats
│   │   └── LIMITATIONS.md              honest caveats
│   ├── results/                        per-seed and aggregate JSON outputs
│   ├── vectors/                        steering vectors (critical roles,
│   │                                   conformist roles, CAA, randoms,
│   │                                   CAA-component + residual per role)
│   ├── data/                           philpapers2020 eval + NLP-survey +
│   │                                   political-typology-quiz (CAA train)
│   ├── legacy/                         preserved pre-rewrite 7-condition
│   │                                   outputs for provenance comparison
│   ├── runs/                           per-run log files (stdout/stderr)
│   ├── PIPELINE_MAP.md                 one-page pipeline + runtime map
│   ├── GAP_ANALYSIS.md                 ruthless audit against 3 objectives
│   └── README.md                       full reproducibility guide (commands,
│                                       H100 runtimes, HF auth, etc.)
├── Issues.pdf / Issues_Report.pdf      pre-rewrite statistical review
├── Novelty_Report.pdf                  novelty analysis vs prior work
├── Updates to Ishaan Repo.pdf          detailed changelog of the rewrite
└── generate_*_report.py                scripts that produced the PDFs
```

## Reproducibility in one command block

Full pipeline on a single H100 or GH200, ~10 GPU hours:

```bash
cd experiment-main/scripts
export EXPERIMENT_ROOT=$PWD/..
export ASSISTANT_AXIS_PATH=/path/to/cloned/safety-research/assistant-axis
pip install transformers accelerate huggingface_hub datasets scipy \
            scikit-learn statsmodels matplotlib seaborn plotly

huggingface-cli login                                            # gated Gemma 2 27B
python fetch_external.py                                         # datasets + role vectors
python 00_setup.py                                               # sanity check
python 00b_rebuild_eval.py                                       # 600 counterbalanced rows
python 02b_extract_caa.py                                        # Rimsky CAA vector
python 01_prepare_steering_vectors.py                            # decomposition + cosine matrix
python run_multiseed.py --seeds 42 7 123 456 789 --split tune \
       --skip-response-gen
python ../paper/scripts/aggregate_multiseed.py --split tune      # consensus best_coefs
python run_multiseed.py --seeds 42 7 123 --split test \
       --locked-coefs-from ../results/best_coefs_tune_aggregate.json \
       --skip-response-gen
python ../paper/scripts/aggregate_multiseed.py --split test
python 02c_evaluate_decomposition.py --split test \
       --locked-coefs-from ../results/best_coefs_tune_aggregate.json
python 02d_response_capture.py --split test \
       --locked-coefs-from ../results/best_coefs_tune_aggregate.json
python over_correction_check.py --split test \
       --locked-coefs-from ../results/best_coefs_tune_aggregate.json
python ../paper/scripts/build_all.py --skip-multiseed
python ../paper/scripts/fill_results.py
```

Detailed walk-through, troubleshooting, and H100 budget breakdown:
`experiment-main/README.md`.

## References

- **Model.** Google, *Gemma 2 27B Instruct* (gated). https://huggingface.co/google/gemma-2-27b-it
- **Steering library.** safety-research, *assistant-axis*. https://github.com/safety-research/assistant-axis
- **Pre-computed vectors.** lu-christina, *assistant-axis-vectors* (HF dataset). https://huggingface.co/datasets/lu-christina/assistant-axis-vectors
- **Sycophancy eval + CAA training data.** Anthropic, *evals*. https://github.com/anthropics/evals/tree/main/sycophancy
- **CAA method.** Rimsky et al. 2024, *Steering Llama 2 via Contrastive Activation Addition*. https://arxiv.org/abs/2312.06681
- **philpapers2020 A/B preferences.** Perez et al. 2023, *Discovering Language Model Behaviors with Model-Written Evaluations*. https://arxiv.org/abs/2212.09251

## License and provenance

Pre-computed role vectors and sycophancy datasets are downloaded from their
original sources and are not redistributed in this repository (see
`experiment-main/.gitignore`). All code and derived results are released here
for reproduction and review.
