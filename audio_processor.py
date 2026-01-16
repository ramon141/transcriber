#!/usr/bin/env python3
"""
Módulo de processamento de áudio para interface Streamlit.
Contém wrappers das funções de split_audio.py com suporte a callbacks.
Suporta conversão de vídeo para áudio e diarização (identificação de falantes).
"""

import os
import tempfile
import traceback
from pathlib import Path
from typing import List, Dict, Optional
import streamlit as st
import librosa
import soundfile as sf
import numpy as np

# Importa funções do módulo principal
from split_audio import (
    criar_pasta_saida,
    carregar_modelo_whisper,
)

# Importa funções de diarização
from diarization import (
    verificar_token_configurado,
    carregar_pipeline_diarizacao,
    diarizar_audio,
    mapear_falantes_para_nomes,
    combinar_diarizacao_transcricao,
    formatar_transcricao_com_falantes,
    criar_resumo_falantes,
)


def extrair_audio_de_video(arquivo_video: str, callbacks: dict = None):
    """
    Extrai áudio de um arquivo de vídeo e salva como WAV.

    Args:
        arquivo_video: Caminho do arquivo de vídeo
        callbacks: Dict com callback 'status' para atualizar UI

    Returns:
        Caminho do arquivo de áudio extraído
    """
    try:
        from moviepy.video.io.VideoFileClip import VideoFileClip
    except ImportError:
        raise ImportError("moviepy não está instalado. Execute: pip install moviepy")

    status_callback = callbacks.get('status') if callbacks else None

    if status_callback:
        status_callback(f"Extraindo áudio do vídeo...")

    # Cria arquivo temporário para o áudio
    arquivo_audio = tempfile.NamedTemporaryFile(delete=False, suffix='.wav').name

    # Extrai áudio do vídeo
    video = VideoFileClip(arquivo_video)

    # Extrai e salva o áudio
    video.audio.write_audiofile(
        arquivo_audio,
        codec='pcm_s16le'  # WAV format
    )
    video.close()

    if status_callback:
        status_callback(f"Áudio extraído com sucesso!")

    return arquivo_audio


def detectar_tipo_arquivo(arquivo: str):
    """
    Detecta se o arquivo é vídeo ou áudio baseado na extensão.

    Args:
        arquivo: Caminho do arquivo

    Returns:
        'video' ou 'audio'
    """
    extensoes_video = ['.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv', '.webm', '.m4v', '.mpg', '.mpeg']
    extensoes_audio = ['.mp3', '.wav', '.m4a', '.aac', '.flac', '.ogg', '.wma']

    extensao = Path(arquivo).suffix.lower()

    if extensao in extensoes_video:
        return 'video'
    elif extensao in extensoes_audio:
        return 'audio'
    else:
        return 'unknown'


@st.cache_resource
def carregar_modelo_whisper_streamlit(modelo_nome: str):
    """
    Carrega o modelo Whisper com cache para evitar recarregamentos.

    Args:
        modelo_nome: Nome do modelo ('tiny', 'base', 'small', 'medium', 'large')

    Returns:
        Modelo Whisper carregado
    """
    return carregar_modelo_whisper(modelo_nome)


@st.cache_resource
def carregar_pipeline_diarizacao_streamlit():
    """
    Carrega o pipeline de diarização Pyannote com cache.

    Returns:
        Pipeline de diarização carregado
    """
    return carregar_pipeline_diarizacao()


