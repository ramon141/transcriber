#!/usr/bin/env python3
"""
Interface Web Streamlit para Split Audio.
Processador e transcritor de áudio com interface intuitiva.
"""

import os
import io
import tempfile
import zipfile
from pathlib import Path
import streamlit as st

# Importa funções do processador
from audio_processor import (
    carregar_modelo_whisper_streamlit,
    processar_audio_streamlit,
    obter_info_modelo
)


def configurar_pagina():
    """Configura a página do Streamlit."""
    st.set_page_config(
        page_title="Split Audio - Processador de Áudio",
        page_icon="🎵",
        layout="wide",
        initial_sidebar_state="expanded"
    )


def inicializar_session_state():
    """Inicializa o estado da sessão."""
    if 'processing' not in st.session_state:
        st.session_state.processing = False
    if 'results' not in st.session_state:
        st.session_state.results = None
    if 'modelo_carregado' not in st.session_state:
        st.session_state.modelo_carregado = None
    if 'ultimo_modelo' not in st.session_state:
        st.session_state.ultimo_modelo = None


def mostrar_info_arquivo(uploaded_file):
    """Mostra informações sobre o arquivo carregado."""
    tamanho_mb = uploaded_file.size / (1024 * 1024)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Nome do Arquivo", uploaded_file.name)
    with col2:
        st.metric("Tamanho", f"{tamanho_mb:.1f} MB")
    with col3:
        extensao = Path(uploaded_file.name).suffix.upper()
        st.metric("Formato", extensao)


def criar_zip_resultados(pasta_saida: str):
    """
    Cria um arquivo ZIP com todos os resultados.

    Args:
        pasta_saida: Caminho da pasta com os resultados

    Returns:
        Bytes do arquivo ZIP
    """
    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
        pasta_path = Path(pasta_saida)
        for arquivo in pasta_path.rglob('*'):
            if arquivo.is_file():
                zipf.write(arquivo, arquivo.relative_to(pasta_path.parent))

    zip_buffer.seek(0)
    return zip_buffer.getvalue()


def sidebar_configuracoes():
    """
    Renderiza a barra lateral com configurações.

    Returns:
        Tuple com (modelo_nome, duracao_segmentos)
    """
    with st.sidebar:
        st.title("⚙️ Configurações")

        # Configurações de transcrição
        st.subheader("Modelo de Transcrição")

        modelo_nome = st.select_slider(
            "Modelo Whisper",
            options=['tiny', 'base', 'small', 'medium', 'large'],
            value='base',
            help="Escolha o modelo de IA para transcrição"
        )

        # Mostra informações do modelo
        info = obter_info_modelo(modelo_nome)
        st.info(f"""
**{info['descricao']}**

**Qualidade:** {info['qualidade']}
**Velocidade:** {info['velocidade']}
**Tempo estimado:** {info['tempo_estimado']}
        """)

        # Duração dos segmentos
        st.subheader("Configurações de Divisão")
        duracao_segmentos = st.number_input(
            "Duração do Segmento (minutos)",
            min_value=1,
            max_value=10,
            value=4,
            help="Quanto tempo terá cada segmento de áudio"
        )

        # Informações adicionais
        st.divider()
        st.caption("💡 **Dica:** Para arquivos grandes, use segmentos menores e o modelo 'tiny' para processar mais rápido.")

        return modelo_nome, duracao_segmentos


