import io
import os
import zipfile
from pathlib import Path

import streamlit as st

from ui.state import guard_arquivo, init_state
from ui.style import obter_cor_falante, section_header, stepper
from audio_processor import (
    carregar_modelo_whisper_streamlit,
    carregar_pipeline_diarizacao_streamlit,
    processar_audio_streamlit,
)
from supabase_integration import (
    buscar_por_hash,
    salvar_transcricao,
    verificar_supabase_configurado,
)

init_state()
guard_arquivo()
stepper(4)
section_header("▶️ Processamento", "Configurações salvas — inicie a transcrição quando estiver pronto.")

# ── Resumo das configurações ──────────────────────────────────────────────────
arquivo_nome: str = st.session_state.arquivo_nome or "—"
modelo_nome: str = st.session_state.cfg_modelo_nome
duracao_segmentos: int = st.session_state.cfg_duracao_segmentos
diarizar: bool = st.session_state.cfg_diarizar
tempo_inicio: float = st.session_state.corte_inicio or 0.0
tempo_fim: float | None = st.session_state.corte_fim

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Arquivo", arquivo_nome)
with col2:
    st.metric("Modelo", modelo_nome)
with col3:
    st.metric("Segmentos", f"{duracao_segmentos} min")
with col4:
    st.metric("Falantes", "Sim" if diarizar else "Não")

st.divider()


def _criar_zip(pasta_saida: str) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        pasta = Path(pasta_saida)
        for arq in pasta.rglob("*"):
            if arq.is_file():
                zf.write(arq, arq.relative_to(pasta.parent))
    buf.seek(0)
    return buf.getvalue()


def _exibir_resultados(resultados: dict) -> None:
    diarizacao_ativada: bool = resultados.get("diarizacao_ativada", False)
    resumo_falantes: dict = resultados.get("resumo_falantes", {})

    st.success("✅ Transcrição concluída!")

    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
    with m_col1:
        st.metric("Segmentos", len(resultados.get("segmentos", [])))
    with m_col2:
        st.metric("Duração", f"{resultados.get('duracao_total', 0):.1f} min")
    with m_col3:
        st.metric("Falantes", len(resumo_falantes) if diarizacao_ativada else "—")
    with m_col4:
        pasta_nome = Path(resultados["pasta_saida"]).name if resultados.get("pasta_saida") else "—"
        st.metric("Pasta", pasta_nome)

    # ── Tabs ──────────────────────────────────────────────────────────────────
    if diarizacao_ativada:
        tab1, tab2, tab3, tab4 = st.tabs(
            ["📄 Completa", "👥 Por Falante", "📁 Segmentos", "⬇️ Downloads"]
        )
    else:
        tab1, tab2, tab3 = st.tabs(["📄 Completa", "📁 Segmentos", "⬇️ Downloads"])

    with tab1:
        if diarizacao_ativada:
            segs_falantes: list[dict] = resultados.get("segmentos_com_falantes", [])
            if segs_falantes:
                for seg in segs_falantes:
                    falante = seg.get("falante", "DESCONHECIDO")
                    cor = obter_cor_falante(falante)
                    texto = seg.get("texto", "")
                    st.markdown(
                        f'<div class="speaker-bubble">'
                        f'<span style="color:{cor};font-weight:700;">[{falante}]</span> {texto}'
                        f"</div>",
                        unsafe_allow_html=True,
                    )
            else:
                st.text_area("Texto transcrito", value=resultados.get("transcricao_completa", ""), height=400)
        else:
            st.text_area(
                "Texto transcrito",
                value=resultados.get("transcricao_completa", ""),
                height=400,
                help="Selecione tudo (Ctrl+A) e copie (Ctrl+C)",
            )

    if diarizacao_ativada:
        with tab2:
            if resumo_falantes:
                for falante, stats in resumo_falantes.items():
                    cor = obter_cor_falante(falante)
                    tempo_min = stats.get("tempo_total", 0) / 60
                    with st.expander(f"👤 {falante} — {stats.get('num_falas', 0)} falas ({tempo_min:.1f} min)"):
                        st.markdown(
                            f'<div style="border-left:4px solid {cor};padding-left:12px;">',
                            unsafe_allow_html=True,
                        )
                        for texto in stats.get("textos", []):
                            st.write(f"• {texto}")
                        st.markdown("</div>", unsafe_allow_html=True)
            else:
                st.info("Nenhum falante identificado.")
        tab_segs = tab3
        tab_dl = tab4
    else:
        tab_segs = tab2
        tab_dl = tab3

    with tab_segs:
        for seg in resultados.get("segmentos", []):
            with st.expander(f"🎵 Segmento {seg['numero']:02d} ({seg['duracao']:.1f}s)"):
                st.write(seg["texto"])

    with tab_dl:
        arq_completo: str = resultados.get("arquivo_completo", "")
        arq_detalhado: str = resultados.get("arquivo_detalhado", "")

        if os.path.exists(arq_completo):
            with open(arq_completo, "r", encoding="utf-8") as f:
                conteudo_completo = f.read()
            label = "📄 Transcrição Completa"
            if diarizacao_ativada:
                label += " (com falantes)"
            label += " (.txt)"
            st.download_button(label, data=conteudo_completo, file_name=Path(arq_completo).name, mime="text/plain")

        if os.path.exists(arq_detalhado):
            with open(arq_detalhado, "r", encoding="utf-8") as f:
                conteudo_detalhado = f.read()
            st.download_button(
                "📋 Transcrição Detalhada (.txt)",
                data=conteudo_detalhado,
                file_name=Path(arq_detalhado).name,
                mime="text/plain",
            )

        st.divider()
        pasta_saida_dl = resultados.get("pasta_saida", "")
        if pasta_saida_dl and os.path.exists(pasta_saida_dl):
            if st.button("📦 Criar ZIP com tudo", type="primary"):
                with st.spinner("Criando ZIP..."):
                    zip_data = _criar_zip(pasta_saida_dl)
                st.download_button(
                    "⬇️ Baixar tudo (áudios + transcrições)",
                    data=zip_data,
                    file_name=f"{Path(pasta_saida_dl).name}.zip",
                    mime="application/zip",
                )
        else:
            st.caption("📦 ZIP não disponível para resultados carregados do cache.")

    # ── Botão Notion ──────────────────────────────────────────────────────────
    st.divider()
    col_back2, col_space2, col_notion = st.columns([1, 4, 1])
    with col_back2:
        if st.button("← Voltar", use_container_width=True, key="voltar_apos_resultado"):
            st.switch_page("ui/pages/3_corte.py")
    with col_notion:
        if st.button("📝 Enviar ao Notion →", type="primary", use_container_width=True):
            st.switch_page("ui/pages/5_notion.py")


