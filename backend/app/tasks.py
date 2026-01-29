import time
import uuid as uuid_lib
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import DATABASE_URL_SYNC
from app.models import Scan, InventorySnapshot, HeatmapSnapshot, Recommendation
from app.celery_app import celery_app

# Celery는 별도 프로세스라 get_db(Dependency) 못 씀 -> 엔진을 따로 만든다
engine = create_engine(DATABASE_URL_SYNC, echo=False, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def _mock_inventory():
    return {
        "pqc_readiness_score": 6.8,
        "algorithm_ratios": [
            {"name": "RSA", "ratio": 0.55},
            {"name": "ECC", "ratio": 0.25},
            {"name": "AES", "ratio": 0.20},
        ],
        "inventory_table": [
            {"algorithm": "RSA", "count": 12, "locations": ["src/auth.py:42", "src/crypto/rsa.py:10"]},
            {"algorithm": "ECC", "count": 5, "locations": ["src/tls.py:88"]},
        ],
    }


def _mock_heatmap():
    # 프론트에서 원하는 재귀 트리 형태를 그대로 tree에 저장
    return {
        "name": "Q-shield",
        "path": "",
        "type": "dir",
        "risk_score": 0.62,
        "children": [
            {
                "name": "backend",
                "path": "backend",
                "type": "dir",
                "risk_score": 0.70,
                "children": [
                    {
                        "name": "app",
                        "path": "backend/app",
                        "type": "dir",
                        "risk_score": 0.75,
                        "children": [
                            {
                                "name": "main.py",
                                "path": "backend/app/main.py",
                                "type": "file",
                                "risk_score": 0.80,
                            }
                        ],
                    }
                ],
            },
            {"name": "frontend", "path": "frontend", "type": "dir", "risk_score": 0.35, "children": []},
        ],
    }


def _mock_recommendations():
    return [
        {
            "priority_rank": 1,
            "estimated_effort": "2 M/D",
            "ai_recommendation": "## 1) 인증 구간 RSA 사용 감지\n- Kyber로 키교환 전환을 권장합니다.\n- TLS 설정에서 PFS를 강화하세요.\n",
            "algorithm": "RSA",
            "context": "auth",
        },
        {
            "priority_rank": 2,
            "estimated_effort": "1 M/D",
            "ai_recommendation": "## 2) ECC 서명 사용 감지\n- Dilithium 기반 서명으로 전환을 검토하세요.\n",
            "algorithm": "ECC",
            "context": "sign",
        },
    ]


@celery_app.task(name="run_scan_pipeline")
def run_scan_pipeline(scan_uuid: str):
    db = SessionLocal()
    scan_uuid_obj = None

    try:
        # 문자열 -> UUID로 변환 (DB 컬럼 타입이 UUID)
        scan_uuid_obj = uuid_lib.UUID(scan_uuid)

        scan = db.query(Scan).filter(Scan.uuid == scan_uuid_obj).first()
        if not scan:
            return

        # 1) 시작
        scan.status = "IN_PROGRESS"
        scan.progress = 0.05
        scan.message = "Cloning repository..."
        db.commit()

        time.sleep(1.2)

        # 2) 분석 단계
        scan.progress = 0.45
        scan.message = "Analyzing crypto usage..."
        db.commit()

        time.sleep(1.2)

        # 3) 결과 저장 (Mock)
        inv_payload = _mock_inventory()
        heat_payload = _mock_heatmap()

        # InventorySnapshot: data 컬럼이 없음. 3개 필드로 저장해야 함.
        inv = InventorySnapshot(
            scan_uuid=scan_uuid_obj,
            pqc_readiness_score=int(inv_payload.get("pqc_readiness_score", 0)),
            algorithm_ratios=inv_payload.get("algorithm_ratios", []),
            inventory_table=inv_payload.get("inventory_table", []),
        )

        # HeatmapSnapshot: tree 컬럼에 저장
        heat = HeatmapSnapshot(
            scan_uuid=scan_uuid_obj,
            tree=heat_payload,
        )

        # 기존 데이터가 있으면 교체(같은 scan_uuid가 PK라 중복 insert 시 에러 가능)
        db.merge(inv)
        db.merge(heat)

        # Recommendation: 여러 개 insert (기존 것 삭제하고 새로 넣는 방식 추천)
        db.query(Recommendation).filter(Recommendation.scan_uuid == scan_uuid_obj).delete()
        for rec in _mock_recommendations():
            db.add(Recommendation(scan_uuid=scan_uuid_obj, **rec))

        scan.progress = 0.90
        scan.message = "Generating recommendations..."
        db.commit()

        time.sleep(0.8)

        # 4) 완료
        scan.status = "COMPLETED"
        scan.progress = 1.0
        scan.message = "Completed"
        db.commit()

    except Exception as e:
        # 실패 처리
        try:
            if scan_uuid_obj is not None:
                scan = db.query(Scan).filter(Scan.uuid == scan_uuid_obj).first()
            else:
                scan = None
            if scan:
                scan.status = "FAILED"
                scan.progress = scan.progress or 0.0
                scan.message = f"Failed: {e}"
                scan.error_log = str(e)
                db.commit()
        except Exception:
            pass
        raise
    finally:
        db.close()
