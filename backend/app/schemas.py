from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID

# 1) POST /api/scans
class ScanCreateRequest(BaseModel):
    github_url: str

class ScanCreateResponse(BaseModel):
    uuid: str
    status: str  # QUEUED | IN_PROGRESS ...


# 2) GET /api/scans/{uuid}/status
class ScanStatusResponse(BaseModel):
    status: str
    progress: float = Field(ge=0.0, le=1.0)
    message: str


# 3) GET /api/scans (이력)
class ScanListItem(BaseModel):
    uuid: str
    repo_name: str
    status: str
    created_at: datetime

class ScanListResponse(BaseModel):
    items: List[ScanListItem]