# ── Cache Supabase ────────────────────────────────────────────────────────────
arquivo_hash: str | None = st.session_state.get("arquivo_hash")


def _reconstruir_de_cache(cached: dict) -> dict:
    return {
        "sucesso": True,
        "transcricao_completa": cached.get("transcricao_completa", ""),
        "segmentos": [],
        "segmentos_com_falantes": cached.get("segmentos_com_falantes") or [],
        "resumo_falantes": cached.get("resumo_falantes") or {},
        "diarizacao_ativada": cached.get("diarizacao_ativada", False),
        "arquivo_completo": "",
        "arquivo_detalhado": "",
        "pasta_saida": "",
        "duracao_total": cached.get("duracao_total", 0),
        "_from_cache": True,
    }


# ── Área de processamento ─────────────────────────────────────────────────────
resultados_existentes: dict | None = st.session_state.get("results")

# Verifica cache antes de exibir botão de processar
if not resultados_existentes and verificar_supabase_configurado() and arquivo_hash:
    try:
        cached = buscar_por_hash(arquivo_hash)
        if cached:
            st.info(
                f"🗄️ Transcrição em cache encontrada no Supabase — "
                f"arquivo: **{cached.get('nome_arquivo', '?')}** · "
                f"modelo: **{cached.get('modelo_whisper', '?')}**"
            )
            col_use, _ = st.columns([1, 3])
            with col_use:
                if st.button("✅ Usar cache", type="primary", use_container_width=True):
                    st.session_state.results = _reconstruir_de_cache(cached)
                    st.rerun()
            st.divider()
    except Exception:
        pass  # ignora falha de conexão sem bloquear o fluxo

if resultados_existentes and resultados_existentes.get("sucesso"):
    col_processar, col_novo = st.columns([3, 1])
    with col_processar:
        st.info("Transcrição já realizada. Veja os resultados abaixo ou processe novamente.")
    with col_novo:
        if st.button("🔄 Novo", use_container_width=True):
            st.session_state.results = None
            st.rerun()
    _exibir_resultados(resultados_existentes)
