from typing import Dict
from app.schemas import ScanResponse

_scans: Dict[int, ScanResponse] = {}
_next_id: int = 1

def create_scan(scan: ScanResponse) -> ScanResponse:
    global _next_id
    scan = scan.model_copy(update={"id": _next_id})
    _scans[_next_id] = scan
    _next_id += 1
    return scan

def get_scan(scan_id: int) -> ScanResponse | None:
    return _scans.get(scan_id)

def update_scan(scan_id: int, scan: ScanResponse) -> None:
    _scans[scan_id] = scan
