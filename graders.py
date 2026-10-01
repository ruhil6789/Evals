"""
Graders — testing criteria that decide pass/fail (and optional score).

Analog of OpenAI testing_criteria / Graders docs:
  - string_check (eq, neq, contains, startswith, …)
  - regex_check
  - label_set (output ∈ allowed labels)
  - llm_judge stub (pluggable; default is heuristic for offline demos)

Research note: prefer graders that *discriminate* (match / compare / score
against rubric) over open-ended generation for the judge itself.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional
import re
import uuid

from core import GradeResult


def _render(template: str, item: dict, sample_output: str) -> str:
    """Minimal {{ item.x }} / {{ sample.output_text }} templating."""
    out = template
    out = out.replace("{{ sample.output_text }}", sample_output)
    out = out.replace("{{sample.output_text}}", sample_output)
    for key, val in item.items():
        out = out.replace(f"{{{{ item.{key} }}}}", str(val))
        out = out.replace(f"{{{{item.{key}}}}}", str(val))
    return out


@dataclass
class Grader:
    name: str
    type: str
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])

    def grade(self, item: dict, output_text: str) -> GradeResult:
        raise NotImplementedError

    def to_dict(self) -> dict:
        return {"name": self.name, "id": f"{self.name}-{self.id}", "type": self.type}


@dataclass
class StringCheckGrader(Grader):
    """
    Match model output to a reference (ground truth or another field).

    operations: eq | neq | contains | not_contains | startswith | endswith
    """

    type: str = "string_check"
    input: str = "{{ sample.output_text }}"
    reference: str = "{{ item.correct_label }}"
    operation: str = "eq"
    case_sensitive: bool = True
    strip: bool = True

    def grade(self, item: dict, output_text: str) -> GradeResult:
        left = _render(self.input, item, output_text)
        right = _render(self.reference, item, output_text)
        if self.strip:
            left, right = left.strip(), right.strip()
        if not self.case_sensitive:
            left, right = left.lower(), right.lower()

        op = self.operation
        if op == "eq":
            ok = left == right
        elif op == "neq":
            ok = left != right
        elif op == "contains":
            ok = right in left
        elif op == "not_contains":
            ok = right not in left
        elif op == "startswith":
            ok = left.startswith(right)
        elif op == "endswith":
            ok = left.endswith(right)
        else:
            return GradeResult(
                self.name, self.id, False, 0.0, detail=f"unknown operation {op}"
            )

        return GradeResult(
            grader_name=self.name,
            grader_id=self.id,
            passed=ok,
            score=1.0 if ok else 0.0,
            detail=f"{op}: {left!r} vs {right!r}",
            raw={"left": left, "right": right, "operation": op},
        )

    def to_dict(self) -> dict:
        d = super().to_dict()
        d.update(
            {
                "input": self.input,
                "reference": self.reference,
                "operation": self.operation,
            }
        )
        return d


@dataclass
class RegexGrader(Grader):
    type: str = "regex_check"
    pattern: str = r".+"
    must_match: bool = True

    def grade(self, item: dict, output_text: str) -> GradeResult:
        m = re.search(self.pattern, output_text.strip(), flags=re.IGNORECASE | re.DOTALL)
        ok = bool(m) if self.must_match else not bool(m)
        return GradeResult(
            self.name,
            self.id,
            ok,
            1.0 if ok else 0.0,
            detail=f"regex={self.pattern!r} matched={bool(m)}",
            raw={"match": m.group(0) if m else None},
        )


@dataclass
class LabelSetGrader(Grader):
    """Pass iff normalized output is in the allowed label set."""

    type: str = "label_set"
    labels: tuple = ("Hardware", "Software", "Other")

    def grade(self, item: dict, output_text: str) -> GradeResult:
        pred = output_text.strip()
        ok = pred in self.labels
        return GradeResult(
            self.name,
            self.id,
            ok,
            1.0 if ok else 0.0,
            detail=f"{pred!r} in {self.labels}",
        )


@dataclass
class RubricScoreGrader(Grader):
    """
    Lightweight stand-in for LLM-as-judge / G-Eval style scoring.

    Offline demo: heuristic coherence/length score in [0,1], pass if >= threshold.
    Swap `score_fn` for a real judge model in production.
    """

    type: str = "rubric_score"
    threshold: float = 0.5
    score_fn: Optional[Any] = None

    def grade(self, item: dict, output_text: str) -> GradeResult:
        if self.score_fn:
            score = float(self.score_fn(item, output_text))
        else:
            # Heuristic: non-empty, short categorical answers score high
            text = output_text.strip()
            if not text:
                score = 0.0
            elif len(text.split()) <= 3:
                score = 0.9
            elif len(text) < 200:
                score = 0.7
            else:
                score = 0.4
        ok = score >= self.threshold
        return GradeResult(
            self.name,
            self.id,
            ok,
            score,
            detail=f"score={score:.2f} threshold={self.threshold}",
        )
