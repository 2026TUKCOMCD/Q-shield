# AI Module

This module adds deterministic PQC readiness analysis on top of normalized scan findings.

## Prerequisites

- Install backend dependencies:
  `pip install -r backend/requirements.txt`
- Run migrations:
  `cd backend`
  `alembic upgrade head`
- Configure the RAG corpus folder (optional but recommended):
  PowerShell:
  `$env:AI_RAG_CORPUS_PATH="C:\Users\KunWoongKyung\Documents\2025_2학기\컴퓨터응용설계\pqc문서"`

## Indexing

RAG indexing is lazy and cached on first retrieval. To pre-build the cache:

`cd backend`

`python -m app.ai_module.rag.indexer`

This writes a cached JSON index next to the corpus folder unless `AI_RAG_CACHE_PATH` is set.

## Endpoints

- `GET /api/scans/{uuid}/findings`
  Supports `scanner_type`, `severity`, `limit`, `offset`.
- `POST /api/scans/{uuid}/ai-analysis`
  Enqueues the Celery task and returns immediately.
- `GET /api/scans/{uuid}/ai-analysis`
  Returns the latest stored AI analysis snapshot.

## Run AI Analysis

1. Start the backend API and Celery worker.
2. Trigger analysis:
   `curl -X POST http://localhost:8000/api/scans/<scan-uuid>/ai-analysis -H "Authorization: Bearer <token>"`
3. Fetch the snapshot:
   `curl http://localhost:8000/api/scans/<scan-uuid>/ai-analysis -H "Authorization: Bearer <token>"`

## Local Tests

`$env:PYTHONDONTWRITEBYTECODE=1`

`pytest -p no:cacheprovider backend/tests/test_scoring.py backend/tests/test_ai_analysis.py`
