from __future__ import annotations

import uuid as uuid_lib

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.scan_read_service import get_findings_response


async def fetch_findings(scan_uuid: uuid_lib.UUID, db: Session, *, page_size: int = 200) -> list[dict] | None:
    items: list[dict] = []
    offset = 0

    while True:
        try:
            response = get_findings_response(
                db,
                scan_uuid,
                limit=page_size,
                offset=offset,
                include_scan_validation=True,
            )
        except HTTPException as exc:
            if exc.status_code == 404:
                return None
            raise
        batch = [item.model_dump() for item in response.items]
        if not batch:
            break
        items.extend(batch)
        offset += len(batch)
        if offset >= response.total:
            break

    return items
