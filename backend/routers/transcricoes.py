import hashlib
import os
import sys
import tempfile
import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from fastapi.responses import StreamingResponse

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from audio_processor import (  # noqa: E402
    carregar_modelo_whisper_streamlit,
    carregar_pipeline_diarizacao_streamlit,
    detectar_tipo_arquivo,
)
from backend.model_cache import cache
from backend.models import ConfigTranscricao, UploadResponse
from backend.processing import stream_transcricao
from supabase_integration import (  # noqa: E402
    buscar_por_hash,
    buscar_transcricoes,
    listar_transcricoes,
    salvar_transcricao,
    verificar_supabase_configurado,
)

router = APIRouter()

_arquivos_tmp: dict[str, str] = {}


@router.post("/upload", response_model=UploadResponse)
async def upload_arquivo(file: UploadFile = File(...)) -> UploadResponse:
    conteudo = await file.read()

    sufixo = Path(file.filename or "audio.mp3").suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=sufixo) as tmp:
        tmp.write(conteudo)
        tmp_path = tmp.name

    file_id = str(uuid.uuid4())
    _arquivos_tmp[file_id] = tmp_path

    hash_arquivo = hashlib.sha256(conteudo).hexdigest()
    tipo = detectar_tipo_arquivo(tmp_path)
    duracao = _detectar_duracao(tmp_path, tipo)

    return UploadResponse(
        file_id=file_id,
        nome=file.filename or "arquivo",
        hash_arquivo=hash_arquivo,
        duracao=duracao,
        tipo=tipo,
    )


@router.get("/processar")
async def processar(
    file_id: str,
    modelo_nome: str = "base",
    duracao_segmentos: int = 4,
    diarizar: bool = True,
    tempo_inicio: float = 0.0,
    tempo_fim: Optional[float] = Query(default=None),
    hash_arquivo: str = "",
    nome_arquivo: str = "",
) -> StreamingResponse:
    tmp_path = _arquivos_tmp.get(file_id)
    if not tmp_path or not os.path.exists(tmp_path):
        raise HTTPException(status_code=404, detail="Arquivo não encontrado. Faça upload novamente.")

    _carregar_modelo(modelo_nome)
    if diarizar:
        _carregar_pipeline()

    cfg = ConfigTranscricao(
        modelo_nome=modelo_nome,
        duracao_segmentos=duracao_segmentos,
        diarizar=diarizar,
        tempo_inicio=tempo_inicio,
        tempo_fim=tempo_fim,
    )

    async def _gerar():
        async for chunk in stream_transcricao(
            arquivo=tmp_path,
            modelo=cache.modelo_whisper,
            duracao_segmentos=cfg.duracao_segmentos,
            diarizar=cfg.diarizar,
            pipeline=cache.pipeline_diarizacao if cfg.diarizar else None,
            tempo_inicio=cfg.tempo_inicio,
            tempo_fim=cfg.tempo_fim,
        ):
            yield chunk

        if hash_arquivo and nome_arquivo and verificar_supabase_configurado():
            pass

    return StreamingResponse(_gerar(), media_type="text/event-stream")


@router.post("/salvar")
async def salvar(payload: dict) -> dict:
    if not verificar_supabase_configurado():
        return {"ok": False, "motivo": "Supabase não configurado"}
    try:
        salvar_transcricao(
            hash_arquivo=payload["hash_arquivo"],
            nome_arquivo=payload["nome_arquivo"],
            transcricao_completa=payload.get("transcricao_completa", ""),
            segmentos_com_falantes=payload.get("segmentos_com_falantes", []),
            resumo_falantes=payload.get("resumo_falantes", {}),
            diarizacao_ativada=payload.get("diarizacao_ativada", False),
            modelo_whisper=payload.get("modelo_whisper", ""),
            duracao_total=float(payload.get("duracao_total", 0)),
        )
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "motivo": str(e)}


@router.get("/hash/{hash_arquivo}")
async def buscar_cache(hash_arquivo: str) -> dict:
    if not verificar_supabase_configurado():
        raise HTTPException(status_code=503, detail="Supabase não configurado")
    resultado = buscar_por_hash(hash_arquivo)
    if not resultado:
        raise HTTPException(status_code=404, detail="Não encontrado")
    return resultado


@router.get("/")
async def listar(limite: int = 100) -> list[dict]:
    if not verificar_supabase_configurado():
        return []
    return listar_transcricoes(limite=limite)


@router.get("/buscar")
async def buscar(
    termo: str = "",
    modelo: str = "",
    data_inicio: Optional[str] = None,
    data_fim: Optional[str] = None,
) -> list[dict]:
    if not verificar_supabase_configurado():
        return []
    return buscar_transcricoes(termo=termo, modelo=modelo, data_inicio=data_inicio, data_fim=data_fim)


def _detectar_duracao(tmp_path: str, tipo: str) -> Optional[float]:
    try:
        if tipo == "video":
            from moviepy.video.io.VideoFileClip import VideoFileClip
            vc = VideoFileClip(tmp_path)
            dur = float(vc.duration)
            vc.close()
            return dur
        else:
            import librosa
            return float(librosa.get_duration(path=tmp_path))
    except Exception:
        return None


def _carregar_modelo(modelo_nome: str) -> None:
    if cache.ultimo_modelo_nome != modelo_nome:
        cache.modelo_whisper = None
        cache.ultimo_modelo_nome = modelo_nome
    if cache.modelo_whisper is None:
        cache.modelo_whisper = carregar_modelo_whisper_streamlit(modelo_nome)


def _carregar_pipeline() -> None:
    if not cache.pipeline_carregado:
        try:
            cache.pipeline_diarizacao = carregar_pipeline_diarizacao_streamlit()
            cache.pipeline_carregado = True
        except Exception:
            cache.pipeline_carregado = False
