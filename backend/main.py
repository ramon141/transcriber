from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routers import notion, transcricoes

app = FastAPI(title="Transcriber API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(transcricoes.router, prefix="/api/transcricoes", tags=["transcricoes"])
app.include_router(notion.router, prefix="/api/notion", tags=["notion"])


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
