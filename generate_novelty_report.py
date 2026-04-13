#!/usr/bin/env python3
"""Generate a PDF report analyzing feasibility and impact of novelty directions."""

from fpdf import FPDF


class Report(FPDF):
    def header(self):
        if self.page_no() > 1:
            self.set_font("Helvetica", "I", 9)
            self.set_text_color(120, 120, 120)
            self.cell(0, 8, "Novelty Directions -- Feasibility Report", align="R",
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
        self.ln(3)
        self.multi_cell(0, 7, text, new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

    def sub_heading(self, text):
        self.set_font("Helvetica", "B", 11)
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

    def badge(self, label, color_rgb):
        r, g, b = color_rgb
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(r, g, b)
        self.cell(0, 5, label, new_x="LMARGIN", new_y="NEXT")
        self.set_text_color(30, 30, 30)
        self.ln(1)

    def separator(self):
        self.ln(3)
        y = self.get_y()
        mid = self.w / 2
        self.set_draw_color(180, 180, 180)
        self.line(mid - 40, y, mid + 40, y)
        self.ln(5)


def build():
    pdf = Report()
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=20)

    # ---- TITLE ----
    pdf.add_page()
    pdf.ln(40)
    pdf.set_font("Helvetica", "B", 24)
    pdf.multi_cell(0, 12, "Novelty Directions", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)
    pdf.set_font("Helvetica", "", 14)
    pdf.set_text_color(80, 80, 80)
    pdf.multi_cell(0, 8,
        "Feasibility and Implementation Analysis\nfor the Sycophancy Steering Experiment",
        align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(20)
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(60, 60, 60)
    pdf.multi_cell(0, 6,
        "This report evaluates seven proposed novelty directions for the\n"
        "sycophancy steering paper. For each direction, it assesses:\n\n"
        "  - What already exists in the codebase to support it\n"
        "  - What new work is needed\n"
        "  - Estimated implementation effort\n"
        "  - Expected impact on paper strength\n"
        "  - Concrete implementation steps\n\n"
        "The final section recommends a combined strategy that maximizes\n"
        "novelty while staying within a feasible scope.",
        align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(15)
    pdf.set_font("Helvetica", "I", 10)
    pdf.set_text_color(120, 120, 120)
    pdf.cell(0, 6, "Generated: 2026-04-13", align="C", new_x="LMARGIN", new_y="NEXT")

    # ==================================================================
    # DIRECTION 1
    # ==================================================================
    pdf.add_page()
    pdf.section_title("1. Mechanism-of-Reduction Taxonomy")
    pdf.badge("Feasibility: HIGH  |  Impact: HIGH  |  Effort: ~2 days", (0, 130, 0))

    pdf.sub_heading("Core idea")
    pdf.body(
        "Classify HOW each vector reduces sycophancy, not just by how much. Build a "
        "taxonomy: direct disagreement, evidence-based correction, neutrality/hedging, "
        "refusal, incoherence, persona drift. This turns a single-number comparison into "
        "a qualitative contribution."
    )

    pdf.sub_heading("What already exists in the codebase")
    pdf.bullet(
        "over_correction_check.py already has a keyword-based classifier that sorts "
        "responses into AGREE_CORRECT, DISAGREE_CORRECT, AGREE_WRONG, DISAGREE_WRONG, "
        "HEDGE, REFUSE. This is the skeleton."
    )
    pdf.bullet(
        "qual_check.py generates free-form responses for 5 prompts under 5 conditions. "
        "The infrastructure for steered generation is in place."
    )
    pdf.bullet(
        "The 10 random controls let you show that random vectors produce \"incoherence\" "
        "while targeted vectors produce \"direct disagreement\" -- a clean contrast."
    )

    pdf.sub_heading("What needs to be built")
    pdf.bullet(
        "Expand the classifier from 6 to ~8 categories. Add: \"evidence-based correction\" "
        "(detectable via phrases like 'however, evidence suggests', 'studies show', "
        "'actually, the data indicates') and \"persona drift\" (detectable via incoherent "
        "role-breaking, repeated tokens, or topic derailing)."
    )
    pdf.bullet(
        "Run steered generation on the full eval set (or a large subset, e.g., 100 base "
        "questions) under each condition at the +2000 operating point. Use the open-form "
        "prompt format (strip the A/B scaffolding, ask 'Do you agree? Briefly explain.')."
    )
    pdf.bullet(
        "Produce a heatmap figure: conditions (rows) x behavioral categories (columns), "
        "showing what fraction of responses fall into each mode. This is the key figure."
    )
    pdf.bullet(
        "Optional but high-value: validate the keyword classifier against ~50 hand-labeled "
        "examples, or use an LLM (e.g., Claude) as a labeler for higher accuracy."
    )

    pdf.sub_heading("Implementation estimate")
    pdf.body(
        "Script changes: ~200 lines. GPU time: ~30 min for 100 questions x 8 conditions "
        "x ~120 tokens each. Analysis/figure: ~100 lines. Total: 1-2 days."
    )

    pdf.sub_heading("Why it matters for the paper")
    pdf.body(
        "This is the difference between 'skeptic scored best' and 'skeptic produces "
        "healthy direct disagreement while contrarian produces unstable pushback and "
        "the assistant axis produces passive hedging.' The latter is a real contribution. "
        "It also directly supports Direction 5 (good vs bad disagreement)."
    )

    pdf.separator()

    # ==================================================================
    # DIRECTION 2
    # ==================================================================
    pdf.heading("2. Sycophancy as a Persona-Space Phenomenon")
    pdf.badge("Feasibility: HIGH  |  Impact: HIGH  |  Effort: ~1 day", (0, 130, 0))

    pdf.sub_heading("Core idea")
    pdf.body(
        "Frame sycophancy not as a pure alignment bug but as partly governed by where the "
        "model sits in persona space. Shifting the model's social posture (from assistant "
        "toward skeptic, judge, etc.) changes its deference behavior. This is a conceptual "
        "reframing, not a new experiment."
    )

    pdf.sub_heading("What already exists")
    pdf.bullet(
        "The cosine similarity matrix (fig5) already shows that role vectors form a "
        "structured space: devils_advocate and contrarian are highly correlated (0.88), "
        "skeptic is somewhat independent (0.41 to contrarian, 0.64 to devils_advocate), "
        "scientist is nearly orthogonal to the axis (-0.07)."
    )
    pdf.bullet(
        "The dose-response curves (fig1) already show that different directions in persona "
        "space produce different sycophancy trajectories."
    )
    pdf.bullet(
        "The pooled projection analysis (new in 03_analysis.py) links internal position "
        "along the axis to sycophancy behavior."
    )

    pdf.sub_heading("What needs to be built")
    pdf.bullet(
        "A 2D or 3D PCA/UMAP visualization of the 7 steering vectors projected into a "
        "low-dimensional persona space, with sycophancy reduction annotated on each point. "
        "This is ~50 lines of code and produces a compelling figure."
    )
    pdf.bullet(
        "A paragraph-level analysis in the paper framing section, arguing that the assistant "
        "axis represents 'generic assistant-ness' while the role vectors carve out specific "
        "social stances within that space."
    )
    pdf.bullet(
        "Optional: project the model's baseline activations (unsteered) into this space and "
        "show that Gemma's default position is already 'assistant-like' -- the steering "
        "moves it toward specific role positions."
    )

    pdf.sub_heading("Implementation estimate")
    pdf.body(
        "Script changes: ~80 lines for the PCA figure. No new GPU time needed (uses "
        "existing vector data). Total: half a day."
    )

    pdf.sub_heading("Why it matters")
    pdf.body(
        "This is what gives the paper a conceptual identity beyond 'we tried 7 vectors.' "
        "The claim becomes: sycophancy is partly a representational phenomenon organized "
        "along latent persona dimensions. That is a perspective contribution, not just an "
        "empirical one, and it is what makes the paper citable."
    )

    pdf.separator()

    # ==================================================================
    # DIRECTION 3
    # ==================================================================
    pdf.heading("3. Generic Axis vs Targeted Roles")
    pdf.badge("Feasibility: ALREADY DONE  |  Impact: HIGH  |  Effort: ~0 (framing only)", (0, 100, 200))

    pdf.sub_heading("Core idea")
    pdf.body(
        "The broad assistant axis is too blunt; targeted persona vectors are better tools "
        "for reducing sycophancy."
    )

    pdf.sub_heading("What already exists")
    pdf.body(
        "This IS the main finding of the experiment. The data clearly shows: skeptic, "
        "judge, and devil's advocate all outperform the assistant axis, while contrarian "
        "(the vector most aligned with the axis, cos=-0.80) performs worst among role "
        "vectors. The comparison is already in the results table, fig4, and the statistical "
        "tests."
    )

    pdf.sub_heading("What needs to be built")
    pdf.bullet(
        "Nothing new in the code. This is a framing/writing task."
    )
    pdf.bullet(
        "The paper title and abstract should lead with this contrast. Something like: "
        "'Targeted Persona Vectors Outperform the Generic Assistant Axis for Reducing "
        "Sycophancy in Gemma 2 27B.'"
    )
    pdf.bullet(
        "The discussion should emphasize that the assistant axis captures broad "
        "'assistant-ness' but sycophancy is better addressed by specific social stances "
        "(skeptic, judge) than by generic persona displacement."
    )

    pdf.sub_heading("Why it matters")
    pdf.body(
        "This is the cleanest thesis and the most defensible contribution. It works as "
        "a standalone finding even without the other directions. Every other direction "
        "enriches this core message."
    )

    pdf.separator()

    # ==================================================================
    # DIRECTION 4
    # ==================================================================
    pdf.add_page()
    pdf.heading("4. Format Robustness")
    pdf.badge("Feasibility: MEDIUM  |  Impact: HIGH  |  Effort: ~3-4 days", (200, 130, 0))

    pdf.sub_heading("Core idea")
    pdf.body(
        "Test whether the anti-sycophancy effect holds across different prompt formats: "
        "forced-choice (A/B), free-response, bounded short-answer, and constrained-objective."
    )

    pdf.sub_heading("What already exists")
    pdf.bullet(
        "The forced-choice eval (philpapers2020) is the current benchmark."
    )
    pdf.bullet(
        "qual_check.py already generates free-response text under steering and shows "
        "qualitative differences. But it is not scored."
    )
    pdf.bullet(
        "over_correction_check.py now has a structured classifier that could score "
        "free-response outputs."
    )

    pdf.sub_heading("What needs to be built")
    pdf.bullet(
        "Free-response sycophancy eval: take the philpapers prompts, strip the A/B "
        "scaffolding, ask 'Do you agree? Explain briefly.' Score the response with the "
        "keyword classifier (or an LLM judge). ~100 lines of code."
    )
    pdf.bullet(
        "Bounded short-answer: ask 'Do you agree? Answer yes or no, then explain in "
        "1-2 sentences.' Parse the yes/no as a binary metric. ~50 lines."
    )
    pdf.bullet(
        "Constrained-objective: use a factual QA format where the model is asked to "
        "evaluate a claim and justify. This requires a small new dataset (~20-30 "
        "questions) but can be derived from existing ground-truth probes."
    )
    pdf.bullet(
        "Cross-format comparison figure: sycophancy reduction per condition, broken "
        "out by format. This is the key deliverable."
    )

    pdf.sub_heading("Implementation estimate")
    pdf.body(
        "Script changes: ~400 lines across 2-3 new scripts. GPU time: ~2 hours for "
        "free-response generation across all conditions. Dataset creation: ~2 hours. "
        "Total: 3-4 days."
    )

    pdf.sub_heading("Why it matters")
    pdf.body(
        "Most steering papers live inside one format. Showing cross-format robustness "
        "would make the result much more credible and harder to dismiss as a benchmark "
        "artifact. If some vectors are format-robust and others are not, that is itself "
        "a finding. However, this is the most effort-intensive direction."
    )

    pdf.separator()

    # ==================================================================
    # DIRECTION 5
    # ==================================================================
    pdf.heading("5. Good Disagreement vs Bad Disagreement")
    pdf.badge("Feasibility: HIGH  |  Impact: VERY HIGH  |  Effort: ~2 days", (0, 130, 0))

    pdf.sub_heading("Core idea")
    pdf.body(
        "Reducing agreement is not enough. We need to separate healthy disagreement "
        "(corrects when needed, gives reasons, stays coherent) from pathological "
        "disagreement (contrarian for no reason, hedges endlessly, refuses, becomes "
        "incoherent). Build a quality-of-disagreement rubric."
    )

    pdf.sub_heading("What already exists")
    pdf.bullet(
        "The structured over-correction eval (over_correction_check.py) already classifies "
        "responses on true/false claim probes and computes per-condition accuracy."
    )
    pdf.bullet(
        "The sycophancy logit distribution analysis (Part 1 of over_correction_check.py) "
        "shows whether conditions produce moderation vs inversion."
    )

    pdf.sub_heading("What needs to be built")
    pdf.bullet(
        "A quality-of-disagreement rubric with 5-6 categories: truthful pushback, "
        "evidential challenge, neutral hedging, procedural refusal, unstable contrarianism, "
        "incoherence. This overlaps heavily with Direction 1's taxonomy."
    )
    pdf.bullet(
        "Score ~50-100 steered responses per condition against this rubric. Can use the "
        "keyword classifier as a first pass, then validate a subset manually."
    )
    pdf.bullet(
        "A figure showing: for each condition, what fraction of 'anti-sycophantic' "
        "responses (where the model DID disagree) fall into each quality bucket."
    )
    pdf.bullet(
        "The key claim: skeptic produces mostly 'truthful pushback', contrarian produces "
        "mostly 'unstable contrarianism', axis produces 'neutral hedging'. That would be "
        "a compelling figure."
    )

    pdf.sub_heading("Implementation estimate")
    pdf.body(
        "This shares ~80% of the implementation with Direction 1. If you build both "
        "together, the incremental cost is ~half a day. Total from scratch: 2 days."
    )

    pdf.sub_heading("Why it matters")
    pdf.body(
        "This is the most publishable single contribution you can make. It reframes the "
        "research question from 'how to reduce sycophancy' to 'what kind of "
        "anti-sycophancy do we actually want?' That is a normative contribution that no "
        "reviewer will dismiss as trivial. Combined with Direction 1 (the taxonomy), "
        "this gives the paper real depth."
    )

    pdf.separator()

    # ==================================================================
    # DIRECTION 6
    # ==================================================================
    pdf.add_page()
    pdf.heading("6. Cross-Model Consistency")
    pdf.badge("Feasibility: MEDIUM  |  Impact: VERY HIGH  |  Effort: ~5-7 days", (200, 130, 0))

    pdf.sub_heading("Core idea")
    pdf.body(
        "Test whether the same persona-based anti-sycophancy directions work across "
        "model families (Gemma, Qwen, Llama). Are the effects universal or model-specific?"
    )

    pdf.sub_heading("What already exists")
    pdf.bullet(
        "config.py now centralizes all model-specific constants, making it much easier "
        "to swap models. Change MODEL_NAME, TARGET_LAYER, and TOKEN_IDs."
    )
    pdf.bullet(
        "The assistant-axis repo (safety-research/assistant-axis) has pre-computed "
        "vectors for multiple models. You may be able to download Qwen and Llama "
        "vectors directly."
    )
    pdf.bullet(
        "The full pipeline (01 through 03) is model-agnostic in structure -- only the "
        "config constants are model-specific."
    )

    pdf.sub_heading("What needs to be built")
    pdf.bullet(
        "Per-model config profiles (or a model_configs/ directory with one JSON per model). "
        "Need to determine target_layer and token IDs for each model."
    )
    pdf.bullet(
        "Run the full pipeline for 2 additional models. With 10 random vectors and "
        "16 conditions, each model is ~2-3 hours on H100."
    )
    pdf.bullet(
        "Cross-model comparison figures and analysis. The key figure: a multi-panel "
        "version of fig4 showing best-per-condition across 3 models."
    )
    pdf.bullet(
        "Need to verify that the philpapers2020 eval works with each model's tokenizer "
        "and chat template. May need to adjust token IDs."
    )

    pdf.sub_heading("Implementation estimate")
    pdf.body(
        "Code changes: ~200 lines for multi-model config. GPU time: ~6 hours for 2 "
        "additional models. Analysis: ~1 day. Total: 5-7 days including debugging."
    )

    pdf.sub_heading("Why it matters")
    pdf.body(
        "Cross-model replication instantly elevates the paper. Single-model steering "
        "papers are common; showing that persona-space steering generalizes across "
        "architectures is rare and valuable. However, this is the second-most expensive "
        "direction. Recommend doing this only after Directions 1, 2, 3, and 5 are "
        "locked in."
    )

    pdf.separator()

    # ==================================================================
    # DIRECTION 7
    # ==================================================================
    pdf.heading("7. Representation-Behavior Coupling")
    pdf.badge("Feasibility: HIGH  |  Impact: HIGH  |  Effort: ~1-2 days", (0, 130, 0))

    pdf.sub_heading("Core idea")
    pdf.body(
        "Show that internal movement along persona directions predicts external movement "
        "in sycophancy behavior. Bigger projection shift = bigger behavioral change, and "
        "this relationship is stronger for targeted roles than the generic axis."
    )

    pdf.sub_heading("What already exists")
    pdf.bullet(
        "02_evaluate_steering.py now captures BOTH prompt-token projection AND "
        "response-token projection (mean over 8 generated tokens). This is the internal "
        "measurement."
    )
    pdf.bullet(
        "03_analysis.py already computes a pooled Pearson r between post-steer projection "
        "and syc_logit across all conditions and coefficients."
    )
    pdf.bullet(
        "The post-steer projection is computed analytically: pre_proj + coefficient * "
        "cos(steering_vec, axis_unit). So you already have the shift magnitude."
    )

    pdf.sub_heading("What needs to be built")
    pdf.bullet(
        "Per-condition coupling analysis: for each condition, compute the correlation "
        "between projection shift (across the coefficient sweep) and sycophancy shift. "
        "Targeted roles should show tighter coupling than the generic axis."
    )
    pdf.bullet(
        "Response-token projection analysis: repeat the coupling analysis using the new "
        "response_projection field. The hypothesis is that response-token projections "
        "are better predictors of behavioral change than prompt-token projections."
    )
    pdf.bullet(
        "A scatter plot figure: x = projection shift, y = sycophancy logit change, "
        "color = condition. With regression lines per condition."
    )
    pdf.bullet(
        "Multi-direction projection: project activations onto EACH role direction (not "
        "just the assistant axis) and correlate with sycophancy. Some directions may be "
        "better linear probes for sycophancy than the axis itself."
    )

    pdf.sub_heading("Implementation estimate")
    pdf.body(
        "Script changes: ~200 lines in 03_analysis.py. No new GPU time if using "
        "existing all_results.json (which now includes response_projection). If running "
        "the full pipeline fresh with response_projection capture, add ~30% to eval time. "
        "Total: 1-2 days."
    )

    pdf.sub_heading("Why it matters")
    pdf.body(
        "This is what makes the paper feel mechanistic rather than purely empirical. "
        "The claim becomes: 'we can predict how much a steering intervention will reduce "
        "sycophancy from the size of the internal representation shift.' That bridges "
        "the gap between activation engineering and behavioral outcomes, which is exactly "
        "what the mech-interp community wants to see."
    )

    # ==================================================================
    # RECOMMENDATION
    # ==================================================================
    pdf.add_page()
    pdf.section_title("Recommendation: Combined Strategy")

    pdf.body(
        "The seven directions are not independent. Several share implementation work "
        "and reinforce each other's contribution. Here is the recommended approach, "
        "organized into three tiers by priority."
    )

    pdf.heading("Tier 1: Core Paper Identity (do first, ~3-4 days total)")
    pdf.body("These three directions define what the paper IS about.")

    pdf.sub_heading("Direction 3: Generic Axis vs Targeted Roles (the main thesis)")
    pdf.bullet("Already done. Zero additional code. Pure framing/writing.")
    pdf.bullet("Title: something like 'Targeted Persona Vectors Outperform the Generic "
               "Assistant Axis for Reducing Sycophancy'")

    pdf.sub_heading("Direction 2: Sycophancy as Persona-Space Phenomenon (conceptual framing)")
    pdf.bullet("~Half a day. One new figure (PCA of steering vectors with sycophancy "
               "reduction annotated). Provides the conceptual spine for the paper.")

    pdf.sub_heading("Directions 1 + 5: Mechanism Taxonomy + Good vs Bad Disagreement")
    pdf.bullet("These share ~80% of implementation. Build them together.")
    pdf.bullet("~2-3 days. Steered generation + classifier + heatmap figure + quality rubric.")
    pdf.bullet("This is the strongest single contribution: a taxonomy of anti-sycophancy "
               "modes, with the claim that not all modes are equally desirable.")

    pdf.ln(3)
    pdf.heading("Tier 2: Mechanistic Depth (~1-2 days additional)")

    pdf.sub_heading("Direction 7: Representation-Behavior Coupling")
    pdf.bullet("~1-2 days. Uses existing data (response_projection is already captured). "
               "Adds a scatter plot and per-condition coupling analysis.")
    pdf.bullet("Makes the paper feel mechanistic, not just empirical.")
    pdf.bullet("Especially strong if response-token projections are better predictors "
               "than prompt-token projections -- that would be a finding itself.")

    pdf.ln(3)
    pdf.heading("Tier 3: Generalization (~4-7 days additional)")

    pdf.sub_heading("Direction 4: Format Robustness")
    pdf.bullet("~3-4 days. New eval formats + cross-format figure.")
    pdf.bullet("High impact but high effort. Recommend as a stretch goal.")

    pdf.sub_heading("Direction 6: Cross-Model Consistency")
    pdf.bullet("~5-7 days. 2 additional model runs + cross-model analysis.")
    pdf.bullet("Highest impact if done, but most expensive. Recommend only if time allows.")

    pdf.separator()

    pdf.heading("Proposed Paper Structure")
    pdf.body("If you implement Tiers 1 + 2, the paper writes itself:")

    pdf.bullet("Section 1 (Intro): Sycophancy is partly a persona-space phenomenon, "
               "not just an alignment bug. (Direction 2)")
    pdf.bullet("Section 2 (Method): Activation steering with targeted role vectors vs "
               "the generic assistant axis. 10 random controls, tune/test split. (Direction 3)")
    pdf.bullet("Section 3 (Results - Quantitative): Targeted roles outperform the axis. "
               "Row-level dose-response, Wilcoxon with MCC. (Direction 3)")
    pdf.bullet("Section 4 (Results - Qualitative): Different vectors produce different "
               "behavioral modes. Taxonomy of anti-sycophancy mechanisms. Not all "
               "anti-sycophancy is desirable. (Directions 1 + 5)")
    pdf.bullet("Section 5 (Results - Mechanistic): Projection shift predicts behavioral "
               "shift. Response-token projections are a better probe. (Direction 7)")
    pdf.bullet("Section 6 (Discussion): Design principles for steering-based sycophancy "
               "mitigation. When to use which vector. What 'good disagreement' looks like.")

    pdf.ln(3)
    pdf.heading("Total Estimated Effort")
    pdf.body(
        "Tier 1 (core): 3-4 days of implementation + 1-2 days of writing.\n"
        "Tier 2 (depth): 1-2 additional days.\n"
        "Tier 3 (generalization): 4-7 additional days.\n\n"
        "A solid workshop paper needs Tier 1. A strong conference paper needs "
        "Tiers 1 + 2 + at least one item from Tier 3."
    )

    return pdf


if __name__ == "__main__":
    pdf = build()
    out = "/Users/vikramkakaria/Desktop/Sandbagging/Novelty_Report.pdf"
    pdf.output(out)
    print(f"Report written to {out}")
