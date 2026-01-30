from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime

# 1) POST /api/scans
class ScanCreateRequest(BaseModel):
    github_url: Optional[str] = None
    githubUrl: Optional[str] = None

class ScanCreateResponse(BaseModel):
    uuid: str


# 2) GET /api/scans/{uuid}/status
class ScanStatusResponse(BaseModel):
    uuid: str
    status: str
    progress: int = Field(ge=0, le=100)


# 3) GET /api/scans
class ScanListItem(BaseModel):
    uuid: str
    githubUrl: str
    status: str
    progress: int = Field(ge=0, le=100)
    createdAt: datetime
    updatedAt: datetime

class ScanListResponse(BaseModel):
    items: List[ScanListItem]


# 4) GET /api/scans/{uuid}/inventory
class InventoryAsset(BaseModel):
    id: str
    algorithmType: str
    filePath: str
    lineNumbers: List[int]
    riskScore: float


class InventoryResponse(BaseModel):
    uuid: str
    pqcReadinessScore: float
    algorithmRatios: Dict[str, float]
    inventory: List[InventoryAsset]


# 5) GET /api/scans/{uuid}/recommendations
class RecommendationItem(BaseModel):
    id: str
    priorityRank: int
    priority: str
    issueName: str
    estimatedEffort: str
    aiRecommendation: str
    recommendedPQCAlgorithm: str
    targetAlgorithm: str
    context: str
    filePath: Optional[str] = None


class RecommendationsResponse(BaseModel):
    uuid: str
    recommendations: List[RecommendationItem]


# 6) GET /api/scans/{uuid}/heatmap
class HeatmapNode(BaseModel):
    filePath: str
    fileName: str
    fileType: str  # "file" | "folder"
    aggregatedRiskScore: float
    children: Optional[List["HeatmapNode"]] = None


class HeatmapResponse(BaseModel):
    __root__: List[HeatmapNode]


try:
    HeatmapNode.model_rebuild()
except AttributeError:
    HeatmapNode.update_forward_refs()
