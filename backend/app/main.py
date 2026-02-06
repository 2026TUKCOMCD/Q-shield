from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import CORS_ORIGINS
from app.routes.auth import router as auth_router
from app.routes.repositories import router as repositories_router
from app.routes.scans import router as scans_router

app = FastAPI(title="Q-shield Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in CORS_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(scans_router)
app.include_router(auth_router)
app.include_router(repositories_router)

@app.get("/health")
async def health():
    return {"ok": True}
