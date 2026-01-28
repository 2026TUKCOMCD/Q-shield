import time
from app.celery_app import celery_app
from app.store import get_scan, update_scan
from app.schemas import Finding

@celery_app.task(name="run_scan_pipeline", queue="celery")
def run_scan_pipeline(scan_id: int):
    scan = get_scan(scan_id)
    if not scan:
        return

    # RUNNING
    scan = scan.model_copy(update={"status": "RUNNING"})
    update_scan(scan_id, scan)

    # 실제 스캔 대신 더미 작업
    time.sleep(3)

    dummy_findings = [
        Finding(
            type="SAST",
            severity="HIGH",
            file_path="src/crypto_example.py",
            line_start=10,
            line_end=20,
            algorithm="RSA",
            evidence="RSA.generate(1024)",
            metadata={"key_size": 1024},
        )
    ]

    # DONE
    scan = scan.model_copy(update={
        "status": "DONE",
        "findings": dummy_findings,
    })
    update_scan(scan_id, scan)
