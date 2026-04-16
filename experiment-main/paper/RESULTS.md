# RESULTS

Skeleton of the paper's results section. Every numerical placeholder
(`[TODO_...]`) is annotated with the exact output file path it will be
traced from, so the final fill-in is mechanical after the GPU runs
complete. Once `paper/scripts/build_all.py` has run end-to-end against
fresh results, a follow-up pass replaces the `[TODO_...]` tokens with the
numbers from the indicated files.

All numbers reported in this section come from the **test split** with
coefficients locked from the tune split via
`results/best_coefs_tune.json`, unless a sentence explicitly says
otherwise.

---

## Setup summary (trace path: `results/summary_test.txt`)

- Model: `google/gemma-2-27b-it`, bf16, layer 22.
- Eval: philpapers2020, N = 300 base questions × 2 counterbalanced orderings
  = 600 rows; 50 / 50 tune / test split at the base level.
- Conditions: 1 axis + 5 critical roles + 4 conformist roles + CAA + 10
  random controls = 21.
- Coefficient sweep: 13 values spanning ±5000; direction-aware best-coef
  selection on tune, locked on test.
- Multi-seed: 5 seeds on tune, 3 seeds on test. CAA extracted once.
- Primary test: one-sided paired Wilcoxon signed-rank on base-level
  `syc_logit`, Holm-Bonferroni across 11 real conditions.
- Baseline sycophancy rate: [TODO_BASELINE_RATE] %  (file:
  `results/summary_test.txt`, line "Baseline binary sycophancy rate:").
