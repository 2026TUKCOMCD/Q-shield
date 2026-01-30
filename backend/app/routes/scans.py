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
    ScanStatusResponse, ScanListItem,
    InventoryResponse, InventoryAsset,
    RecommendationsResponse, RecommendationItem,
    HeatmapResponse, HeatmapNode,
)
from app.tasks import run_scan_pipeline


router = APIRouter(prefix="/api/scans", tags=["scans"])


def extract_repo_name(github_url: str) -> str:
    parsed = urlparse(github_url)
    parts = parsed.path.strip("/").split("/")
    if len(parts) >= 2:
        return parts[1]
    return "unknown-repo"


def _map_status(status: str) -> str:
    if status == "QUEUED":
        return "PENDING"
    return status


def _progress_percent(progress: float | None) -> int:
    if progress is None:
        return 0
    pct = int(round(float(progress) * 100))
    if pct < 0:
        return 0
    if pct > 100:
        return 100
    return pct


def _rank_to_priority(rank: int) -> str:
    if rank <= 2:
        return "CRITICAL"
    if rank <= 5:
        return "HIGH"
    if rank <= 8:
        return "MEDIUM"
    return "LOW"


def _extract_issue_name(ai_recommendation: str, fallback: str) -> str:
    if not ai_recommendation:
        return fallback
    first_line = ai_recommendation.strip().splitlines()[0].strip()
    if first_line.startswith("## "):
        return first_line.replace("## ", "").strip() or fallback
    return fallback


def _build_inventory_assets(inv: InventorySnapshot) -> list[InventoryAsset]:
    assets: list[InventoryAsset] = []
    table = inv.inventory_table or []
    for entry in table:
        if not isinstance(entry, dict):
            continue
        algorithm = entry.get("algorithm", "Unknown")
        locations = entry.get("locations") or []
        if not locations:
            assets.append(
                InventoryAsset(
                    id=f"{algorithm}-1",
                    algorithmType=str(algorithm),
                    filePath="unknown",
                    lineNumbers=[],
                    riskScore=5.0,
                )
            )
            continue
        for idx, loc in enumerate(locations, start=1):
            file_path = "unknown"
            line_numbers: list[int] = []
            if isinstance(loc, str):
                if ":" in loc:
                    path_part, line_part = loc.rsplit(":", 1)
                    file_path = path_part or "unknown"
                    try:
                        line_numbers = [int(line_part)]
                    except ValueError:
                        line_numbers = []
                else:
                    file_path = loc
            assets.append(
                InventoryAsset(
                    id=f"{algorithm}-{idx}",
                    algorithmType=str(algorithm),
                    filePath=file_path,
                    lineNumbers=line_numbers,
                    riskScore=5.0,
                )
            )
    return assets


def _convert_heatmap_node(node: dict) -> HeatmapNode:
    name = str(node.get("name", ""))
    path = str(node.get("path", "")) or name
    node_type = node.get("type", "file")
    file_type = "folder" if node_type == "dir" else "file"
    risk_score = float(node.get("risk_score", 0.0) or 0.0)
    if risk_score <= 1.0:
        risk_score = risk_score * 10.0
    children_raw = node.get("children") or []
    children = [_convert_heatmap_node(child) for child in children_raw if isinstance(child, dict)]
    return HeatmapNode(
        filePath=path,
        fileName=name or path,
        fileType=file_type,
        aggregatedRiskScore=risk_score,
        children=children or None,
    )


@router.post("", response_model=ScanCreateResponse, status_code=202)
def create_scan(payload: ScanCreateRequest, db: Session = Depends(get_db)):
    github_url = payload.github_url or payload.githubUrl
    if not github_url:
        raise HTTPException(status_code=400, detail="githubUrl is required")

    repo_name = extract_repo_name(github_url)

    scan = Scan(
        github_url=github_url,
        repo_name=repo_name,
        status="QUEUED",
        progress=0.0,
        message="Queued",
    )
    db.add(scan)
    db.commit()
    db.refresh(scan)
    run_scan_pipeline.delay(str(scan.uuid))

    return ScanCreateResponse(uuid=str(scan.uuid))