def exibir_resultados_transcricao_completa(resultados: dict):
    """Exibe resultados da transcrição completa."""
    st.success("Transcrição completa finalizada!")

    # Métricas
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Segmentos Processados", len(resultados['segmentos']))
    with col2:
        st.metric("Duração Total", f"{resultados['duracao_total']:.1f} min")
    with col3:
        pasta_nome = Path(resultados['pasta_saida']).name
        st.metric("Pasta de Saída", pasta_nome)

    # Tabs para diferentes visualizações
    tab1, tab2, tab3 = st.tabs(["📄 Transcrição Completa", "📁 Segmentos", "⬇️ Downloads"])

    with tab1:
        st.subheader("Transcrição Completa")
        st.text_area(
            "Texto transcrito:",
            value=resultados.get('transcricao_completa', ''),
            height=400,
            help="Copie o texto transcrito daqui"
        )

        # Botão para copiar
        if st.button("📋 Copiar para Área de Transferência"):
            st.info("Use Ctrl+A e Ctrl+C na área de texto acima para copiar")

    with tab2:
        st.subheader("Transcrições por Segmento")

        for seg in resultados.get('segmentos', []):
            with st.expander(f"🎵 Segmento {seg['numero']:02d} ({seg['duracao']:.1f}s)"):
                st.write(seg['texto'])

                # Botão para copiar segmento individual
                st.caption(f"**Timestamp:** {seg.get('timestamp', '')}")

    with tab3:
        st.subheader("Downloads")

        st.write("**Arquivos de Transcrição:**")

        # Lê e oferece download dos arquivos de transcrição
        if os.path.exists(resultados.get('arquivo_completo', '')):
            with open(resultados['arquivo_completo'], 'r', encoding='utf-8') as f:
                conteudo_completo = f.read()

            st.download_button(
                label="📄 Transcrição Completa (.txt)",
                data=conteudo_completo,
                file_name=Path(resultados['arquivo_completo']).name,
                mime="text/plain"
            )

        if os.path.exists(resultados.get('arquivo_detalhado', '')):
            with open(resultados['arquivo_detalhado'], 'r', encoding='utf-8') as f:
                conteudo_detalhado = f.read()

            st.download_button(
                label="📋 Transcrição Detalhada (.txt)",
                data=conteudo_detalhado,
                file_name=Path(resultados['arquivo_detalhado']).name,
                mime="text/plain"
            )

        st.divider()

        st.write("**Pacote Completo:**")
        if st.button("📦 Criar ZIP com Tudo", type="primary"):
            with st.spinner("Criando arquivo ZIP..."):
                zip_data = criar_zip_resultados(resultados['pasta_saida'])
                st.download_button(
                    label="⬇️ Baixar Tudo (Áudios + Transcrições)",
                    data=zip_data,
                    file_name=f"{Path(resultados['pasta_saida']).name}.zip",
                    mime="application/zip"
                )


