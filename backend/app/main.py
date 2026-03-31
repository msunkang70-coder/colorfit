from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import feed, outfit

app = FastAPI(
    title="ColorFit API",
    description="AI 퍼스널컬러 기반 패션 추천 엔진",
    version="0.1.0",
)

app.include_router(feed.router)
app.include_router(outfit.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "colorfit-api"}
