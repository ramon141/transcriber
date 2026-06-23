import os
import tempfile
from pathlib import Path

import streamlit as st

from ui.state import init_state
from ui.style import section_header, stepper

init_state()
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
    tamanho_mb = uploaded_file.size / (1024 * 1024)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Arquivo", uploaded_file.name)
    with col2:
        st.metric("Tamanho", f"{tamanho_mb:.1f} MB")
    with col3:
        st.metric("Formato", Path(uploaded_file.name).suffix.upper())

    if tamanho_mb > 500:
        st.error("Arquivo muito grande! O limite é 500 MB. Para arquivos maiores use o CLI.")
    else:
        st.divider()

        col_btn, col_space = st.columns([1, 4])
        with col_btn:
            avancar = st.button("Avançar →", type="primary", use_container_width=True)

        if avancar:
            with st.spinner("Preparando arquivo..."):
                # Limpa tmp anterior se existir
                old_tmp: str | None = st.session_state.get("tmp_path")
                if old_tmp and os.path.exists(old_tmp):
                    try:
                        os.unlink(old_tmp)
                    except OSError:
                        pass

                suffix = Path(uploaded_file.name).suffix
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                    tmp.write(uploaded_file.getbuffer())
                    tmp_path = tmp.name

                st.session_state.tmp_path = tmp_path
                st.session_state.arquivo_nome = uploaded_file.name
                st.session_state.arquivo_suffix = suffix
                st.session_state.results = None

                # Hash SHA-256 do conteúdo para cache no Supabase
                from supabase_integration import computar_hash
                st.session_state.arquivo_hash = computar_hash(
                    uploaded_file.getbuffer().tobytes()
                )

                # Detecta duração sem processar tudo
                from audio_processor import detectar_tipo_arquivo

                tipo = detectar_tipo_arquivo(tmp_path)
                duracao: float | None = None
                try:
                    if tipo == "video":
                        from moviepy.video.io.VideoFileClip import VideoFileClip

                        vc = VideoFileClip(tmp_path)
                        duracao = float(vc.duration)
                        vc.close()
                    else:
                        import librosa

                        duracao = float(librosa.get_duration(path=tmp_path))
                except Exception:
                    duracao = None

                st.session_state.audio_duracao = duracao
                st.session_state.corte_inicio = 0.0
                st.session_state.corte_fim = duracao

            st.switch_page("ui/pages/2_config.py")
else:
    st.info("👆 Arraste um arquivo de áudio ou vídeo para começar.")

    with st.expander("ℹ️ Formatos suportados"):
        col_a, col_v = st.columns(2)
        with col_a:
            st.markdown("**Áudio**\nMP3 · WAV · M4A · AAC · FLAC · OGG · WMA")
        with col_v:
            st.markdown("**Vídeo**\nMP4 · AVI · MOV · MKV · FLV · WMV · WEBM · M4V · MPG")
