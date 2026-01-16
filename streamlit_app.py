#!/usr/bin/env python3
"""
Interface Web Streamlit para Transcriber.
Processador e transcritor de áudio com interface intuitiva.
Suporta diarização (identificação de falantes).
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
    carregar_pipeline_diarizacao_streamlit,
    processar_audio_streamlit,
    obter_info_modelo
)

# Importa funções de diarização
from diarization import verificar_token_configurado


def configurar_pagina():
    """Configura a página do Streamlit."""
    st.set_page_config(
        page_title="Transcriber - Processador de Áudio",
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
    if 'pipeline_diarizacao' not in st.session_state:
        st.session_state.pipeline_diarizacao = None
    if 'diarizacao_carregada' not in st.session_state:
        st.session_state.diarizacao_carregada = False


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
        Tuple com (modelo_nome, duracao_segmentos, diarizar)
    """
    with st.sidebar:
        st.title("⚙️ Configurações")

        # Configurações de transcrição
        st.subheader("Modelo de Transcrição")

        modelo_nome = st.select_slider(
            "Modelo Whisper",
            options=['tiny', 'base', 'small', 'medium', 'large', 'large-v1', 'large-v2', 'large-v3'],
            value='base',
            help="Escolha o modelo de IA para transcrição. large-v3 é a versão mais recente e precisa."
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

        # Diarização (identificação de falantes)
        st.divider()
        st.subheader("Identificação de Falantes")

        # Verifica se token está configurado
        token_configurado = verificar_token_configurado()

        diarizar = st.checkbox(
            "Identificar Falantes (Diarização)",
            value=True,
            help="Identifica quem está falando em cada momento do áudio",
            disabled=not token_configurado
        )

        if diarizar and token_configurado:
            st.success("Token HF configurado!")
            st.caption("""
A diarização identifica automaticamente os diferentes falantes no áudio.
O resultado mostrará:
- **[FALANTE 1]** Texto falado...
- **[FALANTE 2]** Outro texto...
            """)
        elif diarizar and not token_configurado:
            st.error("Token HF não configurado!")
            st.warning("""
**Para usar diarização:**
1. Crie um arquivo `.env` na raiz do projeto
2. Adicione: `HF_TOKEN=seu_token_aqui`
3. Obtenha o token em: [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)
4. Aceite os termos do modelo em: [pyannote/speaker-diarization-3.1](https://huggingface.co/pyannote/speaker-diarization-3.1)
            """)
            diarizar = False
        else:
            st.caption("Desativado: transcrição simples sem identificação de falantes.")

        # Informações adicionais
        st.divider()
        st.caption("💡 **Dica:** Para arquivos grandes, use segmentos menores e o modelo 'tiny' para processar mais rápido.")

        if diarizar:
            st.caption("⚠️ **Nota:** A diarização é mais lenta. GPU recomendada para melhor desempenho.")

        return modelo_nome, duracao_segmentos, diarizar


def obter_cor_falante(falante: str) -> str:
    """Retorna uma cor para cada falante."""
    cores = {
        'FALANTE 1': '#1f77b4',  # Azul
        'FALANTE 2': '#ff7f0e',  # Laranja
        'FALANTE 3': '#2ca02c',  # Verde
        'FALANTE 4': '#d62728',  # Vermelho
        'FALANTE 5': '#9467bd',  # Roxo
        'FALANTE 6': '#8c564b',  # Marrom
        'FALANTE 7': '#e377c2',  # Rosa
        'FALANTE 8': '#7f7f7f',  # Cinza
        'DESCONHECIDO': '#bcbd22',  # Amarelo
    }
    return cores.get(falante, '#17becf')  # Ciano como padrão


def exibir_resultados_transcricao_completa(resultados: dict):
    """Exibe resultados da transcrição completa."""
    st.success("Transcrição completa finalizada!")

    diarizacao_ativada = resultados.get('diarizacao_ativada', False)
    resumo_falantes = resultados.get('resumo_falantes', {})

    # Métricas
    if diarizacao_ativada and resumo_falantes:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Segmentos Processados", len(resultados['segmentos']))
        with col2:
            st.metric("Duração Total", f"{resultados['duracao_total']:.1f} min")
        with col3:
            st.metric("Falantes Identificados", len(resumo_falantes))
        with col4:
            pasta_nome = Path(resultados['pasta_saida']).name
            st.metric("Pasta de Saída", pasta_nome)
    else:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Segmentos Processados", len(resultados['segmentos']))
        with col2:
            st.metric("Duração Total", f"{resultados['duracao_total']:.1f} min")
        with col3:
            pasta_nome = Path(resultados['pasta_saida']).name
            st.metric("Pasta de Saída", pasta_nome)

    # Tabs para diferentes visualizações
    if diarizacao_ativada:
        tab1, tab2, tab3, tab4 = st.tabs([
            "📄 Transcrição Completa",
            "👥 Por Falante",
            "📁 Segmentos",
            "⬇️ Downloads"
        ])
    else:
        tab1, tab2, tab3 = st.tabs(["📄 Transcrição Completa", "📁 Segmentos", "⬇️ Downloads"])

    with tab1:
        st.subheader("Transcrição Completa")

        if diarizacao_ativada:
            st.caption("Com identificação de falantes")

            # Exibe transcrição com cores por falante
            segmentos_com_falantes = resultados.get('segmentos_com_falantes', [])
            if segmentos_com_falantes:
                for seg in segmentos_com_falantes:
                    falante = seg.get('falante', 'DESCONHECIDO')
                    cor = obter_cor_falante(falante)
                    texto = seg.get('texto', '')
                    st.markdown(
                        f'<span style="color:{cor}; font-weight:bold;">[{falante}]</span> {texto}',
                        unsafe_allow_html=True
                    )
            else:
                st.text_area(
                    "Texto transcrito:",
                    value=resultados.get('transcricao_completa', ''),
                    height=400
                )
        else:
            st.text_area(
                "Texto transcrito:",
                value=resultados.get('transcricao_completa', ''),
                height=400,
                help="Copie o texto transcrito daqui"
            )

        # Botão para copiar
        if st.button("📋 Copiar para Área de Transferência"):
            st.info("Use Ctrl+A e Ctrl+C na área de texto acima para copiar")

    # Tab por falante (apenas se diarização ativada)
    if diarizacao_ativada:
        with tab2:
            st.subheader("Transcrições por Falante")

            if resumo_falantes:
                for falante, stats in resumo_falantes.items():
                    cor = obter_cor_falante(falante)
                    tempo_min = stats['tempo_total'] / 60

                    with st.expander(
                        f"👤 {falante} - {stats['num_falas']} falas ({tempo_min:.1f} min)"
                    ):
                        st.markdown(
                            f'<div style="border-left: 4px solid {cor}; padding-left: 10px;">',
                            unsafe_allow_html=True
                        )

                        for texto in stats.get('textos', []):
                            st.write(f"• {texto}")

                        st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.info("Nenhum falante identificado.")

        # Ajusta índice das tabs
        tab_segmentos = tab3
        tab_downloads = tab4
    else:
        tab_segmentos = tab2
        tab_downloads = tab3

    with tab_segmentos:
        st.subheader("Transcrições por Segmento")

        for seg in resultados.get('segmentos', []):
            with st.expander(f"🎵 Segmento {seg['numero']:02d} ({seg['duracao']:.1f}s)"):
                st.write(seg['texto'])

                # Botão para copiar segmento individual
                st.caption(f"**Timestamp:** {seg.get('timestamp', '')}")

    with tab_downloads:
        st.subheader("Downloads")

        st.write("**Arquivos de Transcrição:**")

        # Lê e oferece download dos arquivos de transcrição
        if os.path.exists(resultados.get('arquivo_completo', '')):
            with open(resultados['arquivo_completo'], 'r', encoding='utf-8') as f:
                conteudo_completo = f.read()

            label_completo = "📄 Transcrição Completa"
            if diarizacao_ativada:
                label_completo += " (com falantes)"
            label_completo += " (.txt)"

            st.download_button(
                label=label_completo,
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
    st.title("🎵 Transcriber - Processador e Transcritor de Áudio/Vídeo")
    st.markdown("""
    Converte vídeos para áudio, divide em segmentos e transcreve automaticamente com IA (faster-whisper).
    **Novidade:** Identificação automática de falantes (diarização) com Pyannote!

    **Áudio:** MP3, WAV, M4A, AAC, FLAC, OGG, WMA
    **Vídeo:** MP4, AVI, MOV, MKV, FLV, WMV, WEBM
    """)

    # Configurações na sidebar
    modelo_nome, duracao_segmentos, diarizar = sidebar_configuracoes()

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
                    with st.spinner(f"Carregando modelo faster-whisper '{modelo_nome}' (pode demorar na primeira vez)..."):
                        modelo_whisper = carregar_modelo_whisper_streamlit(modelo_nome)
                        st.session_state.modelo_carregado = modelo_whisper
                        st.success(f"Modelo '{modelo_nome}' carregado com sucesso!")
                else:
                    modelo_whisper = st.session_state.modelo_carregado

                # Carrega pipeline de diarização se necessário
                pipeline_diarizacao = None
                if diarizar:
                    if not st.session_state.diarizacao_carregada:
                        with st.spinner("Carregando modelo de diarização Pyannote (pode demorar na primeira vez)..."):
                            try:
                                pipeline_diarizacao = carregar_pipeline_diarizacao_streamlit()
                                st.session_state.pipeline_diarizacao = pipeline_diarizacao
                                st.session_state.diarizacao_carregada = True
                                st.success("Modelo de diarização carregado com sucesso!")
                            except Exception as e:
                                st.error(f"Erro ao carregar diarização: {e}")
                                st.warning("Continuando sem identificação de falantes...")
                                diarizar = False
                    else:
                        pipeline_diarizacao = st.session_state.pipeline_diarizacao

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

                # Processa (sempre transcreve, opcionalmente com diarização)
                modo_texto = "com identificação de falantes" if diarizar else "sem identificação de falantes"
                with st.spinner(f"Processando arquivo ({modo_texto})..."):
                    resultados = processar_audio_streamlit(
                        tmp_path,
                        modelo_whisper,
                        duracao_segmentos,
                        callbacks,
                        diarizar=diarizar,
                        pipeline_diarizacao=pipeline_diarizacao
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
            3. **Ative/desative a diarização** (identificação de falantes)
            4. **Carregue seu arquivo** (áudio ou vídeo)
            5. **Clique em "Processar"** e aguarde

            ### O que o sistema faz:
            1. **Se for vídeo:** Extrai o áudio automaticamente
            2. **Divide:** Separa o áudio em segmentos menores
            3. **Diariza (opcional):** Identifica quem está falando em cada momento
            4. **Transcreve:** Usa IA (faster-whisper) para gerar texto de cada segmento
            5. **Combina:** Associa cada frase ao falante correto
            6. **Salva:** Cria arquivos de transcrição com identificação de falantes

            ### Identificação de Falantes (Diarização):
            - **Ativada por padrão** se o token HF estiver configurado
            - Requer token do Hugging Face (gratuito)
            - Resultado: `[FALANTE 1] Olá... [FALANTE 2] Tudo bem...`
            - GPU recomendada para melhor desempenho

            ### Como configurar o Token HF:
            1. Crie conta em [huggingface.co](https://huggingface.co)
            2. Obtenha token em [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)
            3. Aceite os termos em [pyannote/speaker-diarization-3.1](https://huggingface.co/pyannote/speaker-diarization-3.1)
            4. Crie arquivo `.env` na raiz do projeto com: `HF_TOKEN=seu_token`

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
            - Desative diarização se não precisar identificar falantes (mais rápido)
            - Vídeos são convertidos automaticamente para áudio WAV
            - O sistema salva incrementalmente, então se parar, parte do trabalho não é perdido
            """)

    # Rodapé
    st.divider()
    st.caption("Transcriber v3.0 - Transcritor Automático com Diarização | faster-whisper + Pyannote")


if __name__ == "__main__":
    main()
