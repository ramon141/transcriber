from datetime import datetime

import streamlit as st

from ui.helpers import section_header, stepper
from ui.state import guard_results, wizard_nav
from notion_integration import (
    criar_assunto,
    enviar_transcricao_notion,
    listar_assuntos,
    verificar_notion_configurado,
)

OPCAO_NOVO = "➕ Criar novo assunto..."


def render() -> None:
    guard_results()
    stepper(5)
    section_header(
        "📝 Enviar para o Notion",
        "Salve a transcrição em uma página do Notion, dentro de uma sub-página de assunto.",
    )

    if not verificar_notion_configurado():
        _instrucoes_configuracao()
        _navegacao()
        return

    _carregar_assuntos()
    assuntos: list[dict] | None = st.session_state.get("notion_assuntos")

    if assuntos is None:
        st.caption("Clique em **Carregar assuntos** para ver as sub-páginas existentes.")
    else:
        _formulario_envio(assuntos)

    _navegacao()


def _instrucoes_configuracao() -> None:
    st.warning(
        "**Integração com o Notion não configurada.**\n\n"
        "1. Acesse [notion.so/my-integrations](https://www.notion.so/my-integrations) e crie uma integração.\n"
        "2. Copie o token (`secret_...`).\n"
        "3. No Notion, abra a página **Reuniões** → `···` → **Connections** → adicione sua integração.\n"
        "4. Copie o ID da página (UUID na URL).\n"
        "5. Adicione ao `.env`:\n"
        "   ```\n"
        "   NOTION_TOKEN=secret_xxx\n"
        "   NOTION_PARENT_ID=id_da_pagina\n"
        "   ```\n"
        "6. Reinicie o Transcriber."
    )


def _carregar_assuntos() -> None:
    if st.button("🔄 Carregar assuntos do Notion"):
        with st.spinner("Buscando sub-páginas..."):
            try:
                st.session_state.notion_assuntos = listar_assuntos()
            except Exception as e:
                st.error(f"Erro ao listar assuntos: {e}")


def _formulario_envio(assuntos: list[dict]) -> None:
    nomes = [a["nome"] for a in assuntos]
    escolha: str = st.selectbox(
        "Sub-página (assunto)",
        options=nomes + [OPCAO_NOVO],
    )

    novo_nome = ""
    if escolha == OPCAO_NOVO:
        novo_nome = st.text_input("Nome do novo assunto").strip()

    titulo_padrao = f"Reunião {datetime.now().strftime('%d/%m/%Y')}"
    titulo: str = st.text_input("Título da transcrição", value=titulo_padrao).strip()

    st.divider()
    _botao_envio(assuntos, escolha, novo_nome, titulo or titulo_padrao)


def _botao_envio(assuntos: list[dict], escolha: str, novo_nome: str, titulo: str) -> None:
    resultados: dict = st.session_state.results
    dados = {
        "titulo": titulo,
        "transcricao_completa": resultados.get("transcricao_completa", ""),
        "segmentos_com_falantes": resultados.get("segmentos_com_falantes", []),
        "resumo_falantes": resultados.get("resumo_falantes", {}),
        "diarizar": resultados.get("diarizacao_ativada", False),
    }

    if escolha == OPCAO_NOVO:
        if not novo_nome:
            st.caption("Digite o nome do novo assunto para continuar.")
            return
        st.warning(f"O assunto **'{novo_nome}'** será criado em Reuniões.")
        if st.button("✅ Confirmar e enviar", type="primary"):
            _enviar_novo(novo_nome, dados)
    else:
        if st.button("📤 Enviar para o Notion", type="primary"):
            _enviar_existente(assuntos, escolha, dados)


def _enviar_novo(novo_nome: str, dados: dict) -> None:
    try:
        with st.spinner(f"Criando '{novo_nome}' e enviando..."):
            assunto_id = criar_assunto(novo_nome)
            url = enviar_transcricao_notion(assunto_id=assunto_id, **dados)
        st.session_state.notion_assuntos = listar_assuntos()
        if url:
            st.success(f"Enviado! [Abrir no Notion]({url})")
        else:
            st.success("Transcrição enviada ao Notion!")
    except Exception as e:
        st.error(f"Erro ao enviar: {e}")


def _enviar_existente(assuntos: list[dict], escolha: str, dados: dict) -> None:
    try:
        assunto_id = next(a["id"] for a in assuntos if a["nome"] == escolha)
        with st.spinner("Enviando..."):
            url = enviar_transcricao_notion(assunto_id=assunto_id, **dados)
        if url:
            st.success(f"Enviado! [Abrir no Notion]({url})")
        else:
            st.success("Transcrição enviada ao Notion!")
    except StopIteration:
        st.error("Assunto não encontrado. Recarregue a lista.")
    except Exception as e:
        st.error(f"Erro ao enviar: {e}")


def _navegacao() -> None:
    st.divider()
    col_back, _ = st.columns([1, 5])
    with col_back:
        if st.button("← Voltar", use_container_width=True):
            wizard_nav(4)
