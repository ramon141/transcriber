import os
import tempfile
from pathlib import Path

import streamlit as st

from ui.helpers import section_header, stepper
from ui.state import wizard_nav


def render() -> None:
    stepper(1)
    section_header(
        "📁 Selecione seu arquivo",
        "Formatos suportados: MP3, WAV, M4A, AAC, FLAC, OGG · MP4, AVI, MOV, MKV e mais.",
    )

    uploaded_file = st.file_uploader(
        "Arraste aqui ou clique para selecionar",
        type=[
            "mp3", "wav", "m4a", "aac", "flac", "ogg", "wma",
            "mp4", "avi", "mov", "mkv", "flv", "wmv", "webm", "m4v", "mpg", "mpeg",
        ],
        help="Tamanho máximo: 500 MB",
    )

    if uploaded_file:
        _mostrar_info(uploaded_file)
    else:
        st.info("👆 Arraste um arquivo de áudio ou vídeo para começar.")
        _mostrar_formatos()


def _mostrar_info(uploaded_file: object) -> None:
    import streamlit as st

    tamanho_mb = uploaded_file.size / (1024 * 1024)  # type: ignore[attr-defined]

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Arquivo", uploaded_file.name)  # type: ignore[attr-defined]
    with col2:
        st.metric("Tamanho", f"{tamanho_mb:.1f} MB")
    with col3:
        st.metric("Formato", Path(uploaded_file.name).suffix.upper())  # type: ignore[attr-defined]

    if tamanho_mb > 500:
        st.error("Arquivo muito grande! O limite é 500 MB. Para arquivos maiores use o CLI.")
        return

    st.divider()
    col_btn, _ = st.columns([1, 4])
    with col_btn:
        if st.button("Avançar →", type="primary", use_container_width=True):
            _salvar_arquivo(uploaded_file)


def _salvar_arquivo(uploaded_file: object) -> None:
    import streamlit as st
    from supabase_integration import computar_hash
    from audio_processor import detectar_tipo_arquivo

    with st.spinner("Preparando arquivo..."):
        old_tmp: str | None = st.session_state.get("tmp_path")
        if old_tmp and os.path.exists(old_tmp):
            try:
                os.unlink(old_tmp)
            except OSError:
                pass

        nome: str = uploaded_file.name  # type: ignore[attr-defined]
        suffix = Path(nome).suffix
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(uploaded_file.getbuffer())  # type: ignore[attr-defined]
            tmp_path = tmp.name

        st.session_state.tmp_path = tmp_path
        st.session_state.arquivo_nome = nome
        st.session_state.arquivo_suffix = suffix
        st.session_state.results = None
        st.session_state.arquivo_hash = computar_hash(
            uploaded_file.getbuffer().tobytes()  # type: ignore[attr-defined]
        )

        tipo = detectar_tipo_arquivo(tmp_path)
        duracao: float | None = _detectar_duracao(tmp_path, tipo)
        st.session_state.audio_duracao = duracao
        st.session_state.corte_inicio = 0.0
        st.session_state.corte_fim = duracao

    wizard_nav(2)


def _detectar_duracao(tmp_path: str, tipo: str) -> float | None:
    try:
        if tipo == "video":
            from moviepy.video.io.VideoFileClip import VideoFileClip
            vc = VideoFileClip(tmp_path)
            duracao = float(vc.duration)
            vc.close()
            return duracao
        else:
            import librosa
            return float(librosa.get_duration(path=tmp_path))
    except Exception:
        return None


def _mostrar_formatos() -> None:
    with st.expander("ℹ️ Formatos suportados"):
        col_a, col_v = st.columns(2)
        with col_a:
            st.markdown("**Áudio**\nMP3 · WAV · M4A · AAC · FLAC · OGG · WMA")
        with col_v:
            st.markdown("**Vídeo**\nMP4 · AVI · MOV · MKV · FLV · WMV · WEBM · M4V · MPG")
