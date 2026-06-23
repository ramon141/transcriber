from typing import Optional


class _Cache:
    modelo_whisper: Optional[object] = None
    ultimo_modelo_nome: Optional[str] = None
    pipeline_diarizacao: Optional[object] = None
    pipeline_carregado: bool = False


cache = _Cache()