def transcrever_completa_streamlit(
    arquivo_entrada: str,
    modelo_whisper,
    pasta_saida: str,
    nome_base: str,
    segmentos: list,
    callbacks: dict = None,
    diarizar: bool = True,
    pipeline_diarizacao = None
):
    """
    Transcreve todos os segmentos com callbacks para atualizar UI do Streamlit.
    Suporta diarização (identificação de falantes) quando ativada.

    Args:
        arquivo_entrada: Caminho do arquivo de áudio
        modelo_whisper: Modelo Whisper carregado
        pasta_saida: Pasta onde salvar os resultados
        nome_base: Nome base para os arquivos
        segmentos: Lista de tuplas (segmento_audio, duracao)
        callbacks: Dict com callbacks opcionais:
            - 'progress': função(percentual) para atualizar barra de progresso
            - 'status': função(mensagem) para atualizar status
            - 'transcricao_preview': função(texto) para preview da transcrição
        diarizar: Se deve identificar falantes (padrão: True)
        pipeline_diarizacao: Pipeline Pyannote carregado (necessário se diarizar=True)

    Returns:
        Dict com informações dos resultados
    """
    callbacks = callbacks or {}
    progress_callback = callbacks.get('progress')
    status_callback = callbacks.get('status')
    preview_callback = callbacks.get('transcricao_preview')

    # Cria os arquivos de transcrição
    nome_arquivo_completo = f"{nome_base}_transcricao_completa.txt"
    caminho_completo = os.path.join(pasta_saida, nome_arquivo_completo)
    nome_detalhado = f"{nome_base}_transcricao_detalhada.txt"
    caminho_detalhado = os.path.join(pasta_saida, nome_detalhado)

    # Inicializa arquivo com cabeçalho
    modo_texto = "COM IDENTIFICAÇÃO DE FALANTES" if diarizar else "SEM IDENTIFICAÇÃO DE FALANTES"
    with open(caminho_completo, 'w', encoding='utf-8') as f:
        f.write(f"TRANSCRIÇÃO COMPLETA DO ÁUDIO ({modo_texto})\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Arquivo original: {arquivo_entrada}\n")
        f.write(f"Total de segmentos: {len(segmentos)}\n")
        f.write(f"Diarização: {'Ativada' if diarizar else 'Desativada'}\n")
        f.write(f"Status: Processando segmentos...\n\n")
        f.write("=" * 50 + "\n\n")

    # Variáveis para acumular resultados
    todos_segmentos_transcricao = []
    segmentos_diarizacao_global = []
    segmentos_info = []
    offset_tempo = 0.0  # Acumula o offset de tempo para cada segmento

    # Processa cada segmento
    for i, (segmento, duracao) in enumerate(segmentos, 1):
        if status_callback:
            status_callback(f"Processando segmento {i}/{len(segmentos)}...")

        # Salva segmento como WAV temporário
        nome_arquivo = f"{nome_base}_parte_{i:02d}.wav"
        caminho_wav = os.path.join(pasta_saida, nome_arquivo)
        sf.write(caminho_wav, segmento, 48000)

        # Diarização do segmento (se ativada)
        if diarizar and pipeline_diarizacao is not None:
            if status_callback:
                status_callback(f"Identificando falantes no segmento {i}/{len(segmentos)}...")

            segmentos_diar = diarizar_audio(caminho_wav, pipeline_diarizacao)

            # Ajusta timestamps com offset
            for seg_diar in segmentos_diar:
                seg_diar['inicio'] += offset_tempo
                seg_diar['fim'] += offset_tempo
                segmentos_diarizacao_global.append(seg_diar)

        # Transcreve com faster-whisper
        if status_callback:
            status_callback(f"Transcrevendo segmento {i}/{len(segmentos)}...")

        segments, info = modelo_whisper.transcribe(caminho_wav, language="pt")

        # Coleta segmentos com timestamps
        for seg in segments:
            seg_info = {
                'inicio': seg.start + offset_tempo,
                'fim': seg.end + offset_tempo,
                'texto': seg.text.strip()
            }
            if seg_info['texto']:
                todos_segmentos_transcricao.append(seg_info)

        # Texto do segmento atual para preview
        texto_segmento = " ".join([s['texto'] for s in todos_segmentos_transcricao if s['inicio'] >= offset_tempo])

        if texto_segmento:
            segmentos_info.append({
                'numero': i,
                'duracao': duracao,
                'texto': texto_segmento,
                'timestamp': f"[{i:02d}] {texto_segmento}"
            })

            if preview_callback:
                preview_callback(texto_segmento[:100])

        # Remove WAV temporário
        if os.path.exists(caminho_wav):
            os.remove(caminho_wav)

        # Atualiza offset para próximo segmento
        offset_tempo += duracao

        # Atualiza progresso
        if progress_callback:
            progress_callback(i / len(segmentos))

    # Mapeia falantes para nomes amigáveis se diarização ativada
    if diarizar and segmentos_diarizacao_global:
        segmentos_diarizacao_global, mapeamento_falantes = mapear_falantes_para_nomes(
            segmentos_diarizacao_global
        )

        # Combina diarização com transcrição
        segmentos_combinados = combinar_diarizacao_transcricao(
            segmentos_diarizacao_global,
            todos_segmentos_transcricao
        )

        # Formata transcrição com falantes
        transcricao_completa = formatar_transcricao_com_falantes(
            segmentos_combinados,
            incluir_timestamps=False
        )

        # Cria resumo de falantes
        resumo_falantes = criar_resumo_falantes(segmentos_combinados)
    else:
        # Sem diarização: usa transcrição simples
        segmentos_combinados = todos_segmentos_transcricao
        transcricao_completa = " ".join([s['texto'] for s in todos_segmentos_transcricao])
        resumo_falantes = {}

    # Atualização final do arquivo completo
    duracao_total = sum(s['duracao'] for s in segmentos_info) if segmentos_info else offset_tempo
    with open(caminho_completo, 'w', encoding='utf-8') as f:
        f.write(f"TRANSCRIÇÃO COMPLETA DO ÁUDIO ({modo_texto})\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Arquivo original: {arquivo_entrada}\n")
        f.write(f"Total de segmentos: {len(segmentos)}\n")
        f.write(f"Duração total: {duracao_total:.1f} segundos\n")
        f.write(f"Diarização: {'Ativada' if diarizar else 'Desativada'}\n")

        if diarizar and resumo_falantes:
            f.write(f"Falantes identificados: {len(resumo_falantes)}\n")

        f.write(f"Status: COMPLETO\n\n")
        f.write("=" * 50 + "\n\n")
        f.write(transcricao_completa)

    # Salva arquivo detalhado
    with open(caminho_detalhado, 'w', encoding='utf-8') as f:
        f.write(f"TRANSCRIÇÃO DETALHADA DO ÁUDIO ({modo_texto})\n")
        f.write("=" * 60 + "\n\n")

        if diarizar and segmentos_combinados:
            # Com diarização: mostra cada fala com falante
            for i, seg in enumerate(segmentos_combinados, 1):
                f.write(f"SEGMENTO {i:02d}\n")
                f.write("-" * 30 + "\n")
                f.write(f"Tempo: {seg['inicio']:.1f}s - {seg['fim']:.1f}s\n")
                f.write(f"Falante: {seg.get('falante', 'DESCONHECIDO')}\n")
                f.write(f"Texto: {seg['texto']}\n\n")
        else:
            # Sem diarização: mostra por segmento de áudio
            for info in segmentos_info:
                f.write(f"SEGMENTO {info['numero']:02d}\n")
                f.write("-" * 30 + "\n")
                f.write(f"Duração: {info['duracao']:.1f} segundos\n")
                f.write(f"Texto: {info['texto']}\n\n")

    if status_callback:
        status_callback("Transcrição completa finalizada!")

    return {
        'sucesso': True,
        'transcricao_completa': transcricao_completa,
        'segmentos': segmentos_info,
        'segmentos_com_falantes': segmentos_combinados if diarizar else [],
        'resumo_falantes': resumo_falantes,
        'diarizacao_ativada': diarizar,
        'arquivo_completo': caminho_completo,
        'arquivo_detalhado': caminho_detalhado,
        'pasta_saida': pasta_saida
    }


