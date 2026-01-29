import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL_SYNC = os.getenv("DATABASE_URL_SYNC")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")

if not DATABASE_URL_SYNC:
    raise RuntimeError("DATABASE_URL_SYNC is not set. Check backend/.env")
