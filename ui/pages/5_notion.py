from datetime import datetime

import streamlit as st

from ui.state import guard_results, init_state
from ui.style import section_header, stepper
from notion_integration import (
    criar_assunto,
    enviar_transcricao_notion,
    listar_assuntos,
    verificar_notion_configurado,
)

init_state()
guard_results()
stepper(5)
section_header(
    "📝 Enviar para o Notion",
    "Salve a transcrição em uma página do Notion, dentro de uma sub-página de assunto.",
)

if not verificar_notion_configurado():
    st.warning(
        "**Integração com o Notion não configurada.**\n\n"
        "1. Acesse [notion.so/my-integrations](https://www.notion.so/my-integrations) e crie uma integração.\n"
        "2. Copie o token (`secret_...`).\n"
        "3. No Notion, abra a página **Reuniões** → `···` → **Connections** → adicione sua integração.\n"
        "4. Copie o ID da página (o UUID na URL).\n"
        "5. No arquivo `.env` da raiz do projeto, adicione:\n"
        "   ```\n"
        "   NOTION_TOKEN=secret_xxx\n"
        "   NOTION_PARENT_ID=id_da_pagina_reunioes\n"
        "   ```\n"
        "6. Reinicie o Transcriber."
    )
else:
    # ── Carregar assuntos ─────────────────────────────────────────────────────
    if st.button("🔄 Carregar assuntos do Notion"):
        with st.spinner("Buscando sub-páginas..."):
            try:
                st.session_state.notion_assuntos = listar_assuntos()
            except Exception as e:
                st.error(f"Erro ao listar assuntos: {e}")

    assuntos: list[dict] | None = st.session_state.get("notion_assuntos")

    if assuntos is None:
        st.caption("Clique em **Carregar assuntos** para ver as sub-páginas existentes.")
    else:
        OPCAO_NOVO = "➕ Criar novo assunto..."
        nomes = [a["nome"] for a in assuntos]

        escolha: str = st.selectbox(
            "Sub-página (assunto)",
            options=nomes + [OPCAO_NOVO],
            help="Sub-páginas da página Reuniões no Notion.",
        )

        novo_nome = ""
        if escolha == OPCAO_NOVO:
            novo_nome = st.text_input("Nome do novo assunto").strip()

        titulo_padrao = f"Reunião {datetime.now().strftime('%d/%m/%Y')}"
        titulo: str = st.text_input("Título da transcrição", value=titulo_padrao).strip()

        st.divider()

        resultados: dict = st.session_state.results
        diarizacao_ativada: bool = resultados.get("diarizacao_ativada", False)

        dados_envio = {
            "titulo": titulo or titulo_padrao,
            "transcricao_completa": resultados.get("transcricao_completa", ""),
            "segmentos_com_falantes": resultados.get("segmentos_com_falantes", []),
            "resumo_falantes": resultados.get("resumo_falantes", {}),
            "diarizar": diarizacao_ativada,
        }

        if escolha == OPCAO_NOVO:
            if not novo_nome:
                st.caption("Digite o nome do novo assunto para continuar.")
            else:
                st.warning(f"O assunto **'{novo_nome}'** será criado em Reuniões.")
                if st.button("✅ Confirmar e enviar", type="primary"):
                    try:
                        with st.spinner(f"Criando '{novo_nome}' e enviando..."):
                            assunto_id = criar_assunto(novo_nome)
                            url = enviar_transcricao_notion(assunto_id=assunto_id, **dados_envio)
                        st.session_state.notion_assuntos = listar_assuntos()
                        if url:
                            st.success(f"Enviado! [Abrir no Notion]({url})")
                        else:
                            st.success("Transcrição enviada ao Notion!")
                    except Exception as e:
                        st.error(f"Erro ao enviar: {e}")
        else:
            if st.button("📤 Enviar para o Notion", type="primary"):
                try:
                    assunto_id = next(a["id"] for a in assuntos if a["nome"] == escolha)
                    with st.spinner("Enviando..."):
                        url = enviar_transcricao_notion(assunto_id=assunto_id, **dados_envio)
                    if url:
                        st.success(f"Enviado! [Abrir no Notion]({url})")
                    else:
                        st.success("Transcrição enviada ao Notion!")
                except StopIteration:
                    st.error("Assunto não encontrado. Recarregue a lista.")
                except Exception as e:
                    st.error(f"Erro ao enviar: {e}")

# ── Navegação ─────────────────────────────────────────────────────────────────
st.divider()
col_back, _ = st.columns([1, 5])
with col_back:
    if st.button("← Voltar", use_container_width=True):
        st.switch_page("ui/pages/4_processar.py")
