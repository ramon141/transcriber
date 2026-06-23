import sys
from pathlib import Path

from fastapi import APIRouter, HTTPException

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.models import AssuntoNotion, EnvioNotion  # noqa: E402
from notion_integration import (  # noqa: E402
    criar_assunto,
    enviar_transcricao_notion,
    listar_assuntos,
    verificar_notion_configurado,
)

router = APIRouter()


@router.get("/status")
async def status() -> dict[str, bool]:
    return {"configurado": verificar_notion_configurado()}


@router.get("/assuntos", response_model=list[AssuntoNotion])
async def get_assuntos() -> list[AssuntoNotion]:
    if not verificar_notion_configurado():
        raise HTTPException(status_code=503, detail="Notion não configurado")
    try:
        assuntos = listar_assuntos()
        return [AssuntoNotion(id=a["id"], nome=a["nome"]) for a in assuntos]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/assuntos", response_model=AssuntoNotion)
async def post_assunto(payload: dict) -> AssuntoNotion:
    if not verificar_notion_configurado():
        raise HTTPException(status_code=503, detail="Notion não configurado")
    nome: str = payload.get("nome", "").strip()
    if not nome:
        raise HTTPException(status_code=422, detail="Nome obrigatório")
    try:
        assunto_id = criar_assunto(nome)
        return AssuntoNotion(id=assunto_id, nome=nome)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/enviar")
async def enviar(payload: EnvioNotion) -> dict[str, str]:
    if not verificar_notion_configurado():
        raise HTTPException(status_code=503, detail="Notion não configurado")
    try:
        url = enviar_transcricao_notion(
            assunto_id=payload.assunto_id,
            titulo=payload.titulo,
            transcricao_completa=payload.transcricao_completa,
            segmentos_com_falantes=payload.segmentos_com_falantes,
            resumo_falantes=payload.resumo_falantes,
            diarizar=payload.diarizar,
            resumo=payload.resumo,
        )
        return {"url": url or ""}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
