import asyncio
import json
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import AsyncGenerator, Optional

sys.path.insert(0, str(Path(__file__).parent.parent))

from audio_processor import processar_audio  # noqa: E402

_executor = ThreadPoolExecutor(max_workers=1)

# Worker é único: garante 1 transcrição por vez. Um novo pedido cancela o
# anterior (último clique vence), evitando fila travada de jobs abandonados.
_ativo_lock = threading.Lock()
_cancelar_ativo: Optional[threading.Event] = None


async def stream_transcricao(
    arquivo: str,
    modelo: object,
    duracao_segmentos: int,
    diarizar: bool,
    pipeline: Optional[object],
    tempo_inicio: float,
    tempo_fim: Optional[float],
) -> AsyncGenerator[str, None]:
    queue: asyncio.Queue[dict] = asyncio.Queue()
    loop = asyncio.get_running_loop()
    cancelado = threading.Event()

    # Último clique vence: cancela o job anterior e assume como o ativo.
    global _cancelar_ativo
    with _ativo_lock:
        if _cancelar_ativo is not None:
            _cancelar_ativo.set()
        _cancelar_ativo = cancelado

    def _put(event: dict) -> None:
        loop.call_soon_threadsafe(queue.put_nowait, event)

    def cb_progress(p: float) -> None:
        _put({"type": "progress", "value": round(min(float(p), 1.0), 3)})

    def cb_status(msg: str) -> None:
        _put({"type": "status", "message": msg})

    def cb_preview(texto: str) -> None:
        if texto:
            _put({"type": "preview", "text": texto[:150]})

    callbacks = {
        "progress": cb_progress,
        "status": cb_status,
        "transcricao_preview": cb_preview,
        "deve_cancelar": cancelado.is_set,
    }

    future = loop.run_in_executor(
        _executor,
        lambda: processar_audio(
            arquivo,
            modelo,
            duracao_segmentos,
            callbacks,
            diarizar=diarizar,
            pipeline_diarizacao=pipeline,
            tempo_inicio=tempo_inicio,
            tempo_fim=tempo_fim,
        ),
    )

    try:
        while True:
            try:
                event = await asyncio.wait_for(queue.get(), timeout=0.4)
                yield f"data: {json.dumps(event)}\n\n"
            except asyncio.TimeoutError:
                if future.done():
                    break
                yield 'data: {"type":"heartbeat"}\n\n'

        while not queue.empty():
            event = queue.get_nowait()
            yield f"data: {json.dumps(event)}\n\n"

        try:
            resultado = await future
        except Exception as exc:
            import traceback
            payload = {"type": "error", "message": str(exc), "traceback": traceback.format_exc()}
            yield f"data: {json.dumps(payload)}\n\n"
            return

        yield f"data: {json.dumps({'type': 'complete', 'data': resultado})}\n\n"

    finally:
        # Cliente desconectou (GeneratorExit) ou terminou: libera o worker único,
        # sinalizando ao job para parar entre segmentos.
        cancelado.set()
        with _ativo_lock:
            if _cancelar_ativo is cancelado:
                _cancelar_ativo = None
