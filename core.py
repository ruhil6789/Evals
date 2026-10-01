"""
Core types for a framework-agnostic Evals harness.

Mental model (MIT systems × Anthropic deployment safety):
  Evals are structured tests for nondeterministic generators.
  Like BDD: specify desired behavior *before* you trust a prompt/model change.

Pipeline:
  1. Describe the task as an Eval (schema + graders)
  2. Run with a prompt template + dataset
  3. Analyze → iterate
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple
import json
import time
import uuid


class RunStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"


@dataclass
class DataSourceConfig:
    """Schema for eval items (analog of OpenAI data_source_config)."""

    type: str = "custom"
    item_schema: dict = field(default_factory=dict)
    include_sample_schema: bool = True

    def validate_item(self, item: dict) -> list:
        """Return list of validation errors (empty = ok)."""
        errors = []
        props = self.item_schema.get("properties", {})
        required = self.item_schema.get("required", list(props.keys()))
        for key in required:
            if key not in item:
                errors.append(f"missing required field: {key}")
        for key, spec in props.items():
            if key in item and spec.get("type") == "string" and not isinstance(item[key], str):
                errors.append(f"{key} must be string")
        return errors


@dataclass
class EvalSpec:
    """An eval definition: task name + data schema + testing criteria (graders)."""

    name: str
    data_source_config: DataSourceConfig
    testing_criteria: list  # list[Grader]
    id: str = field(default_factory=lambda: f"eval_{uuid.uuid4().hex[:24]}")
    created_at: float = field(default_factory=time.time)
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "object": "eval",
            "id": self.id,
            "name": self.name,
            "created_at": int(self.created_at),
            "data_source_config": {
                "type": self.data_source_config.type,
                "item_schema": self.data_source_config.item_schema,
                "include_sample_schema": self.data_source_config.include_sample_schema,
            },
            "testing_criteria": [g.to_dict() for g in self.testing_criteria],
            "metadata": self.metadata,
        }


@dataclass
class GradeResult:
    grader_name: str
    grader_id: str
    passed: bool
    score: float  # 0.0–1.0
    detail: str = ""
    raw: Any = None


@dataclass
class SampleResult:
    """One dataset row after model generation + grading."""

    item: dict
    output_text: str
    grades: list = field(default_factory=list)
    error: Optional[str] = None
    usage: dict = field(default_factory=dict)

    @property
    def passed(self) -> bool:
        if self.error:
            return False
        if not self.grades:
            return False
        return all(g.passed for g in self.grades)


@dataclass
class EvalRun:
    """Analog of OpenAI eval.run — local, synchronous by default."""

    eval_id: str
    name: str
    model: str
    id: str = field(default_factory=lambda: f"evalrun_{uuid.uuid4().hex[:24]}")
    status: RunStatus = RunStatus.QUEUED
    created_at: float = field(default_factory=time.time)
    samples: list = field(default_factory=list)
    error: Optional[str] = None
    metadata: dict = field(default_factory=dict)
    prompt_template: list = field(default_factory=list)

    @property
    def result_counts(self) -> dict:
        total = len(self.samples)
        errored = sum(1 for s in self.samples if s.error)
        passed = sum(1 for s in self.samples if s.passed)
        failed = sum(1 for s in self.samples if not s.passed and not s.error)
        return {
            "total": total,
            "errored": errored,
            "failed": failed,
            "passed": passed,
        }

    def per_testing_criteria_results(self) -> list:
        buckets: Dict[str, dict] = {}
        for s in self.samples:
            for g in s.grades:
                key = f"{g.grader_name}-{g.grader_id}"
                if key not in buckets:
                    buckets[key] = {
                        "testing_criteria": key,
                        "passed": 0,
                        "failed": 0,
                    }
                if g.passed:
                    buckets[key]["passed"] += 1
                else:
                    buckets[key]["failed"] += 1
        return list(buckets.values())

    def per_model_usage(self) -> list:
        prompt_tokens = completion_tokens = invocation = 0
        for s in self.samples:
            invocation += 1
            prompt_tokens += int(s.usage.get("prompt_tokens", 0))
            completion_tokens += int(s.usage.get("completion_tokens", 0))
        return [
            {
                "model_name": self.model,
                "invocation_count": invocation,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": prompt_tokens + completion_tokens,
                "cached_tokens": 0,
            }
        ]

    def to_dict(self, report_url: str = "") -> dict:
        return {
            "object": "eval.run",
            "id": self.id,
            "eval_id": self.eval_id,
            "report_url": report_url,
            "status": self.status.value,
            "model": self.model,
            "name": self.name,
            "created_at": int(self.created_at),
            "result_counts": self.result_counts,
            "per_model_usage": self.per_model_usage(),
            "per_testing_criteria_results": self.per_testing_criteria_results(),
            "error": self.error,
            "metadata": self.metadata,
        }

    def to_json(self, report_url: str = "") -> str:
        return json.dumps(self.to_dict(report_url=report_url), indent=2)


# Model callable: rendered messages → output text (+ optional usage)
ModelFn = Callable[[List[dict]], Tuple[str, dict]]