def main():
    """Função principal da aplicação."""
    configurar_pagina()
    inicializar_session_state()

    # Título principal
    st.title("🎵 Split Audio - Processador e Transcritor de Áudio/Vídeo")
    st.markdown("""
    Converte vídeos para áudio, divide em segmentos e transcreve automaticamente com IA (Whisper).

    **Áudio:** MP3, WAV, M4A, AAC, FLAC, OGG, WMA
    **Vídeo:** MP4, AVI, MOV, MKV, FLV, WMV, WEBM
    """)

    # Configurações na sidebar
    modelo_nome, duracao_segmentos = sidebar_configuracoes()

    # Upload de arquivo
    st.divider()
    st.subheader("1️⃣ Selecione o Arquivo (Áudio ou Vídeo)")

    uploaded_file = st.file_uploader(
        "Arraste seu arquivo aqui ou clique para selecionar",
        type=['mp3', 'wav', 'm4a', 'aac', 'flac', 'ogg', 'wma',  # Áudio
              'mp4', 'avi', 'mov', 'mkv', 'flv', 'wmv', 'webm', 'm4v', 'mpg', 'mpeg'],  # Vídeo
        help="Tamanho máximo: 500MB"
    )

    # Se arquivo foi carregado
    if uploaded_file is not None:
        # Mostra informações do arquivo
        mostrar_info_arquivo(uploaded_file)

        # Validação de tamanho
        tamanho_mb = uploaded_file.size / (1024 * 1024)
        if tamanho_mb > 500:
            st.error("⚠️ Arquivo muito grande! O limite é 500MB. Para arquivos maiores, use o CLI.")
            return

        st.divider()
        st.subheader("2️⃣ Processar Áudio")

        # Botão de processar
        col1, col2 = st.columns([3, 1])

        with col1:
            processar_btn = st.button(
                "🚀 Processar Áudio",
                type="primary",
                disabled=st.session_state.processing,
                use_container_width=True
            )

        with col2:
            if st.session_state.results is not None:
                if st.button("🗑️ Limpar Resultados"):
                    st.session_state.results = None
                    st.rerun()

        # Processamento
        if processar_btn:
            st.session_state.processing = True

            # Salva arquivo temporário
            with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_file.name).suffix) as tmp_file:
                tmp_file.write(uploaded_file.getbuffer())
                tmp_path = tmp_file.name

            try:
                # Carrega modelo Whisper
                # Verifica se precisa recarregar modelo
                if st.session_state.ultimo_modelo != modelo_nome:
                    st.session_state.modelo_carregado = None
                    st.session_state.ultimo_modelo = modelo_nome

                if st.session_state.modelo_carregado is None:
                    with st.spinner(f"Carregando modelo Whisper '{modelo_nome}' (pode demorar na primeira vez)..."):
                        modelo_whisper = carregar_modelo_whisper_streamlit(modelo_nome)
                        st.session_state.modelo_carregado = modelo_whisper
                        st.success(f"Modelo '{modelo_nome}' carregado com sucesso!")
                else:
                    modelo_whisper = st.session_state.modelo_carregado

                # Área de progresso
                st.divider()
                st.subheader("📊 Progresso")

                progress_bar = st.progress(0)
                status_text = st.empty()
                preview_text = st.empty()

                # Callbacks para atualizar UI
                def update_progress(p):
                    progress_bar.progress(min(p, 1.0))

                def update_status(msg):
                    status_text.text(f"Status: {msg}")

                def update_preview(texto):
                    if texto:
                        preview_text.text(f"Última transcrição: {texto}...")

                callbacks = {
                    'progress': update_progress,
                    'status': update_status,
                    'transcricao_preview': update_preview
                }

                # Processa (sempre transcreve)
                with st.spinner("Processando arquivo..."):
                    resultados = processar_audio_streamlit(
                        tmp_path,
                        modelo_whisper,
                        duracao_segmentos,
                        callbacks
                    )

                # Limpa arquivo temporário
                os.unlink(tmp_path)

                # Verifica resultado
                if resultados.get('sucesso'):
                    st.session_state.results = resultados
                    progress_bar.progress(1.0)
                    status_text.text("Status: Concluído!")
                else:
                    st.error(f"Erro durante processamento: {resultados.get('erro')}")
                    with st.expander("Detalhes do Erro"):
                        st.code(resultados.get('traceback', ''))

            except Exception as e:
                st.error(f"Erro: {str(e)}")
                import traceback
                with st.expander("Detalhes do Erro"):
                    st.code(traceback.format_exc())

            finally:
                st.session_state.processing = False

        # Exibe resultados se existirem
        if st.session_state.results is not None:
            st.divider()
            st.subheader("3️⃣ Resultados")

            resultados = st.session_state.results

            if resultados.get('sucesso'):
                # Sempre exibe resultados de transcrição (já que sempre transcreve)
                exibir_resultados_transcricao_completa(resultados)

    else:
        # Instruções quando não há arquivo
        st.info("👆 Carregue um arquivo de áudio ou vídeo para começar")

        with st.expander("ℹ️ Como Usar"):
            st.markdown("""
            ### Passos:
            1. **Escolha o modelo** Whisper na barra lateral
            2. **Configure a duração** dos segmentos (padrão: 4 minutos)
            3. **Carregue seu arquivo** (áudio ou vídeo)
            4. **Clique em "Processar"** e aguarde

            ### O que o sistema faz:
            1. **Se for vídeo:** Extrai o áudio automaticamente
            2. **Divide:** Separa o áudio em segmentos menores
            3. **Transcreve:** Usa IA (Whisper) para gerar texto de cada segmento
            4. **Salva:** Cria arquivos de transcrição completa e detalhada

            ### Modelos Whisper:
            - **tiny:** Mais rápido (~1.4 min/min áudio), qualidade básica
            - **base:** Balanceado (~2-3 min/min) - **Recomendado**
            - **small:** Boa qualidade (~3-4 min/min)
            - **medium:** Alta qualidade (~4-5 min/min)
            - **large:** Melhor qualidade (~5-6 min/min), muito lento

            ### Formatos Suportados:
            **Áudio:** MP3, WAV, M4A, AAC, FLAC, OGG, WMA
            **Vídeo:** MP4, AVI, MOV, MKV, FLV, WMV, WEBM, M4V, MPG, MPEG

            ### Dicas:
            - Para arquivos grandes (>1 hora), use modelo **tiny** e segmentos de **2-3 min**
            - Vídeos são convertidos automaticamente para áudio WAV
            - O sistema salva incrementalmente, então se parar, parte do trabalho não é perdido
            """)

    # Rodapé
    st.divider()
    st.caption("Split Audio v2.0 - Transcritor Automático de Áudio/Vídeo | Desenvolvido com Streamlit")


if __name__ == "__main__":
    main()
