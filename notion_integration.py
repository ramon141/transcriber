"""
Integração com o Notion para o Transcriber.

Estrutura criada:
    Pai (NOTION_PARENT_ID)
    └── Assunto (sub-página escolhida pelo usuário)
        └── Reunião DD/MM/YYYY
            ├── 📝 Transcrição Completa  [toggle]
            ├── 📋 Resumo (IA)           [toggle — opcional]
            └── ✅ Atividades             [toggle — opcional]
"""

import re
from typing import Dict, List, Optional

from config_store import ChaveIntegracao, obter_integracao
from notion_blocos import construir_blocos

MAX_BLOCOS_POR_REQUEST = 100
TAMANHO_ID_NOTION = 32


def extrair_notion_id(valor: str) -> str:
    """
    Aceita o ID puro ou um link da página do Notion e devolve o ID
    de 32 caracteres hexadecimais (sem hifens).

    Ex.: https://.../Reuni-o-...-38858ce2621081aba8cbf52731fc6eb7
         → 38858ce2621081aba8cbf52731fc6eb7
    """
    texto = valor.strip()

    sequencias = re.findall(r"[0-9a-fA-F]{32}", texto)
    if sequencias:
        return sequencias[-1].lower()

    somente_hex = re.sub(r"[^0-9a-fA-F]", "", texto)
    if len(somente_hex) >= TAMANHO_ID_NOTION:
        return somente_hex[-TAMANHO_ID_NOTION:].lower()

    return texto


def obter_token_notion() -> Optional[str]:
    return obter_integracao(ChaveIntegracao.NOTION_TOKEN)


def obter_parent_id() -> Optional[str]:
    valor = obter_integracao(ChaveIntegracao.NOTION_PARENT_ID)
    if not valor:
        return valor

    return extrair_notion_id(valor)


def verificar_notion_configurado() -> bool:
    return bool(obter_token_notion()) and bool(obter_parent_id())


def validar_token_notion(token: str) -> Optional[str]:
    """Valida o token chamando a API do Notion. None = válido."""
    try:
        from notion_client import Client

        Client(auth=token).users.me()
        return None
    except Exception:
        return "Token do Notion inválido."


def validar_parent_notion(token: str, parent_id: str) -> Optional[str]:
    """Verifica se a página pai existe e está acessível. None = ok."""
    try:
        from notion_client import Client

        pid = extrair_notion_id(parent_id)
        Client(auth=token).blocks.retrieve(block_id=pid)
        return None
    except Exception:
        return (
            "Página do Notion não encontrada ou sem acesso. "
            "Compartilhe a página com a integração."
        )


def _get_client():
    try:
        from notion_client import Client
    except ImportError:
        raise ImportError("notion-client não instalado. Execute: pip install notion-client")

    token = obter_token_notion()
    if not token:
        raise ValueError("NOTION_TOKEN não configurado no .env")

    return Client(auth=token)


def listar_assuntos(parent_id: Optional[str] = None) -> List[Dict]:
    client = _get_client()
    pid = parent_id or obter_parent_id()
    if not pid:
        raise ValueError("NOTION_PARENT_ID não configurado no .env")

    assuntos: List[Dict] = []
    cursor = None

    while True:
        params: Dict = {"block_id": pid, "page_size": 100}
        if cursor:
            params["start_cursor"] = cursor

        resposta = client.blocks.children.list(**params)

        for bloco in resposta.get("results", []):
            if bloco.get("type") == "child_page":
                assuntos.append({"nome": bloco["child_page"]["title"], "id": bloco["id"]})

        if resposta.get("has_more"):
            cursor = resposta.get("next_cursor")
        else:
            break

    return assuntos


def criar_assunto(nome: str, parent_id: Optional[str] = None) -> str:
    client = _get_client()
    pid = parent_id or obter_parent_id()
    if not pid:
        raise ValueError("NOTION_PARENT_ID não configurado no .env")

    pagina = client.pages.create(
        parent={"page_id": pid},
        properties={"title": [{"text": {"content": nome}}]},
    )
    return pagina["id"]


def enviar_transcricao_notion(
    assunto_id: str,
    titulo: str,
    transcricao_completa: str,
    segmentos_com_falantes: Optional[List[Dict]] = None,
    resumo_falantes: Optional[Dict] = None,
    diarizar: bool = False,
    resumo: Optional[str] = None,
    atividades: Optional[Dict[str, List[str]]] = None,
) -> str:
    client = _get_client()

    blocos = construir_blocos(
        transcricao_completa=transcricao_completa,
        segmentos_com_falantes=segmentos_com_falantes,
        diarizar=diarizar,
        resumo=resumo,
        atividades=atividades,
    )

    primeiros = blocos[:MAX_BLOCOS_POR_REQUEST]
    restantes = blocos[MAX_BLOCOS_POR_REQUEST:]

    pagina = client.pages.create(
        parent={"page_id": assunto_id},
        properties={"title": [{"text": {"content": titulo}}]},
        children=primeiros,
    )
    pagina_id = pagina["id"]

    for i in range(0, len(restantes), MAX_BLOCOS_POR_REQUEST):
        lote = restantes[i:i + MAX_BLOCOS_POR_REQUEST]
        client.blocks.children.append(block_id=pagina_id, children=lote)

    return pagina.get("url", "")
