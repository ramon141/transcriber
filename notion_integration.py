#!/usr/bin/env python3
"""
Módulo de integração com o Notion para o Transcriber.

Envia transcrições para o Notion seguindo a estrutura:

    Reuniões (NOTION_PARENT_ID)
    ├── Assunto X        <- sub-página por tema (assunto)
    │   └── Reunião ...  <- página da transcrição
    ├── Assunto Y
    │   └── ...

Cada transcrição vira uma página dentro da sub-página do assunto escolhido.
"""

import os
from datetime import datetime
from typing import List, Dict, Optional
from dotenv import load_dotenv

# Carrega variáveis de ambiente do arquivo .env
load_dotenv()

# Limites da API do Notion
MAX_BLOCOS_POR_REQUEST = 100
MAX_CHARS_POR_TEXTO = 2000


def obter_token_notion() -> Optional[str]:
    """Obtém o token de integração do Notion do arquivo .env."""
    return os.getenv("NOTION_TOKEN")


def obter_parent_id() -> Optional[str]:
    """Obtém o ID da página-pai 'Reuniões' do arquivo .env."""
    return os.getenv("NOTION_PARENT_ID")


def verificar_notion_configurado() -> bool:
    """
    Verifica se o token e a página-pai do Notion estão configurados.

    Returns:
        True se ambos configurados, False caso contrário
    """
    token = obter_token_notion()
    parent = obter_parent_id()
    return bool(token) and bool(parent)


def _get_client():
    """
    Cria e retorna o cliente do Notion.

    Raises:
        ImportError: Se notion-client não estiver instalado
        ValueError: Se o token não estiver configurado
    """
    try:
        from notion_client import Client
    except ImportError:
        raise ImportError(
            "notion-client não está instalado. Execute: pip install notion-client"
        )

    token = obter_token_notion()
    if not token:
        raise ValueError(
            "Token do Notion não configurado. "
            "Crie um arquivo .env com NOTION_TOKEN=secret_xxx. "
            "Obtenha em: https://www.notion.so/my-integrations"
        )

    return Client(auth=token)


def listar_assuntos(parent_id: Optional[str] = None) -> List[Dict]:
    """
    Lista as sub-páginas (assuntos) da página-pai 'Reuniões'.

    Args:
        parent_id: ID da página-pai (opcional, usa .env se não fornecido)

    Returns:
        Lista de assuntos: [{'nome': 'Assunto X', 'id': '...'}, ...]
    """
    client = _get_client()
    pid = parent_id or obter_parent_id()

    if not pid:
        raise ValueError(
            "Página-pai do Notion não configurada. "
            "Adicione NOTION_PARENT_ID=id_da_pagina ao arquivo .env."
        )

    assuntos = []
    cursor = None

    # Pagina por todos os blocos filhos da página-pai
    while True:
        params = {"block_id": pid, "page_size": 100}
        if cursor:
            params["start_cursor"] = cursor

        resposta = client.blocks.children.list(**params)

        for bloco in resposta.get("results", []):
            if bloco.get("type") == "child_page":
                assuntos.append({
                    "nome": bloco["child_page"]["title"],
                    "id": bloco["id"],
                })

        if resposta.get("has_more"):
            cursor = resposta.get("next_cursor")
        else:
            break

    return assuntos


def criar_assunto(nome: str, parent_id: Optional[str] = None) -> str:
    """
    Cria uma nova sub-página de assunto dentro de 'Reuniões'.

    Args:
        nome: Nome do assunto
        parent_id: ID da página-pai (opcional, usa .env se não fornecido)

    Returns:
        ID da sub-página criada
    """
    client = _get_client()
    pid = parent_id or obter_parent_id()

    if not pid:
        raise ValueError(
            "Página-pai do Notion não configurada. "
            "Adicione NOTION_PARENT_ID=id_da_pagina ao arquivo .env."
        )

    pagina = client.pages.create(
        parent={"page_id": pid},
        properties={
            "title": [{"text": {"content": nome}}]
        },
    )
    return pagina["id"]


def _split_2000(texto: str) -> List[str]:
    """Quebra um texto em pedaços de no máximo MAX_CHARS_POR_TEXTO caracteres."""
    if not texto:
        return [""]
    return [
        texto[i:i + MAX_CHARS_POR_TEXTO]
        for i in range(0, len(texto), MAX_CHARS_POR_TEXTO)
    ]


def _bloco_paragrafo(texto: str, falante: Optional[str] = None) -> Dict:
    """
    Cria um bloco de parágrafo, opcionalmente com prefixo do falante em negrito.
    Respeita o limite de 2000 caracteres por item de texto.
    """
    rich_text = []

    if falante:
        rich_text.append({
            "type": "text",
            "text": {"content": f"[{falante}] "},
            "annotations": {"bold": True},
        })

    for pedaco in _split_2000(texto):
        rich_text.append({
            "type": "text",
            "text": {"content": pedaco},
        })

    return {
        "object": "block",
        "type": "paragraph",
        "paragraph": {"rich_text": rich_text},
    }


