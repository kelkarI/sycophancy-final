# LIMITATIONS

Honest limitations that a reviewer will raise. We list them here so they
are not lost in the results prose.

1. **Single model, single scale.** All results are on Gemma 2 27B Instruct.
   We have not repeated the experiment on another model family (Llama,
   Qwen, Mistral) or another scale (9B, 2B, larger Gemma). Persona-direction
   behaviour may depend on the training distribution and post-training of
   the specific model. The assistant-axis vectors and role vectors
   themselves come from `lu-christina/assistant-axis-vectors` on
   HuggingFace and are specific to Gemma 2 27B; no retraining was done.

2. **Single evaluation dataset family.** The sycophancy measure is the
   philpapers2020 A/B preference benchmark from Anthropic's `evals`
   repository. Results may not transfer to free-form sycophancy, agentic
   task settings, or adversarial sycophancy prompts. The CAA training uses
   the NLP-survey and political-typology-quiz sycophancy datasets from the
   same family, which share a construction style with philpapers2020. We
   verified zero train/eval question-text overlap
   (`paper/tables/caa_leakage_receipt.json`) but cannot rule out
   distributional similarity beyond exact matches.

3. **Overcorrection classifier is heuristic.** The AGREE / DISAGREE /
   HEDGE / REFUSE classifier in `over_correction_check.py` uses simple
   keyword regexes, not a learned classifier. It is calibrated for English
   and for the response style that Gemma 2 produces; corner cases
   (sarcasm, chained clauses, implicit agreement via repetition) are not
   covered. We mitigate by reporting per-category counts rather than
   summary accuracies, so a reader can spot classifier-driven effects.

4. **Role-vector source.** The critical and conformist role directions are
   precomputed means of residual activations collected while the model is
   prompted with role-playing. We did not re-collect them or vary the role
   definitions. The `scientist` role in particular produces role vectors
   that are nearly orthogonal to the assistant axis in the cosine matrix;
   a reviewer might reasonably ask whether a differently-collected
   `scientist` vector would behave differently.

5. **Target layer fixed at 22.** Prior work and the original experiment
   identified layer 22 as the operating point. We did not sweep layers in
   this study. A per-layer sweep would add roughly 20× the GPU budget at
   the current coefficient-sweep granularity.

6. **Coefficient sweep is sparse near the operating point.** Between
   $c = 200$ and $c = 5000$ we have five log-spaced values. The best
   coefficient for conformist roles may lie between sampled values.

7. **CAA-extraction noise is not quantified.** The CAA vector is extracted
   once and reused across seeds, so the error bars for the `caa` condition
   reflect eval-sampling noise and not extraction noise. Bootstrapping
   over the CAA training pairs would produce an extraction-noise band; we
   leave this for revision.

8. **Decomposition is only evaluated at the role's tune-locked best
   coefficient.** We chose the cheap option from the Phase-1 decision
   (component + residual at a single operating point, ~40 GPU minutes).
   A full dose-response sweep of the decomposition vectors would let us
   claim the mechanism's robustness across steering magnitudes; we leave
   that for revision.

9. **Multi-seed scope.** 5 tune seeds and 3 test seeds. This is sufficient
   for the error-bar story we report, but the test-side std is based on
   $n = 3$ — a reviewer may reasonably request more.

10. **Negative results not actively searched.** We report per-role whether
    behaviour is dominated by the CAA-aligned component or the residual
    (Figure 3). Where we found a role is dominated by CAA, we say so.
    We have not run sanity-check ablations such as "steer with a random
    *orthogonal* direction to CAA of matched magnitude" — the random-10
    band we do show is much looser than such a matched-null would be.

11. **English only.** All prompts, probes, and the keyword classifier are
    English. Cross-lingual behaviour is untested.

12. **Counterbalancing caveat.** Counterbalancing cancels positional
    A-bias in the mean of base-level `syc_logit`, but not in every
    individual variant. The "positional A-bias" count reported in Figure 2
    (≈233 of 300 base questions at baseline) highlights that many base
    questions are driven primarily by position rather than content. Our
    continuous-metric analyses (syc_logit, not binary) are robust to this;
    the binary-rate numbers should be read in that light.
