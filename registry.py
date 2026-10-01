"""
Eval registry — create / store / retrieve eval specs (local filesystem).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from core import DataSourceConfig, EvalSpec
from graders import Grader


class EvalRegistry:
    def __init__(self, root: str | Path | None = None):
        self.root = Path(root or Path(__file__).parent / ".registry")
        self.root.mkdir(parents=True, exist_ok=True)
        self._mem: dict[str, EvalSpec] = {}

    def create(
        self,
        name: str,
        data_source_config: DataSourceConfig | dict,
        testing_criteria: list[Grader],
        metadata: dict | None = None,
    ) -> EvalSpec:
        if isinstance(data_source_config, dict):
            cfg = DataSourceConfig(
                type=data_source_config.get("type", "custom"),
                item_schema=data_source_config.get("item_schema", {}),
                include_sample_schema=data_source_config.get("include_sample_schema", True),
            )
        else:
            cfg = data_source_config

        spec = EvalSpec(
            name=name,
            data_source_config=cfg,
            testing_criteria=list(testing_criteria),
            metadata=metadata or {},
        )
        self._mem[spec.id] = spec
        path = self.root / f"{spec.id}.json"
        path.write_text(json.dumps(spec.to_dict(), indent=2), encoding="utf-8")
        return spec

    def get(self, eval_id: str) -> Optional[EvalSpec]:
        return self._mem.get(eval_id)

    def require(self, eval_id: str) -> EvalSpec:
        spec = self.get(eval_id)
        if not spec:
            raise KeyError(f"unknown eval_id: {eval_id}")
        return spec
