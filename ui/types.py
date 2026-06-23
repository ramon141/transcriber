from typing import TypedDict


class SegmentoTranscricao(TypedDict, total=False):
    numero: int
    texto: str
    duracao: float


class SegmentoFalante(TypedDict, total=False):
    falante: str
    texto: str


class EstatFalante(TypedDict, total=False):
    num_falas: int
    tempo_total: float
    textos: list[str]


class ResultadoTranscricao(TypedDict, total=False):
    sucesso: bool
    transcricao_completa: str
    segmentos: list[SegmentoTranscricao]
    segmentos_com_falantes: list[SegmentoFalante]
    resumo_falantes: dict[str, EstatFalante]
    diarizacao_ativada: bool
    arquivo_completo: str
    arquivo_detalhado: str
    pasta_saida: str
    duracao_total: float
    erro: str
    traceback: str
    _from_cache: bool
