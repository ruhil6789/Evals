"""
Evals lab demo — IT ticket categorization (OpenAI docs example, offline).

Three steps:
  1. Create an eval for a task
  2. Test a prompt with your eval (dataset + model)
  3. Analyze the results

Run:
  cd evals && python3 demo.py
"""

from __future__ import annotations

from pathlib import Path

from analyze import summarize
from core import DataSourceConfig
from graders import LabelSetGrader, StringCheckGrader
from models import ticket_classifier_stub, weak_ticket_classifier
from registry import EvalRegistry
from runner import Runner

ROOT = Path(__file__).parent
DATA = ROOT / "data" / "tickets.jsonl"

TICKET_INSTRUCTIONS = (
    "You are an expert in categorizing IT support tickets. Given the support "
    "ticket below, categorize the request into one of 'Hardware', 'Software', "
    "or 'Other'. Respond with only one of those words."
)

PROMPT_TEMPLATE = [
    {"role": "developer", "content": TICKET_INSTRUCTIONS},
    {"role": "user", "content": "{{ item.ticket_text }}"},
]


def section(title: str) -> None:
    print("\n" + "=" * 64)
    print(title)
    print("=" * 64)


def create_ticket_eval(registry: EvalRegistry):
    section("1) Create an eval for a task")
    eval_obj = registry.create(
        name="IT Ticket Categorization",
        data_source_config=DataSourceConfig(
            type="custom",
            item_schema={
                "type": "object",
                "properties": {
                    "ticket_text": {"type": "string"},
                    "correct_label": {"type": "string"},
                },
                "required": ["ticket_text", "correct_label"],
            },
            include_sample_schema=True,
        ),
        testing_criteria=[
            StringCheckGrader(
                name="Match output to human label",
                input="{{ sample.output_text }}",
                operation="eq",
                reference="{{ item.correct_label }}",
            ),
            LabelSetGrader(
                name="Output is a valid category",
                labels=("Hardware", "Software", "Other"),
            ),
        ],
        metadata={"domain": "it_support", "lab": "evals"},
    )
    print(eval_obj.to_dict()["id"], eval_obj.name)
    print("criteria:", [g.name for g in eval_obj.testing_criteria])
    return eval_obj


def run_and_analyze(eval_obj, runner: Runner, model_fn, model_name: str, run_name: str):
    section(f"2–3) Run + analyze — {run_name}")
    run = runner.create_run(
        eval_obj,
        name=run_name,
        model_name=model_name,
        model_fn=model_fn,
        prompt_template=PROMPT_TEMPLATE,
        data_path=DATA,
    )
    # Analog of client.evals.runs.retrieve(...)
    fetched = runner.retrieve(run.id, eval_id=eval_obj.id)
    print(summarize(fetched))
    print("\nJSON-ish result_counts:", fetched.result_counts)
    print("Report:", fetched.metadata.get("report_path"))
    return fetched


def demo_prompt_regression(eval_obj, runner: Runner) -> None:
    """
    Cookbook idea: detecting prompt/model regressions.
    Strong stub should beat weak stub on the same eval + data.
    """
    section("Regression check — strong vs weak model")
    strong = runner.create_run(
        eval_obj,
        name="strong-stub",
        model_name="ticket-stub-v1",
        model_fn=ticket_classifier_stub,
        prompt_template=PROMPT_TEMPLATE,
        data_path=DATA,
    )
    weak = runner.create_run(
        eval_obj,
        name="weak-stub",
        model_name="ticket-stub-always-other",
        model_fn=weak_ticket_classifier,
        prompt_template=PROMPT_TEMPLATE,
        data_path=DATA,
    )
    s, w = strong.result_counts["passed"], weak.result_counts["passed"]
    print(f"strong passed={s}/{strong.result_counts['total']}")
    print(f"weak   passed={w}/{weak.result_counts['total']}")
    if s > w:
        print("OK: regression signal detected (weak model scores lower).")
    else:
        print("WARN: expected strong > weak — inspect graders/data.")


if __name__ == "__main__":
    registry = EvalRegistry()
    runner = Runner()
    eval_obj = create_ticket_eval(registry)
    run_and_analyze(
        eval_obj,
        runner,
        ticket_classifier_stub,
        model_name="ticket-stub-v1",
        run_name="Categorization text run",
    )
    demo_prompt_regression(eval_obj, runner)
    print("\nAll eval demos finished.\n")
