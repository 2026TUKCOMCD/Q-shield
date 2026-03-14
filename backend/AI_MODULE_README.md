# AI Module (RAG + OpenAI)

## Overview
The AI analysis pipeline keeps existing API/DB contracts and now runs with:
- corpus ingestion from local NIST PDF/TXT/MD files
- OpenAI embeddings
- persistent Chroma vector storage
- retrieval-grounded GPT response generation
- existing `AiAnalysisResponse` validation and snapshot persistence

The existing endpoints are unchanged:
- `POST /api/scans/{uuid}/ai-analysis`
- `GET /api/scans/{uuid}/ai-analysis`

The existing Celery task name is unchanged:
- `run_ai_analysis`

## Environment Variables
Set these in `backend/.env`:

```env
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-5.4-pro
OPENAI_EMBEDDING_MODEL=text-embedding-3-large

AI_RAG_CORPUS_PATH=/path/to/nist-pdf-folder
AI_VECTOR_DB_DIR=./.qshield_chroma
AI_VECTOR_COLLECTION=qshield_nist_rag
AI_RAG_TOP_K=4
AI_ALLOW_DETERMINISTIC_FALLBACK=false
AI_AUTO_INGEST_ON_EMPTY_VECTOR=false
AI_CACHE_ENABLED=true
AI_CACHE_MAX_AGE_HOURS=168
AI_ANALYSIS_VERSION=v2-rag-gpt54
```

Path note:
- `AI_RAG_CORPUS_PATH` and `AI_VECTOR_DB_DIR` are normalized to absolute paths at startup.
- Relative paths are resolved from the repository root (`Q-shield`), so `AI_RAG_CORPUS_PATH=backend/pqc` is valid regardless of API/Celery working directory.

Existing variables still used:
- `DATABASE_URL_SYNC`
- `REDIS_URL`
- `AI_RAG_CACHE_PATH` (legacy deterministic fallback index)
- Frontend: set `VITE_ENABLE_DEV_FALLBACKS=false` to avoid mock UI fallbacks during real E2E tests.

## Install
From `backend/`:

```bash
pip install -r requirements.txt
```

## Ingestion Command
Ingest your corpus before running AI analysis:

```bash
python -m app.ai_module.rag.ingest --corpus-path "$AI_RAG_CORPUS_PATH" --reset
```

Optional arguments:
- `--chunk-size` (default `1200`)
- `--overlap` (default `150`)
- `--batch-size` (default `64`)
- `--collection-name` (default `qshield_nist_rag`)

## Runtime Flow
1. `orchestrator.compute_and_persist_ai_analysis` fetches findings from the existing source.
2. Findings are normalized and summarized.
3. A retrieval query is built from findings.
4. Top N relevant chunks are retrieved from Chroma.
5. GPT (`OPENAI_MODEL`, default `gpt-5.4-pro`) is called with findings + retrieved context.
6. Output is validated against `AiAnalysisResponse`.
7. Existing `upsert_ai_analysis_snapshot` persists the analysis and citations.

## Transparent Modes
The response now exposes explicit mode and debug metadata:
- `analysis_mode`: `real | fallback | mock | error`
- `rag_corpus_loaded`
- `rag_chunks_retrieved`
- `citations_available`
- `llm_model_used`
- `embedding_model_used`
- `vector_store_collection`
- `debug_message`
- `failure_reason`

Recommendation payload includes code-fix oriented fields:
- `affected_locations`: file path / line / rule / evidence excerpt references from scan findings
- `code_fix_examples`: before/after patch-style snippets per affected file

## Cost Optimization
- Algorithm-signature cache: previously computed `real` analysis with citations is reused for matching algorithm signature.
- Prompt compaction: only compact findings summary and short examples are sent.
- Retrieval compaction: default top-k reduced to `AI_RAG_TOP_K=4`, and chunk text is truncated before prompt injection.

## Real E2E Test Workflow
1. Start dependencies:
```bash
cd backend
docker compose up -d
```
2. Install backend deps and run migrations:
```bash
pip install -r requirements.txt
alembic upgrade head
```
3. Ingest RAG corpus:
```bash
python -m app.ai_module.rag.ingest --corpus-path "$AI_RAG_CORPUS_PATH" --reset
```
4. Start API server:
```bash
uvicorn app.main:app --reload --port 8000
```
5. Start Celery worker (new terminal):
```bash
celery -A app.celery_app worker --loglevel=info
```
6. Trigger real scan + AI analysis:
```bash
curl -X POST http://localhost:8000/api/scans -H "Content-Type: application/json" -d "{\"githubUrl\":\"https://github.com/<owner>/<repo>\"}"
curl -X POST http://localhost:8000/api/scans/<scan-uuid>/ai-analysis
curl http://localhost:8000/api/scans/<scan-uuid>/ai-analysis
```
If you intentionally want to re-run analysis after fixing corpus/model settings:
```bash
curl -X POST "http://localhost:8000/api/scans/<scan-uuid>/ai-analysis?force=true"
```
7. Inspect DB snapshot directly (optional):
```sql
SELECT scan_uuid, analysis_version, citation_missing, citations_count, inputs_summary
FROM ai_analysis_snapshots
ORDER BY updated_at DESC
LIMIT 5;
```

## Logging Signals
Look for these stage logs:
- `ai_rag.ingest` (corpus detection, chunk count, embeddings stored)
- `ai_rag.corpus` (corpus/vector status)
- `ai_rag.retrieve` (query result and failure reason)
- `ai_llm.request` / `ai_llm.parse`
- `ai_analysis` / `ai_analysis_store` / `ai_analysis_task`
