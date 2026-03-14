from __future__ import annotations

import json
import logging
from functools import lru_cache
from typing import Any

from app.ai_module.llm.prompts import build_system_prompt, build_user_prompt
from app.config import OPENAI_API_KEY, OPENAI_MODEL

logger = logging.getLogger(__name__)

try:
    from openai import OpenAI
except Exception:  # pragma: no cover - optional dependency in tests
    OpenAI = None


class LLMClientError(RuntimeError):
    pass


@lru_cache(maxsize=1)
def _get_client() -> Any:
    if OpenAI is None:
        raise LLMClientError("openai package is not installed")
    if not OPENAI_API_KEY:
        raise LLMClientError("OPENAI_API_KEY is not configured")
    return OpenAI(api_key=OPENAI_API_KEY)


def _extract_json_payload(raw_text: str) -> dict[str, Any]:
    text = (raw_text or "").strip()
    if not text:
        logger.error("ai_llm.parse status=failed reason=empty_output")
        raise LLMClientError("Empty response from OpenAI")

    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:]
        text = text.strip()

    try:
        loaded = json.loads(text)
    except json.JSONDecodeError:
        loaded = None
    if isinstance(loaded, dict):
        logger.info("ai_llm.parse status=success mode=direct_json")
        return loaded

    first = text.find("{")
    if first < 0:
        logger.error("ai_llm.parse status=failed reason=no_json_object")
        raise LLMClientError("No JSON object found in OpenAI response")

    depth = 0
    start = -1
    for index, char in enumerate(text[first:], start=first):
        if char == "{":
            if depth == 0:
                start = index
            depth += 1
            continue
        if char == "}":
            depth -= 1
            if depth == 0 and start >= 0:
                candidate = text[start : index + 1]
                try:
                    loaded = json.loads(candidate)
                except json.JSONDecodeError as exc:  # pragma: no cover - defensive path
                    raise LLMClientError(f"Failed to parse JSON payload: {exc}") from exc
                if isinstance(loaded, dict):
                    logger.info("ai_llm.parse status=success mode=substring_json")
                    return loaded
                raise LLMClientError("Parsed payload is not a JSON object")
    logger.error("ai_llm.parse status=failed reason=unbalanced_json")
    raise LLMClientError("Unbalanced JSON object in OpenAI response")


def _extract_output_text(response: Any) -> str:
    output_text = getattr(response, "output_text", None)
    if isinstance(output_text, str) and output_text.strip():
        return output_text

    outputs = getattr(response, "output", None)
    if isinstance(outputs, list):
        texts: list[str] = []
        for item in outputs:
            content = getattr(item, "content", None)
            if not isinstance(content, list):
                continue
            for part in content:
                part_text = getattr(part, "text", None)
                if isinstance(part_text, str):
                    texts.append(part_text)
        if texts:
            return "\n".join(texts)
    return ""


def generate_grounded_ai_analysis(
    *,
    findings: list[dict[str, Any]],
    retrieved_chunks: list[dict[str, Any]],
    risk_metrics: dict[str, Any],
    refactor_cost_estimate: dict[str, Any],
    priority_rank: int,
    inputs_summary: dict[str, Any],
) -> dict[str, Any]:
    client = _get_client()
    logger.info(
        "ai_llm.request stage=start model=%s findings=%s retrieved_chunks=%s",
        OPENAI_MODEL,
        len(findings),
        len(retrieved_chunks),
    )
    try:
        response = client.responses.create(
            model=OPENAI_MODEL,
            input=[
                {"role": "system", "content": build_system_prompt()},
                {
                    "role": "user",
                    "content": build_user_prompt(
                        findings=findings,
                        retrieved_chunks=retrieved_chunks,
                        risk_metrics=risk_metrics,
                        refactor_cost_estimate=refactor_cost_estimate,
                        priority_rank=priority_rank,
                        inputs_summary=inputs_summary,
                    ),
                },
            ],
        )
    except Exception as exc:
        logger.error("ai_llm.request stage=failed model=%s reason=%s", OPENAI_MODEL, str(exc))
        raise LLMClientError(f"OpenAI request failed: {exc}") from exc

    logger.info("ai_llm.request stage=success model=%s", OPENAI_MODEL)
    output_text = _extract_output_text(response)
    return _extract_json_payload(output_text)
