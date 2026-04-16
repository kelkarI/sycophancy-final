# METHODS

## Model

We use **Gemma 2 27B Instruct** (`google/gemma-2-27b-it` on HuggingFace),
loaded in `bfloat16` with `device_map="auto"`. All interventions target the
residual stream at the output of transformer block **22** of 46
(`model.model.layers[22]`). Answer tokens `A` (id 235280) and `B` (id 235305)
are single-token in the Gemma 2 tokenizer; we read log-probabilities at the
last prompt-token position.

## Steering

Activation steering uses the `ActivationSteering` context manager from
`safety-research/assistant-axis`. For a steering vector $v \in
\mathbb{R}^{d}$ and coefficient $c \in \mathbb{R}$, the layer-22 residual
hidden state $h$ is replaced by $h + c\,v$ at every token position for every
forward pass inside the context. All $v$ are $\ell_2$-unit-normalised prior
to steering, so the coefficient carries the entire magnitude.

### Sign convention

Steering vectors are constructed so that the coefficient is signed
consistently with the intended effect:

- **Assistant axis** $v_\text{axis} = \overline{h}_\text{default} -
  \overline{h}_\text{role}$. Positive coefficient pushes the residual
  toward the default-assistant persona.
- **Role directions** $v_\text{role} = \overline{h}_\text{role} -
  \overline{h}_\text{default}$. Positive coefficient pushes toward the role.
- **CAA vector** (Rimsky et al. 2024) $v_\text{CAA} =
  \overline{h}_\text{syc} - \overline{h}_\text{hon}$. Points
  *from honest toward sycophantic*; the best coefficient that reduces
  sycophancy is therefore **negative**.

## Conditions (21)

| Group | Names | Expected direction |
|---|---|---|
| Broad axis | `assistant_axis` | decrease sycophancy |
| Critical roles | `devils_advocate`, `contrarian`, `skeptic`, `judge`, `scientist` | decrease |
| Conformist roles | `peacekeeper`, `pacifist`, `collaborator`, `facilitator` | **increase** |
| Targeted baseline | `caa` | decrease |
| Random controls | `random_0..random_9` | unsigned |

The conformist roles selected above are conflict-avoidant / agreement-seeking
personas present in the pre-computed `lu-christina/assistant-axis-vectors`
dataset for Gemma 2 27B. An earlier draft listed `{servant, diplomat,
disciple, peacemaker}`; those role vectors were not available in the
released dataset, so we substitute the four closest conformist-flavoured
roles that are. The research claim — *steering toward deferential personas
increases sycophancy* — is what the substitute roles test, so the
bidirectionality evidence is preserved. Repeating the experiment with the
original four roles would require running the
`safety-research/assistant-axis` pipeline to extract them ourselves
(~1–2 H100 hours per role), which we leave for a revision.

Critical and conformist roles provide the **bidirectionality** check: if
persona steering genuinely controls the sycophancy axis, conformist roles
should produce the symmetric increase.

## Coefficient sweep

$$c \in \{-5000, -3000, -2000, -1000, -500, -200, 0, 200, 500, 1000, 2000, 3000, 5000\}.$$

## Evaluation set

Anthropic/evals **philpapers2020** sycophancy evaluation. After filtering to
two-choice (A/B) questions and subsampling 300 base questions with seed 42,
each base question is evaluated in **both orderings** (original and A/B
swapped with sycophancy label flipped). Result: 600 rows, paired by `base_id`.
Counterbalancing cancels Gemma's strong positional A-bias in the base-level
means.

## Tune / test split

The 300 base questions are split 50/50 (seed 99) at the **base-question
level** so counterbalanced pairs stay together. Coefficient selection and
the `best_coefs` JSON are produced on the tune split; the test split is
evaluated with those coefficients **locked** via
`03_analysis.py --locked-coefs-from results/best_coefs_tune.json`.

## Multi-seed

The eval subsample and the tune/test split are both regenerated under
multiple seeds (`run_multiseed.py --seeds ...`). We use **5 seeds** on the
tune split (stabilising coefficient selection) and **3 seeds** on the test
split (giving the cross-seed error bars reported throughout). The CAA
direction is extracted **once** up-front and reused across all seeds, so
the `caa` error bars reflect eval-sampling noise, not CAA-extraction noise.

## CAA extraction (Rimsky et al. 2024)

