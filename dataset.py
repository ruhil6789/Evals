"""
Dataset loading — JSONL in the OpenAI evals shape:

  { "item": { "ticket_text": "...", "correct_label": "Hardware" } }
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterator


def load_jsonl(path: str | Path) -> list[dict]:
    path = Path(path)
    rows: list[dict] = []
    with path.open("r", encoding="utf-8") as f:
        for i, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            if "item" in obj:
                rows.append(obj["item"])
            else:
                rows.append(obj)
    return rows


def iter_jsonl(path: str | Path) -> Iterator[dict]:
    for item in load_jsonl(path):
        yield item


def save_jsonl(path: str | Path, items: list[dict]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for item in items:
            f.write(json.dumps({"item": item}, ensure_ascii=False) + "\n")
