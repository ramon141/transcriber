import streamlit as st

from ui.helpers import section_header, stepper
from ui.state import guard_arquivo, wizard_nav
from ui.types import ResultadoTranscricao
from ui.wizard.step4_exibir import exibir_resultados
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


def render() -> None:
    guard_arquivo()
    stepper(4)
    section_header(
        "▶️ Processamento",
        "Configurações salvas — inicie a transcrição quando estiver pronto.",
    )
    _resumo_config()
    st.divider()

    arquivo_hash: str | None = st.session_state.get("arquivo_hash")
    resultados_existentes: ResultadoTranscricao | None = st.session_state.get("results")

    if resultados_existentes and resultados_existentes.get("sucesso"):
        _secao_resultado_existente(resultados_existentes)
    else:
        if not resultados_existentes and verificar_supabase_configurado() and arquivo_hash:
            _verificar_cache(arquivo_hash)
        _secao_processar()


def _resumo_config() -> None:
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Arquivo", st.session_state.arquivo_nome or "—")
    with col2:
        st.metric("Modelo", st.session_state.cfg_modelo_nome)
    with col3:
        st.metric("Segmentos", f"{st.session_state.cfg_duracao_segmentos} min")
    with col4:
        st.metric("Falantes", "Sim" if st.session_state.cfg_diarizar else "Não")


def _verificar_cache(arquivo_hash: str) -> None:
    try:
        cached = buscar_por_hash(arquivo_hash)
        if not cached:
            return
        st.info(
            f"🗄️ Transcrição em cache — "
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
        pass


def _reconstruir_de_cache(cached: dict) -> ResultadoTranscricao:
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


def _secao_resultado_existente(resultados: ResultadoTranscricao) -> None:
    col_info, col_novo = st.columns([3, 1])
    with col_info:
        st.info("Transcrição já realizada. Veja os resultados abaixo ou processe novamente.")
    with col_novo:
        if st.button("🔄 Novo", use_container_width=True):
            st.session_state.results = None
            st.rerun()
    exibir_resultados(resultados)


def _secao_processar() -> None:
    col_btn, _ = st.columns([1, 3])
    with col_btn:
        processar_btn = st.button(
            "🚀 Iniciar Transcrição",
            type="primary",
            disabled=st.session_state.processing,
            use_container_width=True,
        )

    st.divider()
    col_back, _ = st.columns([1, 5])
    with col_back:
        if st.button("← Voltar", use_container_width=True, key="voltar_antes"):
            wizard_nav(3)

    if processar_btn:
        _executar_processamento()


def _executar_processamento() -> None:
    st.session_state.processing = True
    try:
        _carregar_modelos()
        progress_bar = st.progress(0)
        status_text = st.empty()
        preview_text = st.empty()
        resultados = _transcrever(progress_bar, status_text, preview_text)
        if resultados.get("sucesso"):
            st.session_state.results = resultados
            _salvar_no_supabase(resultados)
            progress_bar.progress(1.0)
            status_text.markdown("**Status:** Concluído! ✅")
            st.rerun()
        else:
            st.error(f"Erro: {resultados.get('erro')}")
            with st.expander("Detalhes do erro"):
                st.code(resultados.get("traceback", ""))
    except Exception as e:
        import traceback as tb
        st.error(f"Erro inesperado: {e}")
        with st.expander("Detalhes"):
            st.code(tb.format_exc())
    finally:
        st.session_state.processing = False


def _carregar_modelos() -> None:
    modelo_nome: str = st.session_state.cfg_modelo_nome

    if st.session_state.ultimo_modelo != modelo_nome:
        st.session_state.modelo_carregado = None
        st.session_state.ultimo_modelo = modelo_nome

    if st.session_state.modelo_carregado is None:
        with st.spinner(f"Carregando modelo '{modelo_nome}'..."):
            st.session_state.modelo_carregado = carregar_modelo_whisper_streamlit(modelo_nome)
            st.success(f"Modelo '{modelo_nome}' carregado!")

    if st.session_state.cfg_diarizar and not st.session_state.diarizacao_carregada:
        _carregar_diarizacao()


def _carregar_diarizacao() -> None:
    with st.spinner("Carregando modelo Pyannote..."):
        try:
            pipeline = carregar_pipeline_diarizacao_streamlit()
            st.session_state.pipeline_diarizacao = pipeline
            st.session_state.diarizacao_carregada = True
            st.success("Modelo de diarização carregado!")
        except Exception as e_diar:
            st.error(f"Erro ao carregar diarização: {e_diar}")
            st.warning("Continuando sem identificação de falantes...")
            st.session_state.cfg_diarizar = False


def _transcrever(progress_bar: object, status_text: object, preview_text: object) -> ResultadoTranscricao:
    def update_progress(p: float) -> None:
        progress_bar.progress(min(p, 1.0))  # type: ignore[attr-defined]

    def update_status(msg: str) -> None:
        status_text.markdown(f"**Status:** {msg}")  # type: ignore[attr-defined]

    def update_preview(texto: str) -> None:
        if texto:
            preview_text.caption(f"_Prévia: {texto[:120]}..._")  # type: ignore[attr-defined]

    callbacks = {
        "progress": update_progress,
        "status": update_status,
        "transcricao_preview": update_preview,
    }

    diarizar: bool = st.session_state.cfg_diarizar
    modo = "com identificação de falantes" if diarizar else "sem identificação de falantes"

    with st.spinner(f"Processando ({modo})..."):
        return processar_audio_streamlit(
            st.session_state.tmp_path,
            st.session_state.modelo_carregado,
            st.session_state.cfg_duracao_segmentos,
            callbacks,
            diarizar=diarizar,
            pipeline_diarizacao=st.session_state.pipeline_diarizacao,
            tempo_inicio=float(st.session_state.corte_inicio or 0.0),
            tempo_fim=st.session_state.corte_fim,
        )


def _salvar_no_supabase(resultados: ResultadoTranscricao) -> None:
    arquivo_hash: str | None = st.session_state.get("arquivo_hash")
    if not verificar_supabase_configurado() or not arquivo_hash:
        return
    try:
        salvar_transcricao(
            hash_arquivo=arquivo_hash,
            nome_arquivo=st.session_state.arquivo_nome or "",
            transcricao_completa=resultados.get("transcricao_completa", ""),
            segmentos_com_falantes=resultados.get("segmentos_com_falantes", []),
            resumo_falantes=resultados.get("resumo_falantes", {}),
            diarizacao_ativada=resultados.get("diarizacao_ativada", False),
            modelo_whisper=st.session_state.cfg_modelo_nome,
            duracao_total=float(resultados.get("duracao_total", 0)),
        )
    except Exception:
        pass
