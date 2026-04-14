#!/usr/bin/env python3
"""Generate a PDF report comparing the original repo to the updated repo."""

from fpdf import FPDF


class Report(FPDF):
    def header(self):
        if self.page_no() > 1:
            self.set_font("Helvetica", "I", 9)
            self.set_text_color(120, 120, 120)
            self.cell(0, 8, "Updates to Ishaan Repo", align="R",
                      new_x="LMARGIN", new_y="NEXT")
            self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
            self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 9)
        self.set_text_color(120, 120, 120)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")

    def section_title(self, title):
        self.set_font("Helvetica", "B", 15)
        self.set_text_color(0, 0, 0)
        self.ln(4)
        self.multi_cell(0, 8, title, new_x="LMARGIN", new_y="NEXT")
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(4)

    def heading(self, text):
        self.set_font("Helvetica", "B", 12)
        self.set_text_color(30, 30, 30)
        self.ln(2)
        self.multi_cell(0, 7, text, new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

    def sub_heading(self, text):
        self.set_font("Helvetica", "B", 10.5)
        self.set_text_color(50, 50, 50)
        self.multi_cell(0, 6, text, new_x="LMARGIN", new_y="NEXT")
        self.ln(1)

    def body(self, text):
        self.set_font("Helvetica", "", 10.5)
        self.set_text_color(30, 30, 30)
        self.multi_cell(0, 5.5, text, new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

    def bullet(self, text):
        self.set_font("Helvetica", "", 10.5)
        self.set_text_color(30, 30, 30)
        x = self.get_x()
        self.set_x(x + 6)
        self.cell(5, 5.5, "-")
        self.multi_cell(self.w - self.l_margin - self.r_margin - 11, 5.5, text,
                        new_x="LMARGIN", new_y="NEXT")
        self.ln(1)

    def code(self, text):
        self.set_font("Courier", "", 8.5)
        self.set_fill_color(240, 240, 240)
        self.set_text_color(40, 40, 40)
        x = self.get_x()
        self.set_x(x + 4)
        self.multi_cell(self.w - self.l_margin - self.r_margin - 8, 4.5, text,
                        fill=True, new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

    def old_new(self, old, new):
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(180, 30, 30)
        self.cell(12, 5.5, "OLD:")
        self.set_font("Helvetica", "", 9.5)
        self.set_text_color(30, 30, 30)
        self.multi_cell(0, 5.5, old, new_x="LMARGIN", new_y="NEXT")
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(0, 130, 0)
        self.cell(12, 5.5, "NEW:")
        self.set_font("Helvetica", "", 9.5)
        self.set_text_color(30, 30, 30)
        self.multi_cell(0, 5.5, new, new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

    def separator(self):
        self.ln(2)
        y = self.get_y()
        mid = self.w / 2
        self.set_draw_color(180, 180, 180)
        self.line(mid - 40, y, mid + 40, y)
        self.ln(4)


def build():
    pdf = Report()
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=20)

    # ---- TITLE ----
    pdf.add_page()
    pdf.ln(40)
    pdf.set_font("Helvetica", "B", 24)
    pdf.multi_cell(0, 12, "Updates to Ishaan Repo", align="C",
                   new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)
    pdf.set_font("Helvetica", "", 13)
    pdf.set_text_color(80, 80, 80)
    pdf.multi_cell(0, 7,
        "A complete changelog comparing the original experiment-main\n"
        "repository to the updated version.",
        align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(20)
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(60, 60, 60)
    pdf.multi_cell(0, 6,
        "The original repository had 10 scripts and produced a working\n"
        "sycophancy steering experiment with 7 conditions (axis + 5 roles +\n"
        "1 random), basic McNemar tests, and 5 figures.\n\n"
        "The updated repository has 13 scripts, 21 conditions (axis + 9 roles +\n"
        "CAA + 10 randoms), a tune/test split, decomposition analysis, and\n"
        "fixes to every statistical issue identified in the review.\n\n"
        "This document covers every change in detail.",
        align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(15)
    pdf.set_font("Helvetica", "I", 10)
    pdf.set_text_color(120, 120, 120)
    pdf.cell(0, 6, "Generated: 2026-04-14", align="C",
             new_x="LMARGIN", new_y="NEXT")

    # ======================================================================
    # SECTION 1: NEW FILES
    # ======================================================================
    pdf.add_page()
    pdf.section_title("1. New Files Added")

    pdf.heading("config.py (NEW)")
    pdf.body(
        "Centralized configuration file that replaces all hardcoded constants across "
        "every script. The original repo had ROOT = \"/home/ubuntu/experiment\", "
        "MODEL_NAME, TARGET_LAYER, token IDs, and COEFFICIENTS copy-pasted into each "
        "script independently. Now all scripts import from config.py."
    )
    pdf.sub_heading("What it contains")
    pdf.bullet("Paths (ROOT, ASSISTANT_AXIS_PATH) -- overridable via environment variables")
    pdf.bullet("Model constants (MODEL_NAME, TARGET_LAYER, A_TOKEN_ID, B_TOKEN_ID)")
    pdf.bullet("Role lists: CRITICAL_ROLES (5), CONFORMIST_ROLES (4 new), all labels/colors")
    pdf.bullet("N_RANDOM_VECTORS = 10 (was 1)")
    pdf.bullet("TUNE_FRACTION, TUNE_TEST_SEED for tune/test split")
    pdf.bullet("Degradation detection thresholds")
    pdf.bullet("MCC_METHOD = \"holm\" for multiple comparison correction")
    pdf.bullet("CAA_DATASETS list for CAA extraction")

    pdf.separator()

    pdf.heading("02b_extract_caa.py (NEW)")
    pdf.body(
        "Entirely new script that extracts a Contrastive Activation Addition (CAA) "
        "sycophancy vector following Rimsky et al. (2024). This is the targeted "
        "sycophancy-specific baseline that the general persona vectors are compared against."
    )
    pdf.sub_heading("What it does")
    pdf.bullet("Loads NLP survey + political typology A/B pairs (different from the philpapers eval set)")
    pdf.bullet("For each question, runs two forward passes: one with the sycophantic answer appended, one with the honest answer")
    pdf.bullet("Captures activations at layer 22 for both")
    pdf.bullet("Computes CAA = mean(sycophantic_activations) - mean(honest_activations)")
    pdf.bullet("Unit-normalizes and saves as caa_unit.pt")
    pdf.bullet("Computes cosine similarity with the assistant axis for reference")
    pdf.body(
        "The original repo had no CAA comparison at all. This is one of the key "
        "novelty additions: it lets you ask whether general persona directions can "
        "match a purpose-built sycophancy vector."
    )

    pdf.separator()

    pdf.heading("run_multiseed.py (NEW)")
    pdf.body(
        "Orchestrator script that runs the full pipeline (00b -> 02 -> 03) across "
        "multiple random seeds, then aggregates results with cross-seed mean and "
        "standard deviation. The original repo used a single seed (42) and had no "
        "robustness testing."
    )

    # ======================================================================
    # SECTION 2: MODIFIED FILES
    # ======================================================================
    pdf.add_page()
    pdf.section_title("2. Modified Files -- Script by Script")

    # --- 00_setup.py ---
    pdf.heading("00_setup.py")

    pdf.sub_heading("Output filename changed")
    pdf.old_new(
        "Writes eval_data.json (300 rows, no counterbalancing)",
        "Writes eval_data_raw.json -- distinct name so it cannot be confused with "
        "the counterbalanced version that 00b produces"
    )

    pdf.sub_heading("Coefficient range fixed")
    pdf.old_new(
        "setup_info.json recorded coefficient_range as [-4, -3, ..., 4] (stale from earlier iteration)",
        "Now records the actual COEFFICIENTS from config.py: [-5000, ..., 5000]"
    )

    pdf.sub_heading("Imports centralized")
    pdf.old_new(
        "ROOT, MODEL_NAME, TARGET_LAYER, etc. hardcoded at top of file",
        "All imported from config.py"
    )

    pdf.separator()

    # --- 00b_rebuild_eval.py ---
    pdf.heading("00b_rebuild_eval.py")

    pdf.sub_heading("Multi-seed support")
    pdf.old_new(
        "Seed hardcoded as SEED = 42, no CLI args",
        "Accepts --seed and --n-base flags for multi-seed robustness testing"
    )

    pdf.sub_heading("Imports centralized")
    pdf.old_new("Constants hardcoded", "Imported from config.py")

    pdf.separator()

    # --- 01_prepare_steering_vectors.py ---
    pdf.heading("01_prepare_steering_vectors.py")

    pdf.sub_heading("Random vectors: 1 -> 10")
    pdf.old_new(
        "Generated 1 random vector (torch.manual_seed(1234))",
        "Generates 10 independent random vectors (random_0 through random_9) with "
        "consecutive seeds. Backward-compatible: also saves random_unit.pt as alias for random_0"
    )

    pdf.sub_heading("Conformist roles added")
    pdf.old_new(
        "Only 5 critical roles: devils_advocate, contrarian, skeptic, judge, scientist",
        "Now also prepares 4 conformist roles: servant, diplomat, disciple, peacemaker. "
        "These test bidirectionality -- if critical roles reduce sycophancy, conformist "
        "roles should increase it"
    )

    pdf.sub_heading("CAA vector integration")
    pdf.old_new(
        "No CAA vector",
        "If caa_unit.pt exists (from 02b_extract_caa.py), includes it in the cosine "
        "similarity matrix. Also computes the decomposition: for each role vector, "
        "projects onto the CAA direction to get the CAA-aligned component and the "
        "residual, saves both as separate .pt files"
    )

    pdf.separator()

    # --- 02_evaluate_steering.py ---
    pdf.add_page()
    pdf.heading("02_evaluate_steering.py")

    pdf.sub_heading("Tune/test split")
    pdf.old_new(
        "All 300 base questions used for both coefficient selection AND reporting. "
        "This is the #1 experimental design flaw identified in the Issues.pdf review",
        "New --split flag: 'tune' uses 50% of base questions for coefficient selection, "
        "'test' uses the held-out 50% for final reporting. Split at base-question level "
        "so counterbalanced pairs stay together. Saves split info to tune_test_split.json"
    )

    pdf.sub_heading("Schema check")
    pdf.old_new(
        "No validation. If user ran 00_setup.py but forgot 00b, script silently used "
        "the wrong data format and crashed with a confusing KeyError",
        "Checks that eval_data.json has base_id and variant fields. If not, exits with "
        "a clear error message directing the user to run 00b_rebuild_eval.py"
    )

    pdf.sub_heading("Response-token projections")
    pdf.old_new(
        "Only captured axis projection at the last prompt token position",
        "After the logprob measurement, generates 8 response tokens and captures the "
        "mean axis projection across them. Stored as response_projection alongside "
        "the existing axis_projection. This lets the analysis test whether response-token "
        "projections are better predictors of sycophancy than prompt-token projections"
    )

    pdf.sub_heading("Degradation detection")
    pdf.old_new(
        "Flagged degradation when near_tie_frac > 0.8 (i.e., >80% of rows have "
        "|logp(A) - logp(B)| < 0.05). This threshold was unreachable in practice -- "
        "every single flag in degradation_flags.json was false. The detector was "
        "effectively dead code",
        "Now compares each cell against the random-mean logit at the same coefficient. "
        "Flags degradation when (1) binary rate is within 3pp of 50% AND (2) logit is "
        "within 0.10 of the random mean. This actually catches what degradation looks like"
    )

    pdf.sub_heading("21 conditions (was 7)")
    pdf.old_new(
        "7 conditions: assistant_axis + 5 roles + 1 random",
        "21 conditions: assistant_axis + 5 critical roles + 4 conformist roles + "
        "CAA + 10 randoms"
    )

    pdf.separator()

    # --- 03_analysis.py ---
    pdf.heading("03_analysis.py (major rewrite)")
    pdf.body(
        "This file was almost entirely rewritten. The original was ~670 lines. "
        "The new version is ~870 lines with fundamentally different statistical methods."
    )

    pdf.sub_heading("Primary test changed")
    pdf.old_new(
        "McNemar chi-square on binary choices (600 rows treated as independent). "
        "This tested the wrong thing (binary flips, not logit shifts) and inflated "
        "sample size (n=600 when effective n=300)",
        "Paired Wilcoxon signed-rank on base-level syc_logit (averaged across "
        "original/swapped variants, n=base questions). McNemar kept as secondary. "
        "This matches the declared primary metric and respects non-independence"
    )

    pdf.sub_heading("Spearman dose-response fixed")
    pdf.old_new(
        "Computed on 6 aggregate mean values per condition. With 6 monotonically "
        "decreasing points, mechanically got rho = -1.000 for every condition. "
        "This was the CRITICAL statistical issue -- it looked impressive but "
        "carried zero real information",
        "Computed on row-level data (3600+ points per condition). The old 6-point "
        "version is kept for comparison but labeled as secondary"
    )

    pdf.sub_heading("p-value underflow fixed")
    pdf.old_new(
        "Reported p = 0.0 (floating-point underflow) as a real result",
        "safe_pvalue() function replaces 0.0 with 1e-300. Display as '< 1e-15'"
    )

    pdf.sub_heading("Multiple comparison correction added")
    pdf.old_new(
        "35+ tests with no correction. Contrarian vs axis at p = 0.048 reported "
        "as significant but would not survive any correction",
        "Holm-Bonferroni applied to Wilcoxon and McNemar test families. Reports "
        "both raw and adjusted p-values. Flags which survive correction"
    )

    pdf.sub_heading("Exact McNemar where needed")
    pdf.old_new(
        "mcnemar(exact=False) for all comparisons, even when off-diagonal cells "
        "were 1 or 2 (e.g., skeptic vs baseline: b01=2)",
        "Automatically uses exact=True when min(b01, b10) < 5"
    )

    pdf.sub_heading("Pooled projection analysis added")
    pdf.old_new(
        "Pearson r between projection and syc_logit computed only at baseline "
        "(coeff=0). Small variance, low power, premature 'soft null' conclusion",
        "Also computes pooled Pearson r across ALL conditions and coefficients, "
        "leveraging the full dynamic range created by steering"
    )

    pdf.sub_heading("Random control handling")
    pdf.old_new(
        "One random vector plotted as a single line. Best-coefficient for random "
        "used a different selection criterion (lowest absolute logit, landing at "
        "-5000 in degradation regime)",
        "10 random vectors plotted as mean +/- std band. Consistent selection "
        "criterion (excess over random mean) for ALL conditions"
    )

    pdf.sub_heading("Confounded logistic regression removed")
    pdf.old_new(
        "Included row-level logistic regression of chose_sycophantic on projection "
        "(n=600) with a note saying it was 'expected to be null because confounded "
        "by A-bias.' Result was p = 0.934. Reviewers would ask 'why run a test you "
        "knew was invalid?'",
        "Removed from main output"
    )

    pdf.sub_heading("New analyses added")
    pdf.bullet("CAA decomposition analysis: for each role, reports how much of its effect "
               "comes from the CAA-aligned component vs residual")
    pdf.bullet("Efficiency analysis: sycophancy_reduction / |coefficient| vs cosine(vec, CAA)")
    pdf.bullet("PCA persona-space visualization (Fig 6): 2D projection of all steering "
               "vectors with sycophancy reduction annotated")
    pdf.bullet("Supports --split tune|test|all for tune/test workflow")

    pdf.separator()

    # --- Auxiliary scripts ---
    pdf.add_page()
    pdf.heading("over_correction_check.py")
    pdf.old_new(
        "5 handpicked ground-truth prompts tested under 4 conditions. Output was "
        "free text printed to console. Anecdotal, not systematic",
        "16 structured probes (8 obviously-true claims, 8 obviously-false claims) "
        "tested under 5 conditions. Each response classified by keyword heuristics "
        "into AGREE_CORRECT, DISAGREE_CORRECT, AGREE_WRONG, DISAGREE_WRONG, HEDGE, "
        "REFUSE. Per-condition accuracy table printed and saved to "
        "over_correction_eval.json"
    )

    pdf.separator()

    pdf.heading("pilot_scale.py")
    pdf.old_new(
        "Used eval_data[:50] (first 25 counterbalanced pairs in file order). "
        "Because the file is paired and ordered, this was not a clean sample",
        "Randomly samples 25 base IDs, then takes both variants for each. "
        "Produces a proper random pilot sample"
    )

    pdf.separator()

    pdf.heading("qual_check.py, find_skeptic_agreement.py, pilot_debug.py")
    pdf.body(
        "All updated to import from config.py instead of hardcoding paths and "
        "constants. Functionality unchanged."
    )

    # ======================================================================
    # SECTION 3: EXPERIMENT SCOPE CHANGES
    # ======================================================================
    pdf.add_page()
    pdf.section_title("3. Experiment Scope Changes")

    pdf.heading("Conditions: 7 -> 21")
    pdf.body("The original experiment tested 7 conditions. The new experiment tests 21:")
    pdf.code(
        "ORIGINAL (7):\n"
        "  assistant_axis, devils_advocate, contrarian, skeptic,\n"
        "  judge, scientist, random\n"
        "\n"
        "NEW (21):\n"
        "  assistant_axis                             (broad axis)\n"
        "  devils_advocate, contrarian, skeptic,      (critical roles)\n"
        "  judge, scientist\n"
        "  servant, diplomat, disciple, peacemaker    (conformist roles -- NEW)\n"
        "  caa                                        (targeted baseline -- NEW)\n"
        "  random_0 through random_9                  (10 random controls)"
    )
    pdf.body(
        "The conformist roles test bidirectionality: if persona steering genuinely "
        "controls sycophancy, then pushing toward deferential/compliant roles should "
        "INCREASE sycophancy. If both directions work, the effect is not just noise."
    )
    pdf.body(
        "The CAA vector is the 'gold standard' targeted sycophancy vector, extracted "
        "from sycophancy-specific data. Comparing general persona vectors against CAA "
        "is the core research question."
    )

    pdf.separator()

    pdf.heading("Evaluation: single-pass -> tune/test + multi-seed")
    pdf.old_new(
        "All 300 base questions used for both selecting the best coefficient AND "
        "reporting the final result. One seed, one sample",
        "Tune/test split at base-question level (--split tune|test). Multi-seed "
        "support (--seed flag on 00b, run_multiseed.py wrapper). Pairs always "
        "stay together in the same split"
    )

    pdf.separator()

    pdf.heading("Analysis pipeline: 5 parts (was 3)")
    pdf.body("The original had: (1) steering curves, (2) projection analysis, (3) statistical tests.")
    pdf.body("The new pipeline adds:")
    pdf.bullet("Part 2b: CAA vector extraction (Rimsky et al. method)")
    pdf.bullet("Part 4: Decomposition -- split each role into CAA-aligned + residual, test separately")
    pdf.bullet("Part 5 (expanded): PCA persona-space figure, efficiency analysis, response-token projections")

    pdf.separator()

    pdf.heading("Figures: 5 -> 6")
    pdf.code(
        "ORIGINAL (5 figures):\n"
        "  fig1: steering curves (7 lines)\n"
        "  fig2: projection distributions (baseline)\n"
        "  fig3: projection shift\n"
        "  fig4: best per condition (7 bars)\n"
        "  fig5: cosine similarity heatmap (7x7)\n"
        "\n"
        "NEW (6 figures):\n"
        "  fig1: steering curves (11+ lines, random mean +/- std band)\n"
        "  fig2: projection distributions (baseline)\n"
        "  fig3: projection shift\n"
        "  fig4: best per condition (11 bars, bootstrap CI)\n"
        "  fig5: cosine similarity heatmap (12x12 with CAA + conformist)\n"
        "  fig6: PCA persona-space visualization (NEW)"
    )

    # ======================================================================
    # SECTION 4: STATISTICAL FIXES
    # ======================================================================
    pdf.add_page()
    pdf.section_title("4. Statistical Fixes (Summary)")
    pdf.body(
        "These are the issues identified in the Issues.pdf review and the subsequent "
        "analysis report. All have been addressed in the updated codebase."
    )

    issues = [
        ("#1 CRITICAL", "Spearman rho = -1.0 on 6 points",
         "Row-level Spearman on 3600+ points"),
        ("#2 HIGH", "p-values of exactly 0.0",
         "Guarded with safe_pvalue(), displayed as '< 1e-15'"),
        ("#3 HIGH", "Pearson r only at baseline",
         "Added pooled analysis across all conditions"),
        ("#4 HIGH", "No multiple comparison correction",
         "Holm-Bonferroni on all test families"),
        ("#5 MEDIUM", "McNemar chi-sq with b01 = 1",
         "exact=True when min(b01, b10) < 5"),
        ("#6 MEDIUM", "Random uses different criterion",
         "Consistent excess-over-random-mean for all"),
        ("#7 HIGH", "Degradation flags all false",
         "Comparison to random-mean + rate near 50%"),
        ("#8 MEDIUM", "Best coeff uniformly +2000",
         "Tune/test split prevents selection bias"),
        ("#9 MEDIUM", "Primary metric/test mismatch",
         "Wilcoxon on base-level syc_logit is primary"),
        ("#10 MEDIUM", "Row-level independence violated",
         "All primary analyses at base-question level"),
        ("#11 MEDIUM", "Stale coeff range in setup_info",
         "Uses actual COEFFICIENTS from config"),
        ("#12 MEDIUM", "eval_data.json overwrite",
         "Distinct filenames + schema check"),
        ("#13 LOW", "Hardcoded paths everywhere",
         "config.py with env var overrides"),
        ("#14 LOW", "Confounded logistic regression",
         "Removed from main output"),
    ]

    pdf.set_font("Helvetica", "B", 8.5)
    col_widths = [25, 65, 80]
    for w, h in zip(col_widths, ["Severity", "Original Issue", "Fix Applied"]):
        pdf.cell(w, 6, h, border=1, align="C")
    pdf.ln()
    pdf.set_font("Helvetica", "", 8)
    for sev, issue, fix in issues:
        h = 6
        pdf.cell(col_widths[0], h, sev, border=1, align="C")
        pdf.cell(col_widths[1], h, issue[:40], border=1)
        pdf.cell(col_widths[2], h, fix[:50], border=1)
        pdf.ln()

    # ======================================================================
    # SECTION 5: FILE DIFF SUMMARY
    # ======================================================================
    pdf.add_page()
    pdf.section_title("5. File-by-File Diff Summary")

    files = [
        ("config.py", "NEW", "80 -> 99 lines",
         "Centralized config. All constants, roles, CAA datasets, labels."),
        ("00_setup.py", "MODIFIED", "239 -> 234 lines",
         "Writes eval_data_raw.json. Correct coeff range. Config imports."),
        ("00b_rebuild_eval.py", "MODIFIED", "117 -> 123 lines",
         "Accepts --seed flag. Config imports."),
        ("01_prepare_steering_vectors.py", "MODIFIED", "104 -> 131 lines",
         "9 roles (was 5). 10 randoms (was 1). CAA integration. Decomposition."),
        ("02_evaluate_steering.py", "MODIFIED", "338 -> 430 lines",
         "Tune/test split. Schema check. Response projections. 21 conditions."),
        ("02b_extract_caa.py", "NEW", "0 -> 142 lines",
         "CAA sycophancy vector extraction (Rimsky et al. method)."),
        ("03_analysis.py", "REWRITTEN", "671 -> 870 lines",
         "Wilcoxon primary. Row-level Spearman. MCC. Decomp. PCA. Efficiency."),
        ("over_correction_check.py", "REWRITTEN", "108 -> 230 lines",
         "16 structured probes. Keyword classifier. Accuracy table. JSON output."),
        ("pilot_scale.py", "MODIFIED", "64 -> 79 lines",
         "Random base_id sampling. Config imports."),
        ("pilot_debug.py", "MODIFIED", "117 -> 112 lines",
         "Config imports. No functional changes."),
        ("qual_check.py", "MODIFIED", "85 -> 78 lines",
         "Config imports. References random_0 instead of random."),
        ("find_skeptic_agreement.py", "MODIFIED", "78 -> 80 lines",
         "Config imports."),
        ("run_multiseed.py", "NEW", "0 -> 146 lines",
         "Multi-seed orchestrator. Aggregates mean +/- std across seeds."),
        ("README.md", "REWRITTEN", "~440 -> ~230 lines",
         "Complete Lambda GPU workflow. Full pipeline description."),
    ]

    pdf.set_font("Helvetica", "B", 8.5)
    col_widths2 = [48, 18, 25, 79]
    for w, h in zip(col_widths2, ["File", "Status", "Lines", "Changes"]):
        pdf.cell(w, 6, h, border=1, align="C")
    pdf.ln()
    pdf.set_font("Helvetica", "", 7.5)
    for fname, status, lines, desc in files:
        h = 6
        pdf.set_font("Courier", "", 7.5)
        pdf.cell(col_widths2[0], h, fname, border=1)
        pdf.set_font("Helvetica", "B", 7.5)
        color_map = {"NEW": (0, 130, 0), "MODIFIED": (200, 130, 0), "REWRITTEN": (180, 30, 30)}
        r, g, b = color_map.get(status, (0, 0, 0))
        pdf.set_text_color(r, g, b)
        pdf.cell(col_widths2[1], h, status, border=1, align="C")
        pdf.set_text_color(30, 30, 30)
        pdf.set_font("Helvetica", "", 7.5)
        pdf.cell(col_widths2[2], h, lines, border=1, align="C")
        pdf.cell(col_widths2[3], h, desc[:52], border=1)
        pdf.ln()

    pdf.ln(6)
    pdf.body(
        "Total lines of code: original ~2050, updated ~2834 (~38% increase). "
        "3 new files, 9 modified files, 2 rewritten files."
    )

    # ======================================================================
    # SECTION 6: WHAT STAYED THE SAME
    # ======================================================================
    pdf.section_title("6. What Stayed the Same")
    pdf.body("The following aspects of the experiment are unchanged:")
    pdf.bullet("Model: Gemma 2 27B Instruct (google/gemma-2-27b-it), bf16, device_map='auto'")
    pdf.bullet("Target layer: model.model.layers[22]")
    pdf.bullet("Steering method: ActivationSteering from safety-research/assistant-axis (addition, all positions)")
    pdf.bullet("Eval dataset: philpapers2020 (300 base questions, counterbalanced)")
    pdf.bullet("Token IDs: A = 235280, B = 235305")
    pdf.bullet("Coefficient sweep: [-5000, -3000, -2000, -1000, -500, -200, 0, 200, 500, 1000, 2000, 3000, 5000]")
    pdf.bullet("Counterbalancing method: A/B swap with flipped sycophancy labels")
    pdf.bullet("Two metrics: binary sycophancy rate + mean sycophancy logit")
    pdf.bullet("CaptureHook registered before ActivationSteering (pre-steer projection)")
    pdf.bullet("Baseline (coeff=0) run once and shared across conditions")
    pdf.bullet("Checkpointing per condition for resume support")

    return pdf


if __name__ == "__main__":
    pdf = build()
    out = "/Users/vikramkakaria/Desktop/Sandbagging/Updates to Ishaan Repo.pdf"
    pdf.output(out)
    print(f"Report written to {out}")