else:
    col_btn, col_sp = st.columns([1, 3])
    with col_btn:
        processar_btn = st.button(
            "🚀 Iniciar Transcrição",
            type="primary",
            disabled=st.session_state.processing,
            use_container_width=True,
        )

    st.divider()
    col_back3, _ = st.columns([1, 5])
    with col_back3:
        if st.button("← Voltar", use_container_width=True, key="voltar_antes"):
            st.switch_page("ui/pages/3_corte.py")

    if processar_btn:
        st.session_state.processing = True
        tmp_path: str = st.session_state.tmp_path

        try:
            # Carrega modelo Whisper
            if st.session_state.ultimo_modelo != modelo_nome:
                st.session_state.modelo_carregado = None
                st.session_state.ultimo_modelo = modelo_nome

            if st.session_state.modelo_carregado is None:
                with st.spinner(f"Carregando modelo '{modelo_nome}'..."):
                    modelo_whisper = carregar_modelo_whisper_streamlit(modelo_nome)
                    st.session_state.modelo_carregado = modelo_whisper
                    st.success(f"Modelo '{modelo_nome}' carregado!")
            else:
                modelo_whisper = st.session_state.modelo_carregado

            # Carrega pipeline de diarização
            pipeline_diarizacao = None
            if diarizar:
                if not st.session_state.diarizacao_carregada:
                    with st.spinner("Carregando modelo de diarização Pyannote..."):
                        try:
                            pipeline_diarizacao = carregar_pipeline_diarizacao_streamlit()
                            st.session_state.pipeline_diarizacao = pipeline_diarizacao
                            st.session_state.diarizacao_carregada = True
                            st.success("Modelo de diarização carregado!")
                        except Exception as e_diar:
                            st.error(f"Erro ao carregar diarização: {e_diar}")
                            st.warning("Continuando sem identificação de falantes...")
                            diarizar = False
                else:
                    pipeline_diarizacao = st.session_state.pipeline_diarizacao

            # Progresso
            progress_bar = st.progress(0)
            status_text = st.empty()
            preview_text = st.empty()

            def update_progress(p: float) -> None:
                progress_bar.progress(min(p, 1.0))

            def update_status(msg: str) -> None:
                status_text.markdown(f"**Status:** {msg}")

            def update_preview(texto: str) -> None:
                if texto:
                    preview_text.caption(f"_Prévia: {texto[:120]}..._")

            callbacks = {
                "progress": update_progress,
                "status": update_status,
                "transcricao_preview": update_preview,
            }

            modo = "com identificação de falantes" if diarizar else "sem identificação de falantes"
            with st.spinner(f"Processando arquivo ({modo})..."):
                resultados = processar_audio_streamlit(
                    tmp_path,
                    modelo_whisper,
                    duracao_segmentos,
                    callbacks,
                    diarizar=diarizar,
                    pipeline_diarizacao=pipeline_diarizacao,
                    tempo_inicio=tempo_inicio,
                    tempo_fim=tempo_fim,
                )

            if resultados.get("sucesso"):
                st.session_state.results = resultados
                # Auto-save no Supabase (silencioso — não falha o fluxo)
                if verificar_supabase_configurado() and arquivo_hash:
                    try:
                        salvar_transcricao(
                            hash_arquivo=arquivo_hash,
                            nome_arquivo=st.session_state.arquivo_nome or "",
                            transcricao_completa=resultados.get("transcricao_completa", ""),
                            segmentos_com_falantes=resultados.get("segmentos_com_falantes", []),
                            resumo_falantes=resultados.get("resumo_falantes", {}),
                            diarizacao_ativada=resultados.get("diarizacao_ativada", False),
                            modelo_whisper=modelo_nome,
                            duracao_total=float(resultados.get("duracao_total", 0)),
                        )
                    except Exception:
                        pass
                progress_bar.progress(1.0)
                status_text.markdown("**Status:** Concluído! ✅")
                st.rerun()
            else:
                st.error(f"Erro: {resultados.get('erro')}")
                with st.expander("Detalhes do erro"):
                    st.code(resultados.get("traceback", ""))

        except Exception as e:
            import traceback

            st.error(f"Erro inesperado: {e}")
            with st.expander("Detalhes"):
                st.code(traceback.format_exc())
        finally:
            st.session_state.processing = False