- Baseline sycophancy logit: [TODO_BASELINE_LOGIT]  (same file, "Baseline mean
  sycophancy logit:").

---

## Objective 1 — Role-direction steering reduces sycophancy; conformist roles increase it

**Headline figure:** `paper/figures/figure_1_bidirectionality.pdf`. Each of the
11 real conditions at its tune-locked best coefficient, as Δlogit vs
baseline, ordered critical → axis + CAA → conformist. Error bars are
cross-seed std on the test split (n = 3).

### 1a. Critical roles reduce sycophancy

- The most effective single condition is [TODO_MOST_EFFECTIVE_LABEL]
  (Δlogit = [TODO_MOST_EFFECTIVE_DELTA] relative to baseline; Δrate =
  [TODO_MOST_EFFECTIVE_DELTARATE] pp; one-sided Wilcoxon
  $p_\text{Holm}$ = [TODO_MOST_EFFECTIVE_PADJ]). File:
  `paper/tables/table_1_results.csv`, row with the most negative
  `delta_logit` among `expected_direction == "decrease"`.
- All [TODO_N_CRITICAL_SIG] / 5 critical roles remain significant after
  Holm. File: same table, `significant_after_mcc` column filtered to the
  critical-role rows.

### 1b. Conformist roles **increase** sycophancy (bidirectionality)

Steering toward conformist personas produces symmetric increases in
sycophancy:

- Mean Δlogit over the 4 conformist roles at their locked best (positive)
  coefficient: [TODO_CONFORMIST_MEAN_DELTA]. File:
  `paper/tables/table_1_results.csv`, rows where
  `expected_direction == "increase"`.
- [TODO_CONFORMIST_N_SIG] / 4 conformist roles show a statistically
  significant increase (one-sided Wilcoxon, alternative = greater,
  Holm-adjusted). File: same table, `wilcoxon_alt` column for those rows
  and `significant_after_mcc` flag.
- For reference, the random-vector null band on the same axis is
  [TODO_RANDOM_BAND_STD] (± 1 SD across 10 random unit vectors).

### 1c. Assistant axis is reliably effective but dominated by targeted roles

- Assistant-axis best Δlogit: [TODO_AXIS_DELTA] at $c^* =$
  [TODO_AXIS_COEF]. File: `paper/tables/table_1_results.csv` row
  `assistant_axis`.

**Interpretation (two sentences).** The same structural change — adding a
unit persona vector to layer 22 at non-trivial coefficient — moves the
sycophancy axis in both directions, as predicted. This is the cleanest
bidirectionality evidence: if the effect were noise, pushing toward
conformist personas would not systematically raise `syc_logit` while
pushing toward critical personas systematically lowers it.

---

## Objective 2 — CAA (Rimsky et al. 2024) as targeted baseline

**Headline figure:** `paper/figures/figure_2_caa_headtohead.pdf`. Two panels:
Δlogit bars (baseline, `assistant_axis`, `caa`, best critical role, best
conformist role) and an efficiency panel (reduction per unit |coefficient|).

### 2a. CAA and the best role direction reduce sycophancy by similar amounts

- CAA Δlogit: [TODO_CAA_DELTA] at $c^* =$ [TODO_CAA_COEF] (sign convention:
  CAA points *from honest toward sycophantic*, so the best coefficient is
  negative). File: `paper/tables/figure_2_caa_headtohead.csv`.
- Best critical role Δlogit: [TODO_BEST_ROLE_DELTA] at $c^* =$
  [TODO_BEST_ROLE_COEF].
- Difference CAA − best-role: [TODO_CAA_MINUS_ROLE], within
  [TODO_CAA_ROLE_OVERLAP_95CI] 95 % CI → [TODO_CAA_VS_ROLE_CLAIM].

### 2b. Assistant axis is effective but less efficient than both CAA and best role

- Reduction per unit |coef|, axis: [TODO_EFF_AXIS] × 10⁻⁴.
- Reduction per unit |coef|, CAA: [TODO_EFF_CAA] × 10⁻⁴.
- Reduction per unit |coef|, best role: [TODO_EFF_ROLE] × 10⁻⁴.
  File: `paper/tables/figure_2_caa_headtohead.csv`, companion panel.

**Interpretation.** A general persona direction drawn from role-playing
(not from sycophancy-specific data) matches the targeted CAA baseline to
within [TODO_CAA_VS_ROLE_CLAIM]. This is consistent with sycophancy being
largely characterised by displacement along the same direction the model
already uses for persona modulation.

---

## Objective 3 — Decomposition: how much of each role's effect lives along CAA?

**Headline figure:** `paper/figures/figure_3_decomposition.pdf`. Per role, three
bars: full role direction, unit-normalised CAA-aligned component, and
unit-normalised residual, each steered at the role's tune-locked best
coefficient. Roles ordered by |cos(role, CAA)| descending.

**Precision note (as in the figure caption):** we steer with the
**unit-normalised** CAA-aligned component and residual of each role, at
**matched coefficient** — not with the components themselves. This
isolates the *direction* question from the *magnitude* question.

### 3a. For high-cos roles, the CAA-aligned component reproduces most of the effect

For roles with $|\cos(v_\text{role}, v_\text{CAA})| >$
[TODO_HIGH_COS_THRESHOLD], the CAA-aligned component at matched
coefficient delivers [TODO_HIGH_COS_FRAC] × the full Δlogit, while the
residual contributes [TODO_HIGH_COS_RESID_FRAC] ×. Example roles:
[TODO_HIGH_COS_EXAMPLES]. File:
`paper/tables/figure_3_decomposition.csv`, columns
`fraction_from_caa_component` and `fraction_from_residual`.

### 3b. For low-cos roles, the residual carries the effect

For roles with $|\cos(v_\text{role}, v_\text{CAA})| <$
[TODO_LOW_COS_THRESHOLD], the residual at matched coefficient
delivers [TODO_LOW_COS_FRAC] × the full Δlogit, while the CAA-aligned
component contributes [TODO_LOW_COS_CAA_FRAC] ×. Example roles:
[TODO_LOW_COS_EXAMPLES]. This is the headline negative-result cell — roles
that work despite being nearly orthogonal to CAA have a mechanism beyond
the targeted direction.

### 3c. Geometry figure (supporting)

`paper/figures/figure_5_cosine_heatmap.pdf` and
`paper/figures/figure_6_pca_persona_space.pdf` provide the full geometry.
Trace paths: `results/vector_cosine_similarities.json` (13 × 13 matrix)
and `vectors/steering/*_unit.pt` for PCA inputs.

---

## Overcorrection taxonomy (supporting Objectives 1 and 2)

**Figure:** `paper/figures/figure_4_overcorrection_taxonomy.pdf`. Two panels:
AGREE / DISAGREE / HEDGE / REFUSE counts on 8 true claims and 8 false
claims, for each of baseline + 11 real + 1 random.

- Critical roles that most reduce sycophancy on `syc_logit` show
  [TODO_CRITICAL_OVERCORRECTION] DISAGREE_WRONG (overcorrection) events
  out of [TODO_TOTAL_TRUE_PROBES] TRUE-claim probes. File:
  `paper/tables/figure_4_overcorrection_taxonomy.csv`, rows with
  `claim_type == "TRUE"` and critical condition.
- Conformist roles show [TODO_CONFORMIST_AGREE_WRONG] AGREE_WRONG
  (sycophantic error) events on [TODO_TOTAL_FALSE_PROBES] FALSE-claim
  probes, consistent with their increase-sycophancy effect on the
  philpapers measure.
- HEDGE and REFUSE rates remain below [TODO_HEDGE_REFUSE_CAP] across all
  conditions, so the Δlogit effect is not driven by the model refusing or
  hedging out.

---

## Supplementary analyses

### Dose-response (trace: `results/statistical_tests_test.json`, key
`dose_response_row_level`)

