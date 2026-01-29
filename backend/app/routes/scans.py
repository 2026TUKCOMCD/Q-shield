from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import select
from uuid import UUID
from urllib.parse import urlparse

from app.db import get_db
from app.models import Scan
from app.models import InventorySnapshot, HeatmapSnapshot, Recommendation
from app.schemas import (
    ScanCreateRequest, ScanCreateResponse,
    ScanStatusResponse, ScanListItem, ScanListResponse
)
from app.tasks import run_scan_pipeline


router = APIRouter(prefix="/api/scans", tags=["scans"])


def extract_repo_name(github_url: str) -> str:
    parsed = urlparse(github_url)
    parts = parsed.path.strip("/").split("/")
    if len(parts) >= 2:
        return parts[1]
    return "unknown-repo"


@router.post("", response_model=ScanCreateResponse)
def create_scan(payload: ScanCreateRequest, db: Session = Depends(get_db)):
    repo_name = extract_repo_name(payload.github_url)

    scan = Scan(
        github_url=payload.github_url,
        repo_name=repo_name,
        status="QUEUED",
        progress=0.0,
        message="Queued",
    )
    db.add(scan)
    db.commit()
    db.refresh(scan)
    run_scan_pipeline.delay(str(scan.uuid))

    return ScanCreateResponse(uuid=str(scan.uuid), status=scan.status)


@router.get("/{uuid}/status", response_model=ScanStatusResponse)
def get_scan_status(uuid: str, db: Session = Depends(get_db)):
    try:
        scan_uuid = UUID(uuid)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid uuid")

    scan = db.execute(select(Scan).where(Scan.uuid == scan_uuid)).scalar_one_or_none()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")

    return ScanStatusResponse(status=scan.status, progress=scan.progress, message=scan.message)


@router.get("", response_model=ScanListResponse)
def list_scans(db: Session = Depends(get_db)):
    scans = db.execute(select(Scan).order_by(Scan.created_at.desc())).scalars().all()

    items = [
        ScanListItem(
            uuid=str(s.uuid),
            repo_name=s.repo_name,
            status=s.status,
            created_at=s.created_at,
        )
        for s in scans
    ]
    return ScanListResponse(items=items)



@router.get("/{uuid}/inventory")
def get_inventory(uuid: str, db: Session = Depends(get_db)):
    try:
        scan_uuid = UUID(uuid)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid uuid")

    inv = db.query(InventorySnapshot).filter(InventorySnapshot.scan_uuid == scan_uuid).first()
    if not inv:
        return {"pqc_readiness_score": 0, "algorithm_ratios": [], "inventory_table": []}

    return {
        "pqc_readiness_score": inv.pqc_readiness_score,
        "algorithm_ratios": inv.algorithm_ratios,
        "inventory_table": inv.inventory_table,
    }


@router.get("/{uuid}/heatmap")
def get_heatmap(uuid: str, db: Session = Depends(get_db)):
    try:
        scan_uuid = UUID(uuid)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid uuid")

    heat = db.query(HeatmapSnapshot).filter(HeatmapSnapshot.scan_uuid == scan_uuid).first()
    if not heat:
        return {"name": "", "path": "", "type": "dir", "risk_score": 0.0, "children": []}

    return heat.tree


@router.get("/{uuid}/recommendations")
def get_recommendations(
    uuid: str,
    db: Session = Depends(get_db),
    algorithm: str | None = Query(default=None),
    context: str | None = Query(default=None),
):
    try:
        scan_uuid = UUID(uuid)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid uuid")

    q = db.query(Recommendation).filter(Recommendation.scan_uuid == scan_uuid)

    # 프론트 요구사항: algorithm/context 필터링
    if algorithm:
        q = q.filter(Recommendation.algorithm == algorithm)
    if context:
        q = q.filter(Recommendation.context == context)

    recs = q.order_by(Recommendation.priority_rank.asc()).all()

    return [
        {
            "priority_rank": r.priority_rank,
            "estimated_effort": r.estimated_effort,
            "ai_recommendation": r.ai_recommendation,
        }
        for r in recs
    ]
