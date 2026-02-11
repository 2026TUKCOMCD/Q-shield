import os
import sys
from pathlib import Path

os.environ.setdefault("DATABASE_URL_SYNC", "sqlite+pysqlite:///:memory:")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.severity_map import canonicalize_severity


def test_severity_mapping_examples():
    assert canonicalize_severity("HIGH")[0] == "HIGH"
    assert canonicalize_severity("critical")[0] == "CRITICAL"
    assert canonicalize_severity("warning")[0] == "MEDIUM"
