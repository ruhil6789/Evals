"""
Prompt templating — {{ item.field }} substitution into message lists.
"""

from __future__ import annotations

import re
from typing import Any


_VAR = re.compile(r"\{\{\s*item\.(\w+)\s*\}\}")


def render_value(value: Any, item: dict) -> Any:
    if not isinstance(value, str):
        return value

    def repl(m: re.Match) -> str:
        key = m.group(1)
        if key not in item:
            raise KeyError(f"template missing item.{key}")
        return str(item[key])

    return _VAR.sub(repl, value)


def render_messages(template: list[dict], item: dict) -> list[dict]:
    rendered = []
    for msg in template:
        rendered.append(
            {
                "role": msg["role"],
                "content": render_value(msg["content"], item),
            }
        )
    return rendered
