from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routers import config, notion, transcricoes

app = FastAPI(title="Transcriber API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",
        "tauri://localhost",
        "https://tauri.localhost",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(transcricoes.router, prefix="/api/transcricoes", tags=["transcricoes"])
app.include_router(notion.router, prefix="/api/notion", tags=["notion"])
app.include_router(config.router, prefix="/api/config", tags=["config"])


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
