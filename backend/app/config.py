import os
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = Path(__file__).resolve().parents[1]

load_dotenv(PROJECT_ROOT / ".env")
load_dotenv(BACKEND_ROOT / ".env")


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _resolve_env_path(value: str | None) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""

    path = Path(raw).expanduser()
    if path.is_absolute():
        return str(path)

    cwd_candidate = (Path.cwd() / path).resolve()
    if cwd_candidate.exists():
        return str(cwd_candidate)

    project_candidate = (PROJECT_ROOT / path).resolve()
    if project_candidate.exists():
        return str(project_candidate)

    backend_candidate = (BACKEND_ROOT / path).resolve()
    if backend_candidate.exists():
        return str(backend_candidate)

    # Keep relative-path behavior stable across API/Celery by anchoring to repository root.
    return str(project_candidate)


DATABASE_URL_SYNC = os.getenv("DATABASE_URL_SYNC")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
AUTH_SECRET_KEY = os.getenv("AUTH_SECRET_KEY", "dev-insecure-change-me")
AUTH_ACCESS_TOKEN_EXPIRES_MINUTES = int(os.getenv("AUTH_ACCESS_TOKEN_EXPIRES_MINUTES", "60"))
AUTH_ALGORITHM = "HS256"
FRONTEND_AUTH_CALLBACK_URL = os.getenv("FRONTEND_AUTH_CALLBACK_URL", "http://localhost:5173/auth/callback")
GOOGLE_OAUTH_CLIENT_ID = os.getenv("GOOGLE_OAUTH_CLIENT_ID", "")
GOOGLE_OAUTH_CLIENT_SECRET = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET", "")
GOOGLE_OAUTH_REDIRECT_URI = os.getenv("GOOGLE_OAUTH_REDIRECT_URI", "http://localhost:8000/api/auth/google/callback")
GITHUB_OAUTH_CLIENT_ID = os.getenv("GITHUB_OAUTH_CLIENT_ID", "")
GITHUB_OAUTH_CLIENT_SECRET = os.getenv("GITHUB_OAUTH_CLIENT_SECRET", "")
GITHUB_OAUTH_REDIRECT_URI = os.getenv("GITHUB_OAUTH_REDIRECT_URI", "http://localhost:8000/api/auth/github/callback")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5.4-pro")
OPENAI_EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-large")
AI_RAG_CORPUS_PATH = _resolve_env_path(os.getenv("AI_RAG_CORPUS_PATH", ""))
AI_RAG_CACHE_PATH = _resolve_env_path(os.getenv("AI_RAG_CACHE_PATH", ""))
AI_VECTOR_DB_DIR = _resolve_env_path(os.getenv("AI_VECTOR_DB_DIR", "./.qshield_chroma"))
AI_VECTOR_COLLECTION = os.getenv("AI_VECTOR_COLLECTION", "qshield_nist_rag")
AI_RAG_TOP_K = int(os.getenv("AI_RAG_TOP_K", "4"))
AI_ALLOW_DETERMINISTIC_FALLBACK = _env_bool("AI_ALLOW_DETERMINISTIC_FALLBACK", default=False)
AI_AUTO_INGEST_ON_EMPTY_VECTOR = _env_bool("AI_AUTO_INGEST_ON_EMPTY_VECTOR", default=False)
AI_CACHE_ENABLED = _env_bool("AI_CACHE_ENABLED", default=True)
AI_CACHE_MAX_AGE_HOURS = int(os.getenv("AI_CACHE_MAX_AGE_HOURS", "168"))
AI_ANALYSIS_VERSION = os.getenv("AI_ANALYSIS_VERSION", "v1")

if not DATABASE_URL_SYNC:
    raise RuntimeError("DATABASE_URL_SYNC is not set. Check backend/.env")
