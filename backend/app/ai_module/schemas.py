from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class Citation(BaseModel):
    doc_id: str
    title: str
    section: str
    page: int | None = None
    url: str | None = None
    snippet: str


class AffectedLocation(BaseModel):
    file_path: str
    line_start: int | None = None
    line_end: int | None = None
    rule_id: str | None = None
    scanner_type: str | None = None
    evidence_excerpt: str | None = None


class CodeFixExample(BaseModel):
    file_path: str
    language: str | None = None
    rationale: str
    before_code: str
    after_code: str
    confidence: float = Field(ge=0.0, le=1.0)


class RefactorCostEstimate(BaseModel):
    level: Literal["LOW", "MEDIUM", "HIGH"]
    explanation: str
    affected_files: int


class RecommendationPayload(BaseModel):
    title: str
    description: str
    nist_standard_reference: str
    affected_locations: list[AffectedLocation] = Field(default_factory=list)
    code_fix_examples: list[CodeFixExample] = Field(default_factory=list)
    citations: list[Citation] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)


class AiAnalysisResponse(BaseModel):
    risk_score: int = Field(ge=0, le=100)
    pqc_readiness_score: int = Field(ge=0, le=100)
    severity_weighted_index: float = Field(ge=0.0)
    refactor_cost_estimate: RefactorCostEstimate
    priority_rank: int = Field(ge=1)
    recommendations: list[RecommendationPayload] = Field(default_factory=list)
    analysis_summary: str
    confidence_score: float = Field(ge=0.0, le=1.0)
    citation_missing: bool
    inputs_summary: dict = Field(default_factory=dict)
    analysis_mode: Literal["real", "fallback", "mock", "error"] = "error"
    rag_corpus_loaded: bool = False
    rag_chunks_retrieved: int = 0
    citations_available: bool = False
    llm_model_used: str | None = None
    embedding_model_used: str | None = None
    vector_store_collection: str | None = None
    debug_message: str | None = None
    failure_reason: str | None = None


class AiAnalysisStartResponse(BaseModel):
    status: str
    scan_id: str
    ai_analysis_id: str | None = None
