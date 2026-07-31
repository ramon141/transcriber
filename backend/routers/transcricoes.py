import asyncio
import hashlib
import json
import os
import shutil
import sys
import tempfile
import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from fastapi.responses import StreamingResponse

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from audio_processor import detectar_tipo_arquivo  # noqa: E402
from split_audio import carregar_modelo_whisper  # noqa: E402
from diarization import carregar_pipeline_diarizacao  # noqa: E402
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

# Uploads persistidos em disco: nome = file_id + sufixo. Sobrevive a restart
# do backend (o mapa em memória sumia e quebrava o processar após reload).
_UPLOAD_DIR = Path(tempfile.gettempdir()) / "transcriber_uploads"
_UPLOAD_DIR.mkdir(exist_ok=True)


def _buscar_upload(file_id: str) -> Optional[str]:
    encontrados = list(_UPLOAD_DIR.glob(f"{file_id}.*"))
    return str(encontrados[0]) if encontrados else None


def limpar_uploads() -> None:
    # Remove uploads e pastas _dividido órfãos da sessão anterior (startup).
    for item in _UPLOAD_DIR.glob("*"):
        try:
            shutil.rmtree(item) if item.is_dir() else item.unlink()
        except OSError:
            pass


@router.post("/upload", response_model=UploadResponse)
async def upload_arquivo(file: UploadFile = File(...)) -> UploadResponse:
    conteudo = await file.read()

    file_id = str(uuid.uuid4())
    sufixo = Path(file.filename or "audio.mp3").suffix
    tmp_path = str(_UPLOAD_DIR / f"{file_id}{sufixo}")
    with open(tmp_path, "wb") as tmp:
        tmp.write(conteudo)

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
    tmp_path = _buscar_upload(file_id)
    if not tmp_path or not os.path.exists(tmp_path):
        raise HTTPException(status_code=404, detail="Arquivo não encontrado. Faça upload novamente.")

    cfg = ConfigTranscricao(
        modelo_nome=modelo_nome,
        duracao_segmentos=duracao_segmentos,
        diarizar=diarizar,
        tempo_inicio=tempo_inicio,
        tempo_fim=tempo_fim,
    )

    async def _gerar():
        # Carrega modelos DENTRO do stream, emitindo status antes de cada carga.
        # Antes rodavam na rota (fetch ficava mudo por 30-60s no 1º uso).
        loop = asyncio.get_running_loop()

        # A carga do modelo/pipeline roda em thread; enquanto isso emitimos
        # heartbeats num loop com await. Sem esses yields periódicos, o chunk
        # de status fica preso no buffer e só aparece quando a carga termina.
        yield _sse_status(f"Carregando modelo Whisper ({modelo_nome})...")
        async for hb in _carregar_com_heartbeat(loop, _carregar_modelo, modelo_nome):
            yield hb

        if diarizar:
            yield _sse_status("Carregando identificação de falantes...")
            async for hb in _carregar_com_heartbeat(loop, _carregar_pipeline):
                yield hb

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

        # Transcrição terminou: remove o upload e a pasta _dividido do disco.
        # Se o cliente desconectar antes (GeneratorExit), não chega aqui e os
        # arquivos ficam para o reprocessamento (último-clique-vence).
        try:
            os.remove(tmp_path)
            pasta = _UPLOAD_DIR / f"{Path(tmp_path).stem}_dividido"
            shutil.rmtree(pasta, ignore_errors=True)
        except OSError:
            pass

    # Headers anti-buffering do SSE. A causa do "status só aparece em lote":
    # o proxy dev do Next.js comprimia (gzip) o event-stream quando o Chrome
    # mandava Accept-Encoding, e o gzip acumula blocos antes de enviar.
    # no-transform proíbe o proxy de comprimir; nosniff e X-Accel-Buffering
    # são proteções extras contra buffering de browser/proxy reverso.
    return StreamingResponse(
        _gerar(),
        media_type="text/event-stream",
        headers={
            "X-Content-Type-Options": "nosniff",
            "Cache-Control": "no-cache, no-transform",
            "X-Accel-Buffering": "no",
        },
    )


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


@router.post("/resumir")
async def resumir_texto(payload: dict) -> dict[str, str]:
    import asyncio
    from backend.summarizer import resumir_transcricao

    texto = str(payload.get("transcricao", "")).strip()
    if not texto:
        raise HTTPException(status_code=422, detail="Campo 'transcricao' obrigatório")

    try:
        loop = asyncio.get_event_loop()
        resumo = await loop.run_in_executor(None, resumir_transcricao, texto)
        return {"resumo": resumo}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/atividades")
async def extrair_atividades_endpoint(payload: dict) -> dict[str, dict[str, list[str]]]:
    import asyncio
    from backend.summarizer import extrair_atividades

    texto = str(payload.get("transcricao", "")).strip()
    if not texto:
        raise HTTPException(status_code=422, detail="Campo 'transcricao' obrigatório")

    try:
        loop = asyncio.get_event_loop()
        atividades = await loop.run_in_executor(None, extrair_atividades, texto)
        return {"atividades": atividades}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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


def _sse_status(mensagem: str) -> str:
    return f"data: {json.dumps({'type': 'status', 'message': mensagem})}\n\n"


async def _carregar_com_heartbeat(loop, func, *args):
    # Roda a carga (bloqueante, GIL-pesada) em thread e emite heartbeats
    # enquanto ela não termina, forçando o flush do stream para o cliente.
    future = loop.run_in_executor(None, func, *args)
    while not future.done():
        yield 'data: {"type":"heartbeat"}\n\n'
        await asyncio.sleep(0.3)
    await future


def _carregar_modelo(modelo_nome: str) -> None:
    if cache.ultimo_modelo_nome != modelo_nome:
        cache.modelo_whisper = None
        cache.ultimo_modelo_nome = modelo_nome
    if cache.modelo_whisper is None:
        cache.modelo_whisper = carregar_modelo_whisper(modelo_nome)


def _carregar_pipeline() -> None:
    if not cache.pipeline_carregado:
        try:
            cache.pipeline_diarizacao = carregar_pipeline_diarizacao()
            cache.pipeline_carregado = True
        except Exception:
            cache.pipeline_carregado = False
