# Evals Lab — Structured Evaluation for Nondeterministic Systems


> **Thesis.** Generative models are variable. Classical unit tests assume
> determinism. **Evals** are structured tests that still let you say:
> “for this task distribution, under this prompt/model, against these
> graders, performance is X — and it must not regress.”

```
Describe task as Eval  →  Run (prompt × data × model)  →  Analyze → iterate
        (BDD-like)              (samples + grades)         (report)
```

Companion lab: [`../guardrail/`](../guardrail/) enforces **continue / pause / stop**
at runtime. This lab **measures** whether behavior matches intent before and
after you change prompts, models, or rails.

---

## 1. Why evals exist

| Without evals | With evals |
|---------------|------------|
| “It seems to work” (vibe-based) | Task-scoped pass rates + failure cases |
| Surprise regressions on model upgrades | Comparable runs on a frozen dataset |
| Only academic metrics (BLEU/perplexity) | Graders tied to *your* product criteria |
| Safety claims without evidence | Measurable refusal / categorization / tool choice |

**Tips (best practices distilled):**

1. Adopt **eval-driven development** — write scoped tests early.  
2. Design **task-specific** evals on realistic traffic distributions.  
3. **Log everything** — mine production for hard cases.  
4. **Automate** scoring when you can; calibrate with humans.  
5. Evaluation is a **journey**, not a destination.  
6. Maintain **human↔auto agreement** before scaling LLM-as-judge.

**Anti-patterns:** overly generic metrics only; biased datasets; vibe evals;
ignoring human disagreement.

---

## 2. The three-step loop (matches the API guide)

### Step A — Create an eval for a task

An eval needs:

- **`data_source_config`** — schema for each test `item`
- **`testing_criteria`** — graders that decide pass/fail

Example task (from the docs): categorize IT tickets → `Hardware` | `Software` | `Other`.

### Step B — Test a prompt with your eval

Provide:

- JSONL dataset (`{"item": {...}}` per line)
- Prompt **template** with `{{ item.field }}`
- A **model** (stub offline, or live API)

### Step C — Analyze the results

Inspect `result_counts`, per-criteria breakdowns, and per-sample failures.
Iterate prompt / model / data. Optionally compare runs (regression).

---

## 3. Package layout

```
evals/
  core.py          EvalSpec, EvalRun, SampleResult
  graders.py       string_check, regex, label_set, rubric_score
  dataset.py       JSONL load/save
  prompt.py        {{ item.* }} templating
  models.py        ticket stub + optional OpenAI adapter
  registry.py      create/store eval definitions
  runner.py        create_run / retrieve / write reports
  analyze.py       summarize + markdown report
  demo.py          end-to-end IT ticket lab
  data/tickets.jsonl
  reports/         generated run reports
  README.md        this document
  REVIEW.md        design review & residual risks
```

---

## 4. Quick start

```bash
cd evals
python3 demo.py
```

You should see:

1. Eval created (`IT Ticket Categorization`)
2. Run completed with pass/fail per ticket
3. Strong stub vs weak stub **regression signal**
4. Markdown + JSON under `reports/`

### Minimal API sketch (local)

```python
from core import DataSourceConfig
from graders import StringCheckGrader
from models import ticket_classifier_stub
from registry import EvalRegistry
from runner import Runner

registry = EvalRegistry()
runner = Runner()

eval_obj = registry.create(
    name="IT Ticket Categorization",
    data_source_config={
        "type": "custom",
        "item_schema": {
            "type": "object",
            "properties": {
                "ticket_text": {"type": "string"},
                "correct_label": {"type": "string"},
            },
            "required": ["ticket_text", "correct_label"],
        },
    },
    testing_criteria=[
        StringCheckGrader(
            name="Match output to human label",
            input="{{ sample.output_text }}",
            operation="eq",
            reference="{{ item.correct_label }}",
        )
    ],
)

run = runner.create_run(
    eval_obj,
    name="Categorization text run",
    model_name="ticket-stub-v1",
    model_fn=ticket_classifier_stub,
    prompt_template=[
        {"role": "developer", "content": "Categorize as Hardware, Software, or Other."},
        {"role": "user", "content": "{{ item.ticket_text }}"},
    ],
    data_path="data/tickets.jsonl",
)
print(run.result_counts)
```

Optional live model (needs key):

```python
from models import openai_responses_adapter
model_fn = openai_responses_adapter("gpt-4.1-mini")
```

---

## 5. Graders (testing criteria)

| Type | Use when |
|------|----------|
| `StringCheckGrader` | Exact / contains match to human label |
| `LabelSetGrader` | Output must be one of allowed labels |
| `RegexGrader` | Format constraints |
| `RubricScoreGrader` | Soft quality score (swap in LLM judge) |

**LLM-as-judge guidance (from best-practice literature):**

- Prefer pairwise / pass-fail / reference-guided over free-form critique alone  
- Control length bias; ask for reasoning before score  
- Validate agreement with human labels before trusting at scale  
- Start with a strong judge model, then distill if cost matters  

---

## 6. Where nondeterminism enters (architectures)

| Architecture | Extra nondeterminism to eval |
|--------------|------------------------------|
| Single-turn | Instruction following, functional correctness |
| Workflow | Each step’s prompt + correctness of extracted fields |
| Single-agent | **Tool selection** + **argument precision** |
| Multi-agent | **Handoff accuracy** between specialists |

Only add multi-agent complexity when evals show a single agent failing
instruction-following or tool choice under load.

Map these to this repo’s **guardrail** lab: tool-selection evals tell you
*what* to measure; tool guardrails + HITL decide *what may execute*.

---

## 7. Mapping to OpenAI Evals API shapes

| OpenAI concept | This harness |
|----------------|--------------|
| `client.evals.create` | `EvalRegistry.create` |
| `data_source_config` | `DataSourceConfig` |
| `testing_criteria` / graders | `StringCheckGrader`, … |
| JSONL `{"item": ...}` | `data/tickets.jsonl` + `load_jsonl` |
| `evals.runs.create` | `Runner.create_run` |
| `evals.runs.retrieve` | `Runner.retrieve` |
| `result_counts` / report URL | `EvalRun.result_counts` + `reports/*.md` |
| `{{ item.ticket_text }}` | `prompt.render_messages` |

---

## 8. Continuous evaluation (CE)

Recommended loop for production teams:

1. Freeze a **gold** JSONL set (typical + edge + adversarial).  
2. Run evals on every prompt/model/guardrail change in CI.  
3. Mine logs weekly → promote failures into the gold set.  
4. Track pass rate **and** slice by label / locale / length.  
5. Pair with human review on a stratified sample.

---

## 9. What this lab is not

- Not a hosted Evals cloud (and not a migration target for the deprecated platform).  
- Not a replacement for human judgment on high-stakes domains.  
- Not sufficient alone for dual-use safety (combine with training controls + runtime rails).  
- Stub classifiers are for **harness teaching**; publish numbers only after real models + calibrated graders.

See **[REVIEW.md](./REVIEW.md)** for findings and residual risks.

---

## 10. Takeaway

> Specify behavior as data + graders, freeze the distribution, compare runs.
> Improve prompts and models against that meter — then enforce the same
> contracts at runtime with guardrails.
