"""Shared helper for parsing JSON out of LLM responses (generation and judge prompts
both ask for JSON-only output but models sometimes wrap it in markdown code fences)."""

import json
import re
from typing import Any

_CODE_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.IGNORECASE | re.MULTILINE)


def parse_json_response(resposta_bruta: str) -> dict[str, Any]:
    """Strip optional markdown code fences and parse as JSON. Raises json.JSONDecodeError on failure."""
    texto = _CODE_FENCE_RE.sub("", resposta_bruta).strip()
    result: dict[str, Any] = json.loads(texto)
    return result