def dividir_audio_streamlit(
    arquivo_entrada: str,
    duracao_segmento_min: int = 4,
    callbacks: dict = None
):
    """
    Divide um arquivo de áudio em segmentos menores.

    Args:
        arquivo_entrada: Caminho do arquivo de áudio
        duracao_segmento_min: Duração de cada segmento em minutos
        callbacks: Dict com callbacks opcionais

    Returns:
        Dict com informações dos segmentos criados
    """
    callbacks = callbacks or {}
    status_callback = callbacks.get('status')
    progress_callback = callbacks.get('progress')

    if status_callback:
        status_callback(f"Carregando arquivo: {Path(arquivo_entrada).name}")

    # Carrega áudio
    audio_data, sample_rate = librosa.load(arquivo_entrada, sr=None)

    # Informações
    duracao_total_segundos = len(audio_data) / sample_rate
    duracao_total_minutos = duracao_total_segundos / 60

    # Cria pasta de saída
    pasta_saida = criar_pasta_saida(arquivo_entrada)
    nome_base = Path(arquivo_entrada).stem

    # Calcula segmentos
    duracao_segmento_amostras = int(duracao_segmento_min * 60 * sample_rate)
    num_segmentos = int(len(audio_data) / duracao_segmento_amostras) + 1

    if status_callback:
        status_callback(f"Criando {num_segmentos} segmentos de {duracao_segmento_min} minutos")

    segmentos = []
    arquivos_criados = []

    # Divide e salva
    from pydub import AudioSegment

    for i in range(num_segmentos):
        inicio_amostra = i * duracao_segmento_amostras
        fim_amostra = min((i + 1) * duracao_segmento_amostras, len(audio_data))

        # Extrai segmento
        segmento = audio_data[inicio_amostra:fim_amostra]
        duracao_segmento = len(segmento) / sample_rate

        # Salva como M4A
        nome_arquivo = f"{nome_base}_parte_{i+1:02d}.m4a"
        caminho_saida = os.path.join(pasta_saida, nome_arquivo)

        if segmento.dtype != np.float32:
            segmento = segmento.astype(np.float32)

        audio_segment = AudioSegment(
            segmento.tobytes(),
            frame_rate=sample_rate,
            sample_width=4,
            channels=1 if len(segmento.shape) == 1 else segmento.shape[1]
        )

        audio_segment.export(caminho_saida, format="mp4")

        segmentos.append((segmento, duracao_segmento))
        arquivos_criados.append({
            'numero': i + 1,
            'nome': nome_arquivo,
            'caminho': caminho_saida,
            'duracao': duracao_segmento
        })

        if progress_callback:
            progress_callback((i + 1) / num_segmentos)

        if status_callback:
            status_callback(f"Criado segmento {i+1}/{num_segmentos}")

    return {
        'sucesso': True,
        'segmentos': segmentos,
        'arquivos': arquivos_criados,
        'pasta_saida': pasta_saida,
        'nome_base': nome_base,
        'duracao_total': duracao_total_minutos
    }


