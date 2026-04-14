# General Persona Directions Reduce Sycophancy via Activation Steering

We show that general-purpose persona directions -- extracted from open-ended
role-playing, not from sycophancy data -- reduce sycophantic behavior in
**Gemma 2 27B Instruct**, and we decompose why this works geometrically and
mechanistically.

## What this experiment does (start to finish)

### The question

Can general persona vectors (skeptic, judge, devil's advocate, etc.) reduce
sycophancy as effectively as a targeted sycophancy-specific vector (CAA)?
And if so, how does each vector reduce it -- through healthy disagreement,
neutral hedging, or model degradation?

### The method

We use **activation steering**: at inference time, we add a scaled direction
vector to the model's residual stream at layer 22 and measure how the model's
behavior changes on a counterbalanced sycophancy benchmark.

### The experiment structure (5 parts)

**Part 1 -- Steering to reduce sycophancy:**
Sweep 16+ steering conditions (6 critical roles expected to decrease sycophancy,
4 conformist roles expected to increase it, 1 CAA targeted vector, 10 random
controls) across 13 coefficient magnitudes on 300 counterbalanced A/B questions
from Anthropic's philpapers2020 dataset. Measure binary sycophancy rate and
continuous sycophancy logit.

**Part 2 -- CAA sycophancy vector extraction:**
Following Rimsky et al. (2024), extract a targeted sycophancy direction from
NLP survey + political typology datasets (held out from evaluation). This is
the "ground truth" sycophancy direction for comparison.

**Part 3 -- Geometric analysis:**
Compute pairwise cosine similarities between all vectors. Do critical roles
cluster together? Is the CAA vector closer to the critical cluster? Does
cosine similarity with CAA predict behavioral effectiveness?

**Part 4 -- Decomposition and ablation:**
For each role vector, decompose into its CAA-aligned component (the part
that points in the sycophancy direction) and its residual (everything
perpendicular to sycophancy). Test each component separately to determine
whether role vectors work purely because they overlap with the sycophancy
direction, or whether there are independent anti-sycophancy mechanisms.

**Part 5 -- Mechanistic analysis:**
Track the model's position on the Assistant Axis during evaluation. Does
axis projection predict sycophantic vs honest behavior? Does steering
shift the projection in the expected direction? Do response-token
projections correlate more strongly with behavior than prompt-token
projections?

---

## Running on Lambda GPU

### Prerequisites

- **GPU**: ~55 GB VRAM (1x H100 80GB or 1x A100 80GB)
- **Disk**: ~50 GB (model weights + vectors + results)
- **Time**: ~10-12 hours total for full experiment

### Step-by-step setup

```bash
# 1. SSH into your Lambda instance
ssh ubuntu@<your-lambda-ip>

# 2. Clone the repo
cd /home/ubuntu
git clone <your-repo-url> experiment
cd experiment

# 3. Install dependencies
pip install torch transformers accelerate huggingface_hub datasets \
            scipy scikit-learn statsmodels matplotlib seaborn

# 4. HuggingFace auth (Gemma 2 27B is gated -- request access first)
huggingface-cli login
# paste a token that has access to google/gemma-2-27b-it

# 5. Clone the upstream steering library
git clone https://github.com/safety-research/assistant-axis.git /home/ubuntu/assistant-axis

# 6. Set environment variables (add to ~/.bashrc for persistence)
export EXPERIMENT_ROOT=/home/ubuntu/experiment
export ASSISTANT_AXIS_PATH=/home/ubuntu/assistant-axis
```

### Running the experiment

All commands run from the `scripts/` directory:

```bash
cd /home/ubuntu/experiment/scripts
```

#### Phase 1: Setup (~15 min, loads model once for smoke test)

```bash
# Download vectors + datasets, parse philpapers2020, run sanity check
python 00_setup.py

# Download the REAL philpapers2020 data (HF mirror has wrong content)
curl -sLk "https://api.github.com/repos/anthropics/evals/git/blobs/5525210614d4f26b1732042e7dcb7210d23fe5aa" \
     -H "Accept: application/vnd.github.raw" \
     -o ../data/sycophancy/sycophancy_on_philpapers2020.jsonl

# Also download NLP survey + political typology (for CAA extraction)
# These should already be downloaded by 00_setup.py via HuggingFace,
# but verify they exist:
ls ../data/sycophancy/sycophancy_on_nlp_survey.jsonl
ls ../data/sycophancy/sycophancy_on_political_typology.jsonl

# Build the counterbalanced eval set (300 base x 2 orderings = 600 rows)
python 00b_rebuild_eval.py
```

#### Phase 2: Vector preparation (~30 min for CAA, ~1 min for roles)

```bash
# Extract CAA sycophancy vector from training datasets
# This loads the model and runs ~800 forward pass pairs
python 02b_extract_caa.py

# Prepare all steering vectors: axis + 9 roles + CAA + 10 randoms
# Also computes decomposition (CAA-aligned component + residual)
python 01_prepare_steering_vectors.py
```

#### Phase 3: Main evaluation (~6-8 hours)

**Option A: Full run (no tune/test split)**
```bash
python 02_evaluate_steering.py
# Optional: --max-base 20 for a quick smoke test first
# Optional: --resume to restart from checkpoints
```

**Option B: Tune/test workflow (recommended for publication)**
```bash
# Run on tune split (50% of base questions) -- ~3-4 hours
python 02_evaluate_steering.py --split tune

# Analyze tune results to see best coefficients
python 03_analysis.py --split tune

# Run on held-out test split -- ~3-4 hours
python 02_evaluate_steering.py --split test

# Final analysis on test data (these are the reportable numbers)
python 03_analysis.py --split test
```

#### Phase 4: Analysis (~5 min, CPU only)

```bash
# Generate all figures + statistical tests + summary
python 03_analysis.py
# or: python 03_analysis.py --split test  (for test-split results)

# Structured over-correction eval (ground-truth probes) -- ~30 min
python over_correction_check.py

# Free-form generation comparison -- ~20 min
python qual_check.py
```

#### Phase 5: Multi-seed robustness (optional, ~30-40 hours)

```bash
# Run the full pipeline across 5 different base-question subsamples
python run_multiseed.py --seeds 42 7 123 456 789
```

### Monitoring a long run

```bash
# In a separate terminal/tmux pane:
tail -f /home/ubuntu/experiment/results/checkpoints/*.json | head -1
# Or check progress by looking at checkpoint files:
ls -la /home/ubuntu/experiment/results/checkpoints/
```

### Expected outputs

After a full run, you'll have:

```
results/
  summary.txt                    -- start here: human-readable results
  statistical_tests.json         -- all tests with adjusted p-values
  sycophancy_rates.json          -- per-cell rates and logits
  degradation_flags.json         -- which cells are degraded
  vector_cosine_similarities.json
  over_correction_eval.json      -- structured ground-truth probe results
  tune_test_split.json           -- which questions went where

figures/
  fig1_steering_curves.png       -- sycophancy vs coefficient (main figure)
  fig2_projection_distributions.png
  fig3_projection_shift.png
  fig4_best_comparison.png       -- best per condition with bootstrap CI
  fig5_vector_similarities.png   -- cosine heatmap
  fig6_persona_space_pca.png     -- PCA of steering vectors
```

---

## Repo layout

```
.
├── README.md
├── scripts/
│   ├── config.py                   # all constants (paths, model, coefficients, roles)
│   ├── 00_setup.py                 # download vectors + datasets, sanity check
│   ├── 00b_rebuild_eval.py         # counterbalanced eval set (supports --seed)
│   ├── 01_prepare_steering_vectors.py  # all vectors + decomposition + cosine matrix
│   ├── 02_evaluate_steering.py     # main eval (supports --split tune|test)
│   ├── 02b_extract_caa.py          # CAA sycophancy vector extraction
│   ├── 03_analysis.py              # figures + stats + decomposition + PCA
│   ├── over_correction_check.py    # structured ground-truth probes (16 claims)
│   ├── qual_check.py               # free-form generation comparison
│   ├── find_skeptic_agreement.py   # find where skeptic agrees with user
│   ├── pilot_debug.py              # verify hooks and sign convention
│   ├── pilot_scale.py              # find coefficient regime
│   └── run_multiseed.py            # multi-seed experiment runner
│
├── vectors/steering/               # unit-normalized vectors (produced by scripts)
├── data/                           # eval datasets
└── results/                        # all outputs
```

---

## Key design decisions

### Counterbalancing
Gemma 2 27B has a ~93% positional A-bias. Every base question is evaluated
in both A/B orderings. The A-bias cancels in the mean.

### Tune/test split
Best coefficient selection and final reporting use different data splits
(at the base-question level, so counterbalanced pairs stay together).
This prevents selection bias.

### 10 random controls
Random vectors are averaged to produce a stable control baseline with
uncertainty bands, rather than relying on a single random draw.

### Statistical framework
- Primary test: Paired Wilcoxon signed-rank on base-level syc_logit
- Multiple comparison correction: Holm-Bonferroni
- Dose-response: Row-level Spearman (not 6-point aggregate)
- McNemar: exact test when off-diagonal cells < 5
- p-value underflow: guarded (never reports 0.0)

### Bidirectional control
Critical roles (skeptic, judge, etc.) are expected to decrease sycophancy.
Conformist roles (servant, diplomat, etc.) are expected to increase it.
If both directions work, persona steering genuinely controls the sycophancy
axis -- it's not just noise.

### CAA comparison
The CAA vector (Rimsky et al. 2024) is the targeted sycophancy-specific
baseline. It is extracted from different datasets than the eval set.
The decomposition analysis reveals whether role vectors work by overlapping
with the CAA direction or through independent mechanisms.
