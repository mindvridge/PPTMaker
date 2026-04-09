from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import generate, edit, export

app = FastAPI(
    title="DeckCraft API",
    description="AI PPT 생성 백엔드 서비스",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(generate.router, prefix="/api/generate", tags=["generate"])
app.include_router(edit.router, prefix="/api/edit", tags=["edit"])
app.include_router(export.router, prefix="/api/export", tags=["export"])


@app.get("/health")
async def health_check():
    return {"status": "ok"}