@router.get("/{uuid}/status", response_model=ScanStatusResponse)
def get_scan_status(uuid: str, db: Session = Depends(get_db)):
    try:
        scan_uuid = UUID(uuid)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid uuid")

    scan = db.execute(select(Scan).where(Scan.uuid == scan_uuid)).scalar_one_or_none()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")

    return ScanStatusResponse(
        uuid=str(scan.uuid),
        status=_map_status(scan.status),
        progress=_progress_percent(scan.progress),
    )


@router.get("", response_model=list[ScanListItem])
def list_scans(db: Session = Depends(get_db)):
    scans = db.execute(select(Scan).order_by(Scan.created_at.desc())).scalars().all()

    items: list[ScanListItem] = [
        ScanListItem(
            uuid=str(s.uuid),
            githubUrl=s.github_url,
            status=_map_status(s.status),
            progress=_progress_percent(s.progress),
            createdAt=s.created_at,
            updatedAt=s.updated_at,
        )
        for s in scans
    ]
    return items


@router.get("/{uuid}/inventory", response_model=InventoryResponse)
def get_inventory(uuid: str, db: Session = Depends(get_db)):
    try:
        scan_uuid = UUID(uuid)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid uuid")

    inv = db.query(InventorySnapshot).filter(InventorySnapshot.scan_uuid == scan_uuid).first()
    if not inv:
        return InventoryResponse(
            uuid=str(scan_uuid),
            pqcReadinessScore=0.0,
            algorithmRatios={},
            inventory=[],
        )

    ratios = inv.algorithm_ratios or []
    if isinstance(ratios, dict):
        algorithm_ratios = {str(k): float(v) for k, v in ratios.items()}
    else:
        algorithm_ratios = {
            str(item.get("name")): float(item.get("ratio", 0.0))
            for item in ratios
            if isinstance(item, dict) and item.get("name") is not None
        }

    assets = _build_inventory_assets(inv)
    return {
        "uuid": str(scan_uuid),
        "pqcReadinessScore": float(inv.pqc_readiness_score or 0.0),
        "algorithmRatios": algorithm_ratios,
        "inventory": assets,
    }


@router.get("/{uuid}/inventory/{assetId}", response_model=InventoryAsset)
def get_inventory_asset(uuid: str, assetId: str, db: Session = Depends(get_db)):
    try:
        scan_uuid = UUID(uuid)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid uuid")

    inv = db.query(InventorySnapshot).filter(InventorySnapshot.scan_uuid == scan_uuid).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Scan inventory not found")

    assets = _build_inventory_assets(inv)
    for asset in assets:
        if asset.id == assetId:
            return asset

    raise HTTPException(status_code=404, detail="Asset not found")


@router.get("/{uuid}/heatmap", response_model=HeatmapResponse)
def get_heatmap(uuid: str, db: Session = Depends(get_db)):
    try:
        scan_uuid = UUID(uuid)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid uuid")

    heat = db.query(HeatmapSnapshot).filter(HeatmapSnapshot.scan_uuid == scan_uuid).first()
    if not heat:
        return []

    if not isinstance(heat.tree, dict):
        return []

    root = _convert_heatmap_node(heat.tree)
    return [root]


@router.get("/{uuid}/recommendations", response_model=RecommendationsResponse)
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

    # filter
    if algorithm:
        q = q.filter(Recommendation.algorithm == algorithm)
    if context:
        q = q.filter(Recommendation.context == context)

    recs = q.order_by(Recommendation.priority_rank.asc()).all()

    items: list[RecommendationItem] = []
    for r in recs:
        rank = int(r.priority_rank)
        issue_name = _extract_issue_name(r.ai_recommendation, f"Recommendation {rank}")
        file_path = r.context if (r.context and ("/" in r.context or "\\" in r.context)) else None
        items.append(
            RecommendationItem(
                id=str(r.id),
                priorityRank=rank,
                priority=_rank_to_priority(rank),
                issueName=issue_name,
                estimatedEffort=r.estimated_effort or "TBD",
                aiRecommendation=r.ai_recommendation or "",
                recommendedPQCAlgorithm="TBD",
                targetAlgorithm=r.algorithm or "Unknown",
                context=r.context or "",
                filePath=file_path,
            )
        )

    return RecommendationsResponse(uuid=str(scan_uuid), recommendations=items)