def processar_audio_streamlit(
    arquivo_temporario: str,
    modelo_whisper,
    duracao_segmentos: int = 4,
    callbacks: dict = None,
    diarizar: bool = True,
    pipeline_diarizacao = None
):
    """
    Função principal que coordena todo o processamento.
    Sempre divide o áudio/vídeo e transcreve cada parte.
    Suporta diarização (identificação de falantes).

    Fluxo:
    1. Se for vídeo, converte para áudio
    2. Divide o áudio em segmentos
    3. Se diarização ativada, identifica falantes
    4. Transcreve cada segmento
    5. Combina diarização + transcrição

    Args:
        arquivo_temporario: Caminho do arquivo temporário (áudio ou vídeo)
        modelo_whisper: Modelo Whisper carregado
        duracao_segmentos: Duração de cada segmento em minutos
        callbacks: Dict com callbacks para UI
        diarizar: Se deve identificar falantes (padrão: True)
        pipeline_diarizacao: Pipeline Pyannote carregado (necessário se diarizar=True)

    Returns:
        Dict com resultados do processamento
    """
    arquivo_audio_temp = None

    try:
        # Detecta tipo de arquivo
        tipo_arquivo = detectar_tipo_arquivo(arquivo_temporario)

        if tipo_arquivo == 'video':
            # Converte vídeo para áudio
            if callbacks and callbacks.get('status'):
                callbacks['status']("Convertendo vídeo para áudio...")

            arquivo_audio_temp = extrair_audio_de_video(arquivo_temporario, callbacks)
            arquivo_para_processar = arquivo_audio_temp
        elif tipo_arquivo == 'audio':
            arquivo_para_processar = arquivo_temporario
        else:
            raise ValueError(f"Formato de arquivo não suportado: {Path(arquivo_temporario).suffix}")

        # Divide o áudio em segmentos
        resultado_divisao = dividir_audio_streamlit(
            arquivo_para_processar,
            duracao_segmentos,
            callbacks
        )

        if not resultado_divisao['sucesso']:
            return resultado_divisao

        # Transcreve com progresso (e diarização se ativada)
        resultado_transcricao = transcrever_completa_streamlit(
            arquivo_para_processar,
            modelo_whisper,
            resultado_divisao['pasta_saida'],
            resultado_divisao['nome_base'],
            resultado_divisao['segmentos'],
            callbacks,
            diarizar=diarizar,
            pipeline_diarizacao=pipeline_diarizacao
        )

        # Combina resultados
        resultado_transcricao['arquivos'] = resultado_divisao['arquivos']
        resultado_transcricao['duracao_total'] = resultado_divisao['duracao_total']
        resultado_transcricao['tipo_arquivo_original'] = tipo_arquivo

        return resultado_transcricao

    except Exception as e:
        return {
            'sucesso': False,
            'erro': str(e),
            'traceback': traceback.format_exc()
        }
    finally:
        # Limpa arquivo de áudio temporário se foi criado
        if arquivo_audio_temp and os.path.exists(arquivo_audio_temp):
            try:
                os.unlink(arquivo_audio_temp)
            except:
                pass


