from __future__ import annotations

import uuid as uuid_lib

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import Finding, Scan
from app.schemas import FindingItem, FindingsResponse
from app.severity_map import canonicalize_severity


def _validate_scan_access(db: Session, scan_uuid: uuid_lib.UUID, user_uuid: uuid_lib.UUID | None = None) -> None:
    query = db.query(Scan).filter(Scan.uuid == scan_uuid)
    if user_uuid is not None:
        query = query.filter(Scan.user_uuid == user_uuid)
    if not query.first():
        raise HTTPException(status_code=404, detail="Scan not found")


def get_findings_response(
    db: Session,
    scan_uuid: uuid_lib.UUID,
    *,
    scanner_type: str | None = None,
    severity: str | None = None,
    limit: int = 50,
    offset: int = 0,
    user_uuid: uuid_lib.UUID | None = None,
    include_scan_validation: bool = True,
) -> FindingsResponse:
    if include_scan_validation:
        _validate_scan_access(db, scan_uuid, user_uuid=user_uuid)

    query = db.query(Finding).filter(Finding.scan_uuid == scan_uuid)

    if scanner_type:
        query = query.filter(Finding.context == str(scanner_type).upper())
    if severity:
        normalized_severity, _ = canonicalize_severity(severity)
        query = query.filter(Finding.severity == normalized_severity)

    total = int(query.count())
    safe_limit = max(1, min(int(limit or 50), 500))
    safe_offset = max(0, int(offset or 0))

    records = (
        query.order_by(Finding.id.asc())
        .offset(safe_offset)
        .limit(safe_limit)
        .all()
    )

    items = [
        FindingItem(
            id=int(record.id),
            type=record.type,
            severity=record.severity,
            algorithm=record.algorithm,
            context=record.context,
            file_path=record.file_path,
            line_start=record.line_start,
            line_end=record.line_end,
            evidence=record.evidence,
            meta=record.meta or {},
        )
        for record in records
    ]

    return FindingsResponse(
        scan_id=str(scan_uuid),
        total=total,
        limit=safe_limit,
        offset=safe_offset,
        items=items,
    )
