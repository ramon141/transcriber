from math import ceil

import streamlit as st

from ui.state import guard_arquivo, init_state
from ui.style import fmt_mmss, section_header, stepper

init_state()
guard_arquivo()
stepper(3)
section_header(
    "✂️ Recorte do vídeo",
    "Defina o trecho que será transcrito. Somente este intervalo será processado.",
)

duracao: float | None = st.session_state.get("audio_duracao")

if duracao is None or duracao <= 0:
    st.info(
        "Duração do arquivo não detectada (formato pode não ser suportado). "
        "O arquivo completo será transcrito."
    )
    st.session_state.corte_inicio = 0.0
    st.session_state.corte_fim = None

    st.divider()
    col_back, col_space, col_next = st.columns([1, 4, 1])
    with col_back:
        if st.button("← Voltar", use_container_width=True):
            st.switch_page("ui/pages/2_config.py")
    with col_next:
        if st.button("Avançar →", type="primary", use_container_width=True):
            st.switch_page("ui/pages/4_processar.py")
else:
    duracao_total_fmt = fmt_mmss(duracao)

    col_info1, col_info2 = st.columns(2)
    with col_info1:
        st.metric("Duração total do arquivo", duracao_total_fmt)
    with col_info2:
        duracao_seg = st.session_state.cfg_duracao_segmentos
        n_segs_total = ceil(duracao / (duracao_seg * 60))
        st.metric("Segmentos (arquivo completo)", str(n_segs_total))

    st.divider()

    inicio_atual = int(st.session_state.get("corte_inicio") or 0)
    fim_atual = int(st.session_state.get("corte_fim") or duracao)
    fim_atual = min(fim_atual, int(duracao))

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
    n_segs_sel = ceil(duracao_sel / (duracao_seg * 60)) if duracao_sel > 0 else 0

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Início", fmt_mmss(inicio_sel))
    with col2:
        st.metric("Fim", fmt_mmss(fim_sel))
    with col3:
        st.metric("Duração selecionada", fmt_mmss(duracao_sel))

    if duracao_sel <= 0:
        st.error("O ponto de fim deve ser maior que o início.")
    else:
        st.info(
            f"📦 **{n_segs_sel} segmento(s)** de {duracao_seg} min serão criados para o trecho selecionado."
        )

    st.divider()
    col_back, col_space, col_next = st.columns([1, 4, 1])
    with col_back:
        if st.button("← Voltar", use_container_width=True):
            st.switch_page("ui/pages/2_config.py")
    with col_next:
        if duracao_sel > 0:
            if st.button("Avançar →", type="primary", use_container_width=True):
                st.session_state.corte_inicio = float(inicio_sel)
                st.session_state.corte_fim = float(fim_sel)
                st.switch_page("ui/pages/4_processar.py")
        else:
            st.button("Avançar →", type="primary", use_container_width=True, disabled=True)
