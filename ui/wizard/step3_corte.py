from math import ceil

import streamlit as st

from ui.helpers import fmt_mmss, section_header, stepper
from ui.state import guard_arquivo, wizard_nav


def render() -> None:
    guard_arquivo()
    stepper(3)
    section_header(
        "✂️ Recorte do áudio",
        "Defina o trecho que será transcrito. Somente este intervalo será processado.",
    )

    duracao: float | None = st.session_state.get("audio_duracao")

    if not duracao or duracao <= 0:
        _sem_duracao()
    else:
        _com_slider(duracao)


def _sem_duracao() -> None:
    st.info(
        "Duração não detectada (formato pode não ser suportado). "
        "O arquivo completo será transcrito."
    )
    st.session_state.corte_inicio = 0.0
    st.session_state.corte_fim = None

    st.divider()
    col_back, _, col_next = st.columns([1, 4, 1])
    with col_back:
        if st.button("← Voltar", use_container_width=True):
            wizard_nav(2)
    with col_next:
        if st.button("Avançar →", type="primary", use_container_width=True):
            wizard_nav(4)


def _com_slider(duracao: float) -> None:
    col_info1, col_info2 = st.columns(2)
    with col_info1:
        st.metric("Duração total do arquivo", fmt_mmss(duracao))
    with col_info2:
        duracao_seg: int = st.session_state.cfg_duracao_segmentos
        n_total = ceil(duracao / (duracao_seg * 60))
        st.metric("Segmentos (arquivo completo)", str(n_total))

    st.divider()

    inicio_atual = int(st.session_state.get("corte_inicio") or 0)
    fim_atual = min(int(st.session_state.get("corte_fim") or duracao), int(duracao))

    valores = st.slider(
        "Selecione o intervalo (início → fim)",
        min_value=0,
        max_value=int(duracao),
        value=(inicio_atual, fim_atual),
        step=1,
        format="%d s",
        help="Mova as alças para definir o trecho que será transcrito.",
    )

    inicio_sel, fim_sel = valores
    duracao_sel = fim_sel - inicio_sel

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Início", fmt_mmss(inicio_sel))
    with col2:
        st.metric("Fim", fmt_mmss(fim_sel))
    with col3:
        st.metric("Duração selecionada", fmt_mmss(duracao_sel))

    _navegacao_corte(inicio_sel, fim_sel, duracao_sel)


def _navegacao_corte(inicio_sel: int, fim_sel: int, duracao_sel: int) -> None:
    duracao_seg: int = st.session_state.cfg_duracao_segmentos

    if duracao_sel <= 0:
        st.error("O ponto de fim deve ser maior que o início.")
    else:
        n_segs = ceil(duracao_sel / (duracao_seg * 60))
        st.info(f"📦 **{n_segs} segmento(s)** de {duracao_seg} min serão criados.")

    st.divider()
    col_back, _, col_next = st.columns([1, 4, 1])

    with col_back:
        if st.button("← Voltar", use_container_width=True):
            wizard_nav(2)

    with col_next:
        if duracao_sel > 0:
            if st.button("Avançar →", type="primary", use_container_width=True):
                st.session_state.corte_inicio = float(inicio_sel)
                st.session_state.corte_fim = float(fim_sel)
                wizard_nav(4)
        else:
            st.button("Avançar →", type="primary", use_container_width=True, disabled=True)
