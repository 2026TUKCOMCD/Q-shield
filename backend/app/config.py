import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL_SYNC = os.getenv("DATABASE_URL_SYNC")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
AUTH_SECRET_KEY = os.getenv("AUTH_SECRET_KEY", "dev-insecure-change-me")
AUTH_ACCESS_TOKEN_EXPIRES_MINUTES = int(os.getenv("AUTH_ACCESS_TOKEN_EXPIRES_MINUTES", "60"))
AUTH_ALGORITHM = "HS256"

if not DATABASE_URL_SYNC:
    raise RuntimeError("DATABASE_URL_SYNC is not set. Check backend/.env")
