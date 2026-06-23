"""Construtores de blocos Notion e montagem da estrutura da página de transcrição."""

from datetime import datetime
from typing import Dict, List, Optional

MAX_CHARS_POR_TEXTO = 2000
MAX_FILHOS_TOGGLE = 99


def _split_2000(texto: str) -> List[str]:
    if not texto:
        return [""]
    return [texto[i:i + MAX_CHARS_POR_TEXTO] for i in range(0, len(texto), MAX_CHARS_POR_TEXTO)]


def _bloco_paragrafo(texto: str, falante: Optional[str] = None) -> Dict:
    rich_text = []
    if falante:
        rich_text.append({"type": "text", "text": {"content": f"[{falante}] "}, "annotations": {"bold": True}})
    for pedaco in _split_2000(texto):
        rich_text.append({"type": "text", "text": {"content": pedaco}})
    return {"object": "block", "type": "paragraph", "paragraph": {"rich_text": rich_text}}


def _bloco_heading2(texto: str) -> Dict:
    return {
        "object": "block", "type": "heading_2",
        "heading_2": {"rich_text": [{"type": "text", "text": {"content": texto}}]},
    }


def _bloco_heading3(texto: str) -> Dict:
    return {
        "object": "block", "type": "heading_3",
        "heading_3": {"rich_text": [{"type": "text", "text": {"content": texto}}]},
    }


def _bloco_bullet(texto: str) -> Dict:
    return {
        "object": "block", "type": "bulleted_list_item",
        "bulleted_list_item": {
            "rich_text": [{"type": "text", "text": {"content": p}} for p in _split_2000(texto)]
        },
    }


def _bloco_todo(texto: str) -> Dict:
    return {
        "object": "block", "type": "to_do",
        "to_do": {
            "rich_text": [{"type": "text", "text": {"content": texto}}],
            "checked": False,
        },
    }


def _bloco_toggle(titulo: str, filhos: List[Dict]) -> Dict:
    return {
        "object": "block", "type": "toggle",
        "toggle": {
            "rich_text": [{"type": "text", "text": {"content": titulo}, "annotations": {"bold": True}}],
            "children": filhos[:MAX_FILHOS_TOGGLE],
        },
    }


def _filhos_transcricao(
    transcricao_completa: str,
    segmentos_com_falantes: Optional[List[Dict]],
    diarizar: bool,
) -> List[Dict]:
    filhos: List[Dict] = []
    if diarizar and segmentos_com_falantes:
        for seg in segmentos_com_falantes:
            texto = (seg.get("texto") or "").strip()
            if texto:
                filhos.append(_bloco_paragrafo(texto, falante=seg.get("falante", "DESCONHECIDO")))
    else:
        for pedaco in _split_2000(transcricao_completa or ""):
            if pedaco.strip():
                filhos.append(_bloco_paragrafo(pedaco))
    return filhos


def _filhos_resumo_ia(resumo: str) -> List[Dict]:
    filhos: List[Dict] = []
    for linha in resumo.split("\n"):
        linha = linha.strip()
        if not linha:
            continue
        if linha.startswith("## "):
            filhos.append(_bloco_heading2(linha[3:]))
        elif linha.startswith("- ") or linha.startswith("• "):
            filhos.append(_bloco_bullet(linha[2:]))
        elif linha.startswith("| "):
            filhos.append(_bloco_paragrafo(linha))
        else:
            filhos.append(_bloco_paragrafo(linha))
    return filhos


def _filhos_atividades(atividades: Dict[str, List[str]]) -> List[Dict]:
    filhos: List[Dict] = []
    for falante, tarefas in atividades.items():
        if not tarefas:
            continue
        filhos.append(_bloco_heading3(falante))
        for tarefa in tarefas:
            if tarefa.strip():
                filhos.append(_bloco_todo(tarefa.strip()))
    return filhos


def construir_blocos(
    transcricao_completa: str,
    segmentos_com_falantes: Optional[List[Dict]] = None,
    diarizar: bool = False,
    resumo: Optional[str] = None,
    atividades: Optional[Dict[str, List[str]]] = None,
) -> List[Dict]:
    data_str = datetime.now().strftime("%d/%m/%Y %H:%M")
    blocos: List[Dict] = [_bloco_paragrafo(f"Transcrição gerada em {data_str}")]

    filhos_tr = _filhos_transcricao(transcricao_completa, segmentos_com_falantes, diarizar)
    blocos.append(_bloco_toggle("📝 Transcrição Completa", filhos_tr))

    if resumo:
        filhos_rs = _filhos_resumo_ia(resumo)
        blocos.append(_bloco_toggle("📋 Resumo (IA)", filhos_rs))

    if atividades:
        filhos_at = _filhos_atividades(atividades)
        blocos.append(_bloco_toggle("✅ Atividades", filhos_at))

    return blocos
