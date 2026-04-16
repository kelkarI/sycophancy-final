"""
Shared configuration for the sycophancy steering experiment.

All scripts import constants from here instead of hardcoding them.
Paths can be overridden via environment variables.
"""
import os

# ---- Paths (override via env vars for portability) ----
ROOT = os.environ.get("EXPERIMENT_ROOT", "/home/ubuntu/experiment")
ASSISTANT_AXIS_PATH = os.environ.get(
    "ASSISTANT_AXIS_PATH", "/home/ubuntu/assistant-axis"
)

# ---- Model ----
MODEL_NAME = "google/gemma-2-27b-it"
TARGET_LAYER = 22
A_TOKEN_ID = 235280
B_TOKEN_ID = 235305

# ---- Steering conditions ----
# Critical roles: expected to DECREASE sycophancy (push toward independent thinking)
CRITICAL_ROLES = ["devils_advocate", "contrarian", "skeptic", "judge", "scientist"]

# Conformist roles: expected to INCREASE sycophancy (push toward deference).
# Tests bidirectionality: if critical roles reduce syc, conformist roles should increase it.
#
# The original list ("servant", "diplomat", "disciple", "peacemaker") was not
# available in lu-christina/assistant-axis-vectors, so we substitute the closest
# conflict-avoidant / agreement-seeking roles that ARE pre-computed in that
# dataset. All four are defensible conformist personas (peacekeeper avoids
# conflict, pacifist avoids confrontation, collaborator agrees to work together,
# facilitator enables others without pushing back). Revision work could generate
# the original four via the safety-research/assistant-axis pipeline, but that
# costs ~4-8 extra H100 hours and is out of scope for the first submission.
CONFORMIST_ROLES = ["peacekeeper", "pacifist", "collaborator", "facilitator"]

ROLE_NAMES = CRITICAL_ROLES + CONFORMIST_ROLES

N_RANDOM_VECTORS = 10  # number of random control vectors
RANDOM_SEED_BASE = 1234  # seed for first random vector; i-th uses seed + i

# CONDITIONS is built dynamically to include all conditions
CONDITIONS_REAL = ["assistant_axis"] + ROLE_NAMES + ["caa"]
CONDITIONS_CRITICAL = ["assistant_axis"] + CRITICAL_ROLES + ["caa"]
CONDITIONS_CONFORMIST = CONFORMIST_ROLES
CONDITIONS_RANDOM = [f"random_{i}" for i in range(N_RANDOM_VECTORS)]
CONDITIONS = CONDITIONS_REAL + CONDITIONS_RANDOM

# ---- Coefficient sweep ----
# Reduced from 13 points to 9 to fit the multi-seed GPU budget while keeping
# dose-response curves smooth. We dropped {-3000, -200, +200, +3000} since
# those values lie between neighbouring points that are already sampled
# and carried little extra information in the pilot runs. The full 13-point
# sweep is available under COEFFICIENTS_FULL for ablations.
COEFFICIENTS = [
    -5000.0, -2000.0, -1000.0, -500.0,
    0.0,
    500.0, 1000.0, 2000.0, 5000.0,
]
COEFFICIENTS_FULL = [
    -5000.0, -3000.0, -2000.0, -1000.0, -500.0, -200.0,
    0.0,
    200.0, 500.0, 1000.0, 2000.0, 3000.0, 5000.0,
]

# ---- Eval set ----
EVAL_N = 300       # number of base questions
EVAL_SEED = 42     # seed for sampling base questions

# ---- CAA extraction ----
# NLP survey + political typology are used for CAA extraction (training set).
# philpapers2020 is the held-out test set.
# NOTE: the real filename in anthropics/evals is *_political_typology_quiz.jsonl,
# not *_political_typology.jsonl. The earlier filename silently halved the
# CAA training set because 02b_extract_caa.py warned-and-continued.
CAA_DATASETS = [
    "sycophancy_on_nlp_survey.jsonl",
    "sycophancy_on_political_typology_quiz.jsonl",
]
EVAL_DATASET = "sycophancy_on_philpapers2020.jsonl"

# ---- Tune / test split ----
TUNE_FRACTION = 0.5   # fraction of base questions used for tuning
TUNE_TEST_SEED = 99   # seed for the tune/test split (different from eval sampling)

# ---- Degradation detection ----
DEGRAD_RATE_TOL = 0.03     # binary rate within 3 pp of 50%
DEGRAD_LOGIT_TOL = 0.10    # logit within 0.10 of random-mean at same coeff

# ---- Multiple comparison correction ----
MCC_METHOD = "holm"  # "holm", "bonferroni", or "fdr_bh"

# ---- Labels & colours for plots ----
COLORS = {
    "assistant_axis": "#1f77b4",
    "caa":            "#e377c2",
    # Critical roles
    "devils_advocate": "#d62728",
    "contrarian": "#2ca02c",
    "skeptic": "#9467bd",
    "judge": "#ff7f0e",
    "scientist": "#17becf",
    # Conformist roles
    "peacekeeper": "#8c564b",
    "pacifist":    "#bcbd22",
    "collaborator": "#e7969c",
    "facilitator": "#aec7e8",
}
for i in range(N_RANDOM_VECTORS):
    COLORS[f"random_{i}"] = "#7f7f7f"

LABELS = {
    "assistant_axis": "Assistant Axis",
    "caa":            "CAA (targeted)",
    # Critical roles
    "devils_advocate": "Devil's Advocate",
    "contrarian": "Contrarian",
    "skeptic": "Skeptic",
    "judge": "Judge",
    "scientist": "Scientist",
    # Conformist roles
    "peacekeeper": "Peacekeeper",
    "pacifist":    "Pacifist",
    "collaborator": "Collaborator",
    "facilitator": "Facilitator",
}
for i in range(N_RANDOM_VECTORS):
    LABELS[f"random_{i}"] = f"Random {i}" if N_RANDOM_VECTORS > 1 else "Random (ctrl)"


# ---- Expected direction of effect per condition ----
# Used by the direction-aware best-coefficient selector in 03_analysis.py and by
# paper/scripts/* so that conformist roles are not evaluated with the wrong
# operating point. See GAP_ANALYSIS.md Objective 1, item 1.
#
#   "decrease": steering this vector should reduce sycophancy (lower syc_logit).
#               Applies to assistant_axis, critical roles, and CAA (CAA points
#               FROM honest TOWARD sycophantic, so a negative coefficient
#               reduces sycophancy -- the selector handles the sign).
#   "increase": steering this vector should raise sycophancy (bidirectionality
#               check -- conformist roles).
#   "unsigned": no prior; pick the coefficient with the largest absolute delta
#               from the random mean (random controls).
EXPECTED_DIRECTION = {
    "assistant_axis": "decrease",
    "caa":            "decrease",
}
for _r in CRITICAL_ROLES:
    EXPECTED_DIRECTION[_r] = "decrease"
for _r in CONFORMIST_ROLES:
    EXPECTED_DIRECTION[_r] = "increase"
for _i in range(N_RANDOM_VECTORS):
    EXPECTED_DIRECTION[f"random_{_i}"] = "unsigned"
