"""
Eval runner — create run, generate outputs, apply graders.

Mirrors: client.evals.runs.create(...) then retrieve status when completed.
Locally we run synchronously and write a markdown/JSON report.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Optional

from core import EvalRun, EvalSpec, RunStatus, SampleResult
from dataset import load_jsonl
from prompt import render_messages


class Runner:
    def __init__(self, reports_dir: str | Path | None = None):
        self.reports_dir = Path(reports_dir or Path(__file__).parent / "reports")
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        self._runs: dict[str, EvalRun] = {}

    def create_run(
        self,
        eval_spec: EvalSpec,
        *,
        name: str,
        model_name: str,
        model_fn: Callable,
        prompt_template: list[dict],
        data_path: str | Path,
        metadata: dict | None = None,
    ) -> EvalRun:
        run = EvalRun(
            eval_id=eval_spec.id,
            name=name,
            model=model_name,
            status=RunStatus.QUEUED,
            prompt_template=prompt_template,
            metadata=metadata or {},
        )
        self._runs[run.id] = run

        items = load_jsonl(data_path)
        run.status = RunStatus.RUNNING

        try:
            for item in items:
                errors = eval_spec.data_source_config.validate_item(item)
                if errors:
                    run.samples.append(
                        SampleResult(
                            item=item,
                            output_text="",
                            error="; ".join(errors),
                        )
                    )
                    continue

                try:
                    messages = render_messages(prompt_template, item)
                    output_text, usage = model_fn(messages)
                except Exception as e:  # noqa: BLE001 — capture per-row errors
                    run.samples.append(
                        SampleResult(item=item, output_text="", error=str(e))
                    )
                    continue

                grades = [g.grade(item, output_text) for g in eval_spec.testing_criteria]
                run.samples.append(
                    SampleResult(
                        item=item,
                        output_text=output_text,
                        grades=grades,
                        usage=usage or {},
                    )
                )

            run.status = RunStatus.COMPLETED
        except Exception as e:  # noqa: BLE001
            run.status = RunStatus.FAILED
            run.error = str(e)

        report_path = self.write_report(run, eval_spec)
        run.metadata["report_path"] = str(report_path)
        return run

    def retrieve(self, run_id: str, eval_id: str | None = None) -> EvalRun:
        run = self._runs.get(run_id)
        if not run:
            raise KeyError(f"unknown run_id: {run_id}")
        if eval_id and run.eval_id != eval_id:
            raise KeyError("eval_id does not match run")
        return run

    def write_report(self, run: EvalRun, eval_spec: EvalSpec) -> Path:
        from analyze import write_markdown_report

        path = self.reports_dir / f"{run.id}.md"
        write_markdown_report(path, run, eval_spec)
        json_path = self.reports_dir / f"{run.id}.json"
        json_path.write_text(
            run.to_json(report_url=str(path.resolve())), encoding="utf-8"
        )
        return path
