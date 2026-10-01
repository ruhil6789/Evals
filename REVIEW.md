# Design Review — Evals Harness

**Reviewers (role framing):** measurement / systems (MIT) × deployment safety
(Anthropic-style senior scientist).  
**Artifact:** `evals/` local evaluation lab.  
**Date:** 2026-10-01

---

## Verdict

**Pass for research / teaching use.** Implements the OpenAI “Working with
evals” three-step loop offline with compatible shapes. Suitable as a CE
skeleton. **Not** a substitute for calibrated human evals on high-stakes tasks.

---

## Alignment with source documentation

| Doc requirement | Status |
|-----------------|--------|
| Create eval (schema + criteria) | Done — `EvalRegistry` + `DataSourceConfig` + graders |
| JSONL items with ground truth | Done — `data/tickets.jsonl` |
| Prompt template + model run | Done — `prompt.py` + `Runner.create_run` |
| Analyze result_counts / per-criteria | Done — `EvalRun` + `analyze.py` reports |
| Best-practice narrative | Done — README |
| Live OpenAI Responses/Evals API | Optional adapter only (`models.openai_responses_adapter`) |
| Webhooks for async runs | Out of scope (local sync runner) |
| Dashboard UI | Out of scope (markdown reports) |

Note: OpenAI’s hosted Evals platform is deprecated (read-only Oct 31 2026;
shutdown Nov 30 2026). This lab is intentionally **portable** so work survives
that shutdown.

---

## Findings

### F1 — INFO: stub model ≠ production model

`ticket_classifier_stub` is deterministic regex. Demo pass rates do not
generalize. Always re-run with the model you ship.

### F2 — MEDIUM (accepted): no statistical significance helpers

Small N (6 tickets) is fine for plumbing tests, not for claiming SOTA.
Add bootstrap CIs before publishing comparisons.

### F3 — MEDIUM (accepted): LLM-as-judge is heuristic

`RubricScoreGrader` default is length/heuristic. Wire a real judge and
measure Cohen’s κ / agreement vs humans (README §5).

### F4 — LOW (accepted): registry persistence is metadata-only

Saved JSON snapshots graders as dicts but in-memory objects are the source of
truth for re-runs in-process. Reload of grader callables from disk is not
implemented — acceptable for a lab; production should version grader code.

### F5 — LOW: no multi-agent / tool-selection suite yet

README describes architecture-specific eval questions; code demo is
single-turn classification. Next experiment: evaluate `guardrail` tool
choice (expected tool + args) as an eval dataset.

### F6 — INFO: leakage / contamination

If gold labels leak into prompts, string_check scores inflate. Keep
`correct_label` out of rendered user messages (current templates do).

---

## Evaluation checklist

- [x] Create eval with schema + string_check  
- [x] Run on JSONL  
- [x] Report pass/fail + markdown  
- [x] Regression demo (strong > weak)  
- [ ] Human agreement study for any LLM judge  
- [ ] CI job running `python3 demo.py` on PR  
- [ ] Slice metrics by label  
- [ ] Adversarial / multilingual tickets in dataset  

---

## Residual risks

1. **Metric gaming** — optimizing prompts to the grader, not the user.  
2. **Distribution shift** — gold set drifts from production.  
3. **False safety** — high categorization accuracy ≠ safe agent behavior.  
4. **Judge bias** — position/verbosity bias in LLM graders.  

---

## Recommended next experiments

1. Add `data/tickets_adversarial.jsonl` (typos, multilingual, multi-intent).  
2. Eval **tool selection** against the `guardrail` demo agent.  
3. Pairwise prompt A/B with a frozen judge rubric.  
4. Bootstrap confidence intervals on pass rate deltas.  
5. Store anonymized production failures → weekly gold-set PR.

---

## Sign-off

`python3 demo.py` completes create → run → analyze → regression.  
README + REVIEW checked in. **Research demo complete.**