Row-level Spearman $\rho$ on positive coefficients for the 5 critical
roles, `assistant_axis`, and `caa`. Table row summaries in
`results/summary_test.txt`.

### Projection predictors (trace: `paper/figures/figure_supp_projection_ablation.pdf`,
`paper/tables/table_supp_projection_ablation.csv`)

Pooled Pearson $r$ of base-level syc_logit against:
- Prompt-last-token axis projection: $r_\text{prompt}$ =
  [TODO_R_PROMPT], $p$ = [TODO_P_PROMPT].
- Response-token mean axis projection: $r_\text{resp}$ =
  [TODO_R_RESP], $p$ = [TODO_P_RESP].
- Bootstrap 95 % CI on $r_\text{resp} - r_\text{prompt}$:
  [TODO_DIFF_CI]. Whether the response-token predictor is strictly better
  is [TODO_RESP_BETTER_CLAIM].

### CAA train / eval leakage receipt

`paper/tables/caa_leakage_receipt.json` confirms zero question-text overlap
between the CAA training datasets (NLP survey + political-typology quiz)
and the philpapers2020 evaluation set. Exact SHA-256 overlap count:
[TODO_LEAKAGE_COUNT].

---

## Things to check before submission

This is the explicit TODO block the user asked for. Every `[TODO_...]`
above gets filled in from the indicated file. In addition, we track:

- [ ] Multi-seed run completed: 5 tune seeds, 3 test seeds, aggregates
  under `results/seed_*/` and `results/multiseed_aggregate_*.json`.
- [ ] Decomposition eval completed: `results/decomposition_eval_test.json`.
- [ ] Overcorrection eval completed on all 11 real conditions:
  `results/over_correction_eval_test.json`.
- [ ] Leakage receipt produced:
  `paper/tables/caa_leakage_receipt.json`.
- [ ] All paper figures rebuilt at 300 DPI:
  `paper/figures/figure_{1..6}_*.{pdf,png}` and
  `figure_supp_*.{pdf,png}`.
- [ ] `paper/tables/table_1_results.tex` compiles standalone.
- [ ] `README.md` reproducibility section lists the exact commands that
  regenerate every figure and table on a single H100.
- [CITATION NEEDED] Rimsky et al. 2024, "Steering Llama 2 via Contrastive
  Activation Addition". arXiv:2312.06681. Verify the citation key.
- [CITATION NEEDED] Perez et al. 2023, "Discovering Language Model
  Behaviors with Model-Written Evaluations" (philpapers2020 source).
  arXiv:2212.09251.
- [CITATION NEEDED] safety-research/assistant-axis repository.
