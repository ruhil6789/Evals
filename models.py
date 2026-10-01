"""
Model backends for eval runs.

- TicketClassifierStub: offline rule-based stand-in (no API key)
- OpenAIResponsesAdapter: optional live API if OPENAI_API_KEY is set
"""

from __future__ import annotations

import os
import re
from typing import Callable


def estimate_usage(messages: list[dict], output: str) -> dict:
    prompt = " ".join(m.get("content", "") for m in messages)
    # Rough tok≈words heuristic for local demos
    return {
        "prompt_tokens": max(1, len(prompt.split())),
        "completion_tokens": max(1, len(output.split())),
    }


def ticket_classifier_stub(messages: list[dict]) -> tuple[str, dict]:
    """
    Deterministic IT ticket categorizer for offline evals.
    Mimics the doc example labels: Hardware | Software | Other.
    """
    user = ""
    for m in messages:
        if m.get("role") == "user":
            user = m.get("content", "")
    text = user.lower()

    hardware = [
        r"monitor",
        r"keyboard",
        r"mouse",
        r"laptop",
        r"printer",
        r"hardware",
        r"won't turn on",
        r"wont turn on",
        r"screen",
        r"battery",
    ]
    software = [
        r"\bvim\b",
        r"windows",
        r"crash",
        r"install",
        r"software",
        r"app(lication)?",
        r"password reset",
        r"excel",
        r"browser",
        r"can't quit",
        r"cant quit",
    ]

    if any(re.search(p, text) for p in hardware):
        out = "Hardware"
    elif any(re.search(p, text) for p in software):
        out = "Software"
    else:
        out = "Other"

    return out, estimate_usage(messages, out)


def weak_ticket_classifier(messages: list[dict]) -> tuple[str, dict]:
    """Intentionally weak model — always Other — for regression demos."""
    out = "Other"
    return out, estimate_usage(messages, out)


def openai_responses_adapter(
    model: str = "gpt-4.1-mini",
) -> Callable[[list[dict]], tuple[str, dict]]:
    """
    Optional live backend. Requires `openai` package + OPENAI_API_KEY.
    Falls back with a clear error if unavailable.
    """

    def _call(messages: list[dict]) -> tuple[str, dict]:
        try:
            from openai import OpenAI
        except ImportError as e:
            raise RuntimeError("pip install openai to use live Responses API") from e
        if not os.environ.get("OPENAI_API_KEY"):
            raise RuntimeError("Set OPENAI_API_KEY for live evals")

        client = OpenAI()
        # Map developer→system for broader SDK compatibility
        mapped = []
        for m in messages:
            role = m["role"]
            if role == "developer":
                role = "system"
            mapped.append({"role": role, "content": m["content"]})

        resp = client.chat.completions.create(model=model, messages=mapped, temperature=0)
        text = (resp.choices[0].message.content or "").strip()
        usage = {
            "prompt_tokens": getattr(resp.usage, "prompt_tokens", 0) or 0,
            "completion_tokens": getattr(resp.usage, "completion_tokens", 0) or 0,
        }
        return text, usage

    return _call
