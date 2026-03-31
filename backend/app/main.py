from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import feed, metrics, onboarding, outfit, reaction

app = FastAPI(
    title="ColorFit API",
    description="AI 퍼스널컬러 기반 패션 추천 엔진",
    version="0.1.0",
)

app.include_router(feed.router)
app.include_router(metrics.router)
app.include_router(onboarding.router)
app.include_router(outfit.router)
app.include_router(reaction.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    import os
    from pathlib import Path
    data_dir = Path(__file__).resolve().parents[1] / "data"
    files = []
    if data_dir.exists():
        files = [f"{f.name} ({f.stat().st_size})" for f in sorted(data_dir.iterdir()) if f.is_file()]
    return {
        "status": "ok",
        "service": "colorfit-api",
        "data_dir": str(data_dir),
        "data_files": files[:10],
        "cwd": os.getcwd(),
    }
