from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal

ScanStatus = Literal["PENDING", "RUNNING", "DONE", "FAILED"]

class ScanCreateRequest(BaseModel):
    repo_url: str = Field(..., min_length=5)

class Finding(BaseModel):
    type: Literal["SAST", "SCA", "CONFIG"]
    severity: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    file_path: Optional[str] = None
    line_start: Optional[int] = None
    line_end: Optional[int] = None
    algorithm: Optional[str] = None
    evidence: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class ScanResponse(BaseModel):
    id: int
    repo_url: str
    status: ScanStatus
    error_log: Optional[str] = None
    findings: List[Finding] = []