def obter_info_modelo(modelo_nome: str):
    """
    Retorna informações sobre qualidade e velocidade do modelo.

    Args:
        modelo_nome: Nome do modelo

    Returns:
        Dict com informações
    """
    info_modelos = {
        'tiny': {
            'qualidade': '⭐⭐',
            'velocidade': '⚡⚡⚡⚡⚡',
            'descricao': 'Mais rápido, qualidade básica',
            'tempo_estimado': '~1.4 min por min de áudio'
        },
        'base': {
            'qualidade': '⭐⭐⭐',
            'velocidade': '⚡⚡⚡⚡',
            'descricao': 'Balanceado - recomendado',
            'tempo_estimado': '~2-3 min por min de áudio'
        },
        'small': {
            'qualidade': '⭐⭐⭐⭐',
            'velocidade': '⚡⚡⚡',
            'descricao': 'Boa qualidade, velocidade média',
            'tempo_estimado': '~3-4 min por min de áudio'
        },
        'medium': {
            'qualidade': '⭐⭐⭐⭐⭐',
            'velocidade': '⚡⚡',
            'descricao': 'Qualidade alta, mais lento',
            'tempo_estimado': '~4-5 min por min de áudio'
        },
        'large': {
            'qualidade': '⭐⭐⭐⭐⭐⭐',
            'velocidade': '⚡',
            'descricao': 'Melhor qualidade, muito lento',
            'tempo_estimado': '~5-6 min por min de áudio'
        },
        'large-v1': {
            'qualidade': '⭐⭐⭐⭐⭐⭐',
            'velocidade': '⚡',
            'descricao': 'Large versão 1 - Alta precisão',
            'tempo_estimado': '~5-6 min por min de áudio'
        },
        'large-v2': {
            'qualidade': '⭐⭐⭐⭐⭐⭐',
            'velocidade': '⚡',
            'descricao': 'Large versão 2 - Melhor que v1',
            'tempo_estimado': '~5-6 min por min de áudio'
        },
        'large-v3': {
            'qualidade': '⭐⭐⭐⭐⭐⭐',
            'velocidade': '⚡',
            'descricao': 'Large versão 3 - Mais recente e preciso',
            'tempo_estimado': '~5-6 min por min de áudio'
        }
    }

    return info_modelos.get(modelo_nome, info_modelos['base'])