def _bloco_heading(texto: str) -> Dict:
    """Cria um bloco de título (heading_2)."""
    return {
        "object": "block",
        "type": "heading_2",
        "heading_2": {
            "rich_text": [{"type": "text", "text": {"content": texto}}]
        },
    }


def _bloco_bullet(texto: str) -> Dict:
    """Cria um bloco de item de lista."""
    return {
        "object": "block",
        "type": "bulleted_list_item",
        "bulleted_list_item": {
            "rich_text": [
                {"type": "text", "text": {"content": p}}
                for p in _split_2000(texto)
            ]
        },
    }


def _construir_blocos(
    transcricao_completa: str,
    segmentos_com_falantes: Optional[List[Dict]] = None,
    resumo_falantes: Optional[Dict] = None,
    diarizar: bool = False,
    resumo: Optional[str] = None,
) -> List[Dict]:
    """
    Constrói a lista de blocos do Notion a partir da transcrição.
    Segue a diarização quando disponível.
    """
    blocos = []

    # Cabeçalho com data de geração
    data_str = datetime.now().strftime("%d/%m/%Y %H:%M")
    blocos.append(_bloco_paragrafo(f"Transcrição gerada em {data_str}"))

    # Resumo executivo gerado por IA (se disponível)
    if resumo:
        blocos.append(_bloco_heading("📋 Resumo Executivo (IA)"))
        for linha in resumo.split("\n"):
            linha = linha.strip()
            if not linha:
                continue
            if linha.startswith("## "):
                blocos.append(_bloco_heading(linha[3:]))
            elif linha.startswith("- ") or linha.startswith("• "):
                blocos.append(_bloco_bullet(linha[2:]))
            else:
                blocos.append(_bloco_paragrafo(linha))
        blocos.append(_bloco_heading("📝 Transcrição Completa"))

    blocos.append(_bloco_heading("Transcrição"))

    if diarizar and segmentos_com_falantes:
        # Um parágrafo por fala, com o falante em negrito
        for seg in segmentos_com_falantes:
            texto = (seg.get("texto") or "").strip()
            if not texto:
                continue
            falante = seg.get("falante", "DESCONHECIDO")
            blocos.append(_bloco_paragrafo(texto, falante=falante))
    else:
        # Texto corrido em parágrafos de até 2000 caracteres
        for pedaco in _split_2000(transcricao_completa or ""):
            if pedaco.strip():
                blocos.append(_bloco_paragrafo(pedaco))

    # Resumo de falantes (se houver diarização)
    if diarizar and resumo_falantes:
        blocos.append(_bloco_heading("Resumo de Falantes"))
        for falante, stats in resumo_falantes.items():
            tempo_min = stats.get("tempo_total", 0) / 60
            num_falas = stats.get("num_falas", 0)
            blocos.append(
                _bloco_bullet(f"{falante}: {num_falas} falas ({tempo_min:.1f} min)")
            )

    return blocos


def enviar_transcricao_notion(
    assunto_id: str,
    titulo: str,
    transcricao_completa: str,
    segmentos_com_falantes: Optional[List[Dict]] = None,
    resumo_falantes: Optional[Dict] = None,
    diarizar: bool = False,
    resumo: Optional[str] = None,
) -> str:
    """
    Cria uma página de transcrição dentro da sub-página do assunto.
    Trata os limites de 100 blocos por request e 2000 chars por texto.

    Args:
        assunto_id: ID da sub-página do assunto (de listar_assuntos/criar_assunto)
        titulo: Título da página da transcrição
        transcricao_completa: Texto completo da transcrição
        segmentos_com_falantes: Segmentos com 'falante' e 'texto' (diarização)
        resumo_falantes: Estatísticas por falante
        diarizar: Se deve formatar seguindo a diarização

    Returns:
        URL da página criada no Notion
    """
    client = _get_client()

    blocos = _construir_blocos(
        transcricao_completa,
        segmentos_com_falantes,
        resumo_falantes,
        diarizar,
        resumo,
    )

    # Cria a página com os primeiros 100 blocos
    primeiros = blocos[:MAX_BLOCOS_POR_REQUEST]
    restantes = blocos[MAX_BLOCOS_POR_REQUEST:]

    pagina = client.pages.create(
        parent={"page_id": assunto_id},
        properties={
            "title": [{"text": {"content": titulo}}]
        },
        children=primeiros,
    )
    pagina_id = pagina["id"]

    # Anexa o restante em lotes de 100 blocos
    for i in range(0, len(restantes), MAX_BLOCOS_POR_REQUEST):
        lote = restantes[i:i + MAX_BLOCOS_POR_REQUEST]
        client.blocks.children.append(block_id=pagina_id, children=lote)

    return pagina.get("url", "")
