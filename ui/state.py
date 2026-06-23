import streamlit as st


def init_state() -> None:
    defaults: dict[str, object] = {
        "tmp_path": None,
        "arquivo_nome": None,
        "arquivo_suffix": None,
        "arquivo_hash": None,
        "audio_duracao": None,
        "cfg_modelo_nome": "base",
        "cfg_duracao_segmentos": 4,
        "cfg_diarizar": True,
        "corte_inicio": 0.0,
        "corte_fim": None,
        "processing": False,
        "results": None,
        "modelo_carregado": None,
        "ultimo_modelo": None,
        "pipeline_diarizacao": None,
        "diarizacao_carregada": False,
        "notion_assuntos": None,
        "wizard_step": 1,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


def wizard_nav(step: int) -> None:
    st.session_state.wizard_step = step
    st.rerun()


def guard_arquivo() -> None:
    if not st.session_state.get("tmp_path"):
        st.warning("Nenhum arquivo carregado. Volte à primeira etapa.")
        if st.button("← Ir para Upload"):
            wizard_nav(1)
        st.stop()


def guard_results() -> None:
    if not st.session_state.get("results"):
        st.warning("Nenhuma transcrição disponível. Processe um arquivo primeiro.")
        if st.button("← Ir para Processamento"):
            wizard_nav(4)
        st.stop()
