#!/usr/bin/env python3
import streamlit as st

from ui.sidebar import inject_sidebar_css
from ui.state import init_state
from ui.style import inject_css

st.set_page_config(
    page_title="Transcriber",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_css()
inject_sidebar_css()
init_state()

with st.sidebar:
    st.markdown(
        '<div class="sidebar-brand">'
        '<div class="brand-title">🎵 Transcriber</div>'
        '<div class="brand-sub">Transcrição com IA · faster-whisper</div>'
        "</div>",
        unsafe_allow_html=True,
    )

pages: dict[str, list[st.Page]] = {
    "": [
        st.Page(
            "ui/pages/fazer_transcricao.py",
            title="Fazer Transcrição",
            icon="🎙️",
            default=True,
        ),
    ],
    "Transcrições": [
        st.Page("ui/pages/transcricoes_listagem.py", title="Listagem", icon="📋"),
        st.Page("ui/pages/transcricoes_busca.py", title="Busca Avançada", icon="🔍"),
    ],
}

pg = st.navigation(pages, position="sidebar")
pg.run()
