"""
Analyze eval runs — result counts, per-criteria breakdown, markdown report.
"""

from __future__ import annotations

from pathlib import Path

from core import EvalRun, EvalSpec


def summarize(run: EvalRun) -> str:
    rc = run.result_counts
    lines = [
        f"Run: {run.name} ({run.id})",
        f"Status: {run.status.value}",
        f"Model: {run.model}",
        f"Results: passed={rc['passed']} failed={rc['failed']} "
        f"errored={rc['errored']} total={rc['total']}",
        "",
        "Per testing criteria:",
    ]
    for row in run.per_testing_criteria_results():
        lines.append(
            f"  - {row['testing_criteria']}: "
            f"passed={row['passed']} failed={row['failed']}"
        )
    lines.append("")
    lines.append("Samples:")
    for i, s in enumerate(run.samples, 1):
        label = "PASS" if s.passed else ("ERROR" if s.error else "FAIL")
        pred = s.output_text if not s.error else f"<error: {s.error}>"
        ref = s.item.get("correct_label", "")
        ticket = s.item.get("ticket_text", s.item)
        lines.append(f"  [{label}] #{i} pred={pred!r} ref={ref!r}  ticket={ticket!r}")
        for g in s.grades:
            lines.append(f"       grader={g.grader_name} score={g.score:.2f} {g.detail}")
    return "\n".join(lines)


def write_markdown_report(path: str | Path, run: EvalRun, eval_spec: EvalSpec) -> None:
    path = Path(path)
    rc = run.result_counts
    pass_rate = (rc["passed"] / rc["total"]) if rc["total"] else 0.0

    md = [
        f"# Eval report: {run.name}",
        "",
        f"- **eval**: `{eval_spec.name}` (`{run.eval_id}`)",
        f"- **run**: `{run.id}`",
        f"- **status**: `{run.status.value}`",
        f"- **model**: `{run.model}`",
        f"- **pass rate**: **{pass_rate:.0%}** "
        f"({rc['passed']}/{rc['total']}; failed={rc['failed']}, errored={rc['errored']})",
        "",
        "## Per-criteria results",
        "",
        "| Criteria | Passed | Failed |",
        "|----------|--------|--------|",
    ]
    for row in run.per_testing_criteria_results():
        md.append(
            f"| `{row['testing_criteria']}` | {row['passed']} | {row['failed']} |"
        )

    md += ["", "## Samples", ""]
    for i, s in enumerate(run.samples, 1):
        label = "PASS" if s.passed else ("ERROR" if s.error else "FAIL")
        md.append(f"### #{i} — {label}")
        md.append("")
        md.append(f"- item: `{s.item}`")
        md.append(f"- output: `{s.output_text}`")
        if s.error:
            md.append(f"- error: `{s.error}`")
        for g in s.grades:
            md.append(
                f"- grader `{g.grader_name}`: passed={g.passed} "
                f"score={g.score:.2f} — {g.detail}"
            )
        md.append("")

    md += [
        "## Usage",
        "",
        "```json",
        str(run.per_model_usage()),
        "```",
        "",
        "## Research notes",
        "",
        "- Treat this report as a **signal**, not a certificate of safety.",
        "- Calibrate automated graders against human labels before scaling.",
        "- Grow the dataset with production edge cases (logs → eval items).",
        "",
    ]
    path.write_text("\n".join(md), encoding="utf-8")