Contrastive Activation Addition. We append the sycophantic answer token to
each prompt, run a forward pass, and capture the last-position residual at
layer 22; we do the same with the honest answer token. The CAA vector is
$$v_\text{CAA} = \frac{1}{N}\sum_i h_i^{\text{syc}} - \frac{1}{N}\sum_i h_i^{\text{hon}}$$
over $N$ A/B pairs from the **NLP survey** + **political typology quiz**
sycophancy datasets (`sycophancy_on_nlp_survey.jsonl`,
`sycophancy_on_political_typology_quiz.jsonl`). These are disjoint from the
philpapers2020 evaluation set; we ship a hash-overlap receipt as
`paper/tables/caa_leakage_receipt.{json,csv}`.

## CAA decomposition (behavioural)

For each decomposable condition $C \in \{\text{assistant\_axis}\} \cup
\text{ROLE\_NAMES}$, we project $v_C$ onto $v_\text{CAA}$:
$$v_C^{\parallel} = (v_C \cdot v_\text{CAA})\,v_\text{CAA}, \quad
  v_C^{\perp} = v_C - v_C^{\parallel}.$$
We then **unit-normalise both pieces separately** ($\hat{v}_C^{\parallel}$,
$\hat{v}_C^{\perp}$) and steer the model with each at the **same locked
coefficient $c^*_C$** used for the full $v_C$. This isolates the *direction*
question (does the role's effect live along CAA?) from the *magnitude*
question (how much of $v_C$ lies along CAA?).

Precision, repeated from the script docstring and reported verbatim in the
figure caption: **we steer with the unit-normalised CAA-aligned component
and residual of each role, at matched coefficient — not with the
components themselves.**

## Statistical tests

- **Primary significance test.** Paired one-sided Wilcoxon signed-rank
  on base-level mean `syc_logit` (best-coefficient cell vs. baseline),
  $n = \text{number of base questions}$. Alternative is *less* for
  decrease-expected conditions and *greater* for increase-expected
  (conformist) conditions. We also report a two-sided $p$-value as a
  secondary column.
- **Secondary test.** McNemar on paired binary sycophancy choices; exact
  test when $\min(b_{01}, b_{10}) < 5$, continuity-corrected $\chi^2$
  otherwise.
- **Dose response.** Row-level Spearman over positive coefficients
  ($\rho$ on $\sim 3600$ points per condition), not the aggregate
  6-point Spearman which mechanically hits $\rho \approx -1$.
- **Projection predictors.** Pooled Pearson $r$ of base-level
  `syc_logit` against (a) analytically-shifted prompt-last-token axis
  projection and (b) empirical response-token mean axis projection
  captured from 8 greedy generation tokens. A bootstrap 95 % CI on the
  difference $r_\text{resp} - r_\text{prompt}$ is reported.
- **Multiple-comparison correction.** Holm-Bonferroni across the 11
  real conditions in each test family (primary Wilcoxon, McNemar). We
  additionally report a conservative global correction in the text for
  the combined set of primary claims.
- **Effect size.** Baseline-minus-steered Δlogit and Δrate (pp);
  Cohen's $d$ between highest- and lowest-syc-quartile baseline
  projections; bootstrap 95 % CI on per-condition Δlogit.
- **Degradation flag.** A cell is marked degraded when the binary rate
  is within 3 pp of 50 % **and** the mean logit is within 0.10 of the
  random-vector mean at the same coefficient. Degraded cells are
  excluded from the "most-effective" summary.
- **$p$-value underflow.** Guarded with a $10^{-300}$ floor; displayed
  as `< 1e-15`.

## Qualitative / overcorrection taxonomy

16 structured true-vs-false claim probes, generated under every of the 11
real conditions + one random control at the condition's locked best
coefficient. Each response is classified by keyword heuristic into one of
`{AGREE_CORRECT, DISAGREE_CORRECT, AGREE_WRONG, DISAGREE_WRONG, HEDGE,
REFUSE}` and aggregated per condition. The classifier's limitations are
documented in `LIMITATIONS.md`.

## Reproducibility

Every numerical claim in `RESULTS.md` is traced to a specific output file
path. End-to-end commands, their runtimes on an H100-class GPU, and the
expected outputs per step are listed in `README.md` and
`REPRODUCIBILITY.md`.
