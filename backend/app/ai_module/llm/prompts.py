from __future__ import annotations

import json
from collections import Counter
from typing import Any


def _format_context_blocks(retrieved_chunks: list[dict[str, Any]]) -> str:
    if not retrieved_chunks:
        return "(no retrieved context)"

    blocks: list[str] = []
    for index, chunk in enumerate(retrieved_chunks[:4], start=1):
        title = chunk.get("title") or "Unknown"
        page = chunk.get("page")
        doc_id = chunk.get("doc_id") or "unknown"
        section = chunk.get("section") or "N/A"
        text = str(chunk.get("text") or "").strip()[:700]
        blocks.append(
            (
                f"[DOC {index}] title={title} | section={section} | page={page} | source={doc_id}\n"
                f"{text}"
            )
        )
    return "\n\n".join(blocks)


def _compact_findings(findings: list[dict[str, Any]]) -> dict[str, Any]:
    severity_counter: Counter[str] = Counter()
    algorithm_counter: Counter[str] = Counter()
    examples: list[dict[str, Any]] = []

    for item in findings:
        severity = str(item.get("severity") or "UNKNOWN")
        severity_counter[severity] += 1
        algorithm = str(item.get("algorithm") or "UNKNOWN")
        algorithm_counter[algorithm] += 1

    for item in findings[:20]:
        evidence = str(item.get("evidence") or "").strip()
        if len(evidence) > 220:
            evidence = f"{evidence[:220]}..."
        meta = item.get("meta") or {}
        examples.append(
            {
                "type": item.get("type"),
                "severity": item.get("severity"),
                "algorithm": item.get("algorithm"),
                "context": item.get("context"),
                "file_path": item.get("file_path"),
                "line_start": item.get("line_start"),
                "line_end": item.get("line_end"),
                "rule_id": meta.get("rule_id"),
                "scanner_type": meta.get("scanner_type"),
                "evidence_excerpt": evidence or None,
            }
        )

    return {
        "total_findings": len(findings),
        "counts_by_severity": dict(severity_counter),
        "top_algorithms": [name for name, _ in algorithm_counter.most_common(8)],
        "example_findings": examples,
    }


def build_system_prompt() -> str:
    return (
        "You are a PQC migration analysis expert.\n"
        "Use only provided scan findings and retrieved NIST context.\n"
        "Return strict JSON only with no markdown.\n"
        "Never invent citations.\n"
        "Output schema keys:\n"
        "{\n"
        '  "risk_score": int (0..100),\n'
        '  "pqc_readiness_score": int (0..100),\n'
        '  "severity_weighted_index": float,\n'
        '  "refactor_cost_estimate": {\n'
        '    "level": "LOW" | "MEDIUM" | "HIGH",\n'
        '    "explanation": string,\n'
        '    "affected_files": int\n'
        "  },\n"
        '  "priority_rank": int,\n'
        '  "recommendations": [\n'
        "    {\n"
        '      "title": string,\n'
        '      "description": string,\n'
        '      "nist_standard_reference": string,\n'
        '      "affected_locations": [\n'
        "        {\n"
        '          "file_path": string,\n'
        '          "line_start": int | null,\n'
        '          "line_end": int | null,\n'
        '          "rule_id": string | null,\n'
        '          "scanner_type": string | null,\n'
        '          "evidence_excerpt": string | null\n'
        "        }\n"
        "      ],\n"
        '      "code_fix_examples": [\n'
        "        {\n"
        '          "file_path": string,\n'
        '          "language": string | null,\n'
        '          "rationale": string,\n'
        '          "before_code": string,\n'
        '          "after_code": string,\n'
        '          "confidence": float (0..1)\n'
        "        }\n"
        "      ],\n"
        '      "citations": [\n'
        "        {\n"
        '          "doc_id": string,\n'
        '          "title": string,\n'
        '          "section": string,\n'
        '          "page": int | null,\n'
        '          "url": string | null,\n'
        '          "snippet": string\n'
        "        }\n"
        "      ],\n"
        '      "confidence": float (0..1)\n'
        "    }\n"
        "  ],\n"
        '  "analysis_summary": string,\n'
        '  "confidence_score": float (0..1),\n'
        '  "citation_missing": bool,\n'
        '  "inputs_summary": object\n'
        "}\n"
    )


def build_user_prompt(
    *,
    findings: list[dict[str, Any]],
    retrieved_chunks: list[dict[str, Any]],
    risk_metrics: dict[str, Any],
    refactor_cost_estimate: dict[str, Any],
    priority_rank: int,
    inputs_summary: dict[str, Any],
) -> str:
    compact_findings = _compact_findings(findings)
    context_blocks = _format_context_blocks(retrieved_chunks)
    baseline = {
        "risk_metrics": risk_metrics,
        "refactor_cost_estimate": refactor_cost_estimate,
        "priority_rank": priority_rank,
        "inputs_summary": inputs_summary,
    }
    return (
        "SCAN_FINDINGS_COMPACT_JSON:\n"
        f"{json.dumps(compact_findings, ensure_ascii=False, indent=2)}\n\n"
        "RETRIEVED_NIST_CONTEXT:\n"
        f"{context_blocks}\n\n"
        "BASELINE_METRICS_JSON:\n"
        f"{json.dumps(baseline, ensure_ascii=False, indent=2)}\n\n"
        "Requirements:\n"
        "1. Keep output fully compatible with the required schema.\n"
        "2. Ground recommendations on retrieved context whenever possible.\n"
        "3. If context is insufficient, set citation_missing=true.\n"
        "4. Keep recommendations practical for repository migration work.\n"
        "5. For each recommendation include 1-3 affected_locations from provided findings.\n"
        "6. For each recommendation include at least 1 code_fix_examples item with before_code/after_code.\n"
        "7. Use actual finding evidence and file paths. If exact code is limited, provide conservative patch-style snippets.\n"
        "8. Include citation snippets exactly from retrieved context when used.\n"
        "9. Return JSON only.\n"
    )
