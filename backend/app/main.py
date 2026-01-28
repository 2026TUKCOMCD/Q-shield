import time

from fastapi import FastAPI, HTTPException
from app.schemas import ScanCreateRequest, ScanResponse
from app.store import create_scan, get_scan
from app.celery_app import celery_app

app = FastAPI(title="Q-shield API", version="0.1.0")

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/scans", response_model=ScanResponse)
def post_scans(payload: ScanCreateRequest):
    scan = ScanResponse(
        id=0,
        repo_url=payload.repo_url,
        status="PENDING",
        findings=[],
    )
    created = create_scan(scan)

    print(f"[API] enqueue scan_id={created.id} repo={created.repo_url}")
    r = celery_app.send_task("run_scan_pipeline", args=[created.id], queue="celery")
    print(f"[API] celery task sent id={r.id}")

    return created

@app.get("/scans/{scan_id}", response_model=ScanResponse)
def get_scans(scan_id: int):
    scan = get_scan(scan_id)
    if not scan:
        raise HTTPException(status_code=404, detail="scan not found")
    return scan
