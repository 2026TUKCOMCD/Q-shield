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


class RefactorCostEstimate(BaseModel):
    level: Literal["LOW", "MEDIUM", "HIGH"]
    explanation: str
    affected_files: int


class RecommendationPayload(BaseModel):
    title: str
    description: str
    nist_standard_reference: str
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


class AiAnalysisStartResponse(BaseModel):
    status: str
    scan_id: str
    ai_analysis_id: str | None = None
