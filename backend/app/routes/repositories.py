from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import InventorySnapshot, Repository, Scan
from app.schemas import RepositoryListItem, ScanListItem
from app.security import require_user_uuid_from_auth_header


router = APIRouter(prefix="/api/repositories", tags=["repositories"])


def get_request_user_uuid(
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> UUID:
    return require_user_uuid_from_auth_header(authorization)


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


@router.get("", response_model=list[RepositoryListItem])
def list_repositories(
    db: Session = Depends(get_db),
    user_uuid: UUID = Depends(get_request_user_uuid),
):
    repos = (
        db.query(Repository)
        .filter(Repository.user_uuid == user_uuid)
        .filter(Repository.deleted_at.is_(None))
        .order_by(Repository.updated_at.desc())
        .all()
    )

    items: list[RepositoryListItem] = []
    for repo in repos:
        scans = (
            db.query(Scan)
            .filter(Scan.repository_id == repo.id)
            .order_by(Scan.created_at.desc())
            .all()
        )
        total_scans = len(scans)
        latest_scan = scans[0] if scans else None

        latest_score = None
        if latest_scan:
            inv = (
                db.query(InventorySnapshot)
                .filter(InventorySnapshot.scan_uuid == latest_scan.uuid)
                .first()
            )
            if inv:
                latest_score = float(inv.pqc_readiness_score or 0.0)

        items.append(
            RepositoryListItem(
                id=repo.id,
                provider=repo.provider,
                repoUrl=repo.repo_url,
                repoFullName=repo.repo_full_name,
                totalScans=total_scans,
                lastScanStatus=_map_status(latest_scan.status) if latest_scan else None,
                lastScannedAt=latest_scan.created_at if latest_scan else repo.last_scanned_at,
                latestPqcReadinessScore=latest_score,
            )
        )

    return items


@router.get("/{repository_id}/scans", response_model=list[ScanListItem])
def list_repository_scans(
    repository_id: int,
    db: Session = Depends(get_db),
    user_uuid: UUID = Depends(get_request_user_uuid),
):
    repo = (
        db.query(Repository)
        .filter(Repository.id == repository_id)
        .filter(Repository.user_uuid == user_uuid)
        .filter(Repository.deleted_at.is_(None))
        .first()
    )
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    scans = (
        db.query(Scan)
        .filter(Scan.repository_id == repository_id)
        .filter(Scan.user_uuid == user_uuid)
        .order_by(Scan.created_at.desc())
        .all()
    )

    return [
        ScanListItem(
            uuid=str(s.uuid),
            githubUrl=s.github_url,
            repositoryId=s.repository_id,
            status=_map_status(s.status),
            progress=_progress_percent(s.progress),
            createdAt=s.created_at,
            updatedAt=s.updated_at,
        )
        for s in scans
    ]
