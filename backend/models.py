from pydantic import BaseModel
from typing import Optional


class ConfigTranscricao(BaseModel):
    modelo_nome: str = "base"
    duracao_segmentos: int = 4
    diarizar: bool = True
    tempo_inicio: float = 0.0
    tempo_fim: Optional[float] = None


class SegmentoTranscricao(BaseModel):
    numero: int = 0
    texto: str = ""
    duracao: float = 0.0


class SegmentoFalante(BaseModel):
    falante: str = ""
    texto: str = ""


class EstatFalante(BaseModel):
    num_falas: int = 0
    tempo_total: float = 0.0
    textos: list[str] = []


class ResultadoTranscricao(BaseModel):
    sucesso: bool
    transcricao_completa: str = ""
    segmentos: list[SegmentoTranscricao] = []
    segmentos_com_falantes: list[SegmentoFalante] = []
    resumo_falantes: dict[str, EstatFalante] = {}
    diarizacao_ativada: bool = False
    duracao_total: float = 0.0
    arquivo_completo: str = ""
    arquivo_detalhado: str = ""
    pasta_saida: str = ""
    erro: str = ""
    from_cache: bool = False


class UploadResponse(BaseModel):
    file_id: str
    nome: str
    hash_arquivo: str
    duracao: Optional[float]
    tipo: str


class AssuntoNotion(BaseModel):
    id: str
    nome: str


class EnvioNotion(BaseModel):
    assunto_id: str
    titulo: str
    transcricao_completa: str
    segmentos_com_falantes: list[dict] = []
    resumo_falantes: dict[str, dict] = {}
    diarizar: bool = False
    resumo: Optional[str] = None
