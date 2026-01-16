#!/usr/bin/env python3
"""
Script para dividir arquivos de áudio longos em segmentos menores.
Divide um arquivo de áudio de 1 hora em segmentos de 4 minutos cada.
Usa librosa e soundfile para compatibilidade com Python 3.13.
Suporta diarização (identificação de falantes) com Pyannote.
"""

import os
import sys
import numpy as np
from pathlib import Path
import librosa
import soundfile as sf
from pydub import AudioSegment
from faster_whisper import WhisperModel
import argparse
from tqdm import tqdm

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

def verificar_dependencias():
    """Verifica se as dependências necessárias estão instaladas."""
    try:
        import librosa
        import soundfile
        from pydub import AudioSegment
        from faster_whisper import WhisperModel
        from tqdm import tqdm
        print("✓ librosa, soundfile, pydub, faster-whisper e tqdm estão instalados")
        return True
    except ImportError as e:
        print(f"❌ Dependências não encontradas: {e}")
        print("Execute: pip install librosa soundfile pydub faster-whisper torch tqdm")
        return False

def criar_pasta_saida(nome_arquivo_original):
    """Cria uma pasta para os arquivos divididos."""
    nome_base = Path(nome_arquivo_original).stem
    pasta_saida = f"{nome_base}_dividido"
    
    if not os.path.exists(pasta_saida):
        os.makedirs(pasta_saida)
        print(f"✓ Pasta criada: {pasta_saida}")
    else:
        print(f"✓ Pasta já existe: {pasta_saida}")
    
    return pasta_saida

def carregar_modelo_whisper(modelo="base"):
    """Carrega o modelo Whisper (faster-whisper) para transcrição."""
    print(f"🤖 Carregando modelo faster-whisper '{modelo}'...")
    try:
        # Detecta automaticamente o melhor dispositivo e tipo de computação
        modelo_whisper = WhisperModel(modelo, device="auto", compute_type="auto")
        print(f"✓ Modelo faster-whisper '{modelo}' carregado com sucesso")
        return modelo_whisper
    except Exception as e:
        print(f"❌ Erro ao carregar modelo faster-whisper: {e}")
        return None

def transcrever_audio(arquivo_audio, modelo_whisper, pasta_saida, nome_base, parte_num=None):
    """Transcreve um arquivo de áudio usando faster-whisper."""
    try:
        print(f"🎤 Transcrevendo: {arquivo_audio}")

        # Converte para WAV se necessário para melhor compatibilidade
        arquivo_temp = arquivo_audio
        if arquivo_audio.lower().endswith('.m4a'):
            arquivo_temp = arquivo_audio.replace('.m4a', '_temp.wav')
            print(f"🔄 Convertendo M4A para WAV: {arquivo_temp}")

            # Carrega com librosa e salva como WAV
            audio_data, sample_rate = librosa.load(arquivo_audio, sr=None)
            # Ajusta a normalização para valores similares ao arquivo WAV original
            if audio_data.max() > 0.7:  # Se está muito normalizado
                audio_data = audio_data * 0.6  # Reduz para valores similares ao WAV
            sf.write(arquivo_temp, audio_data, sample_rate)

        # Transcreve o áudio com faster-whisper
        segments, info = modelo_whisper.transcribe(arquivo_temp, language="pt")
        texto_transcrito = " ".join([seg.text.strip() for seg in segments])

        # Remove arquivo temporário se foi criado
        if arquivo_temp != arquivo_audio and os.path.exists(arquivo_temp):
            os.remove(arquivo_temp)

        # Nome do arquivo de transcrição
        if parte_num is not None:
            nome_transcricao = f"{nome_base}_parte_{parte_num:02d}.txt"
        else:
            nome_transcricao = f"{nome_base}_transcricao_completa.txt"

        caminho_transcricao = os.path.join(pasta_saida, nome_transcricao)

        # Salva a transcrição
        with open(caminho_transcricao, 'w', encoding='utf-8') as f:
            f.write(texto_transcrito)

        print(f"✓ Transcrição salva: {nome_transcricao}")
        print(f"📝 Texto: {texto_transcrito[:100]}...")

        return True

    except Exception as e:
        print(f"❌ Erro na transcrição: {e}")
        return False

def transcrever_completa_com_progresso(arquivo_entrada, modelo_whisper, pasta_saida, nome_base, segmentos):
    """Transcreve todos os segmentos com barra de progresso e salva incrementalmente."""
    print(f"\n🎤 Iniciando transcrição completa de {len(segmentos)} segmentos...")
    print("=" * 60)

    # Cria os arquivos de transcrição no início
    nome_arquivo_completo = f"{nome_base}_transcricao_completa.txt"
    caminho_completo = os.path.join(pasta_saida, nome_arquivo_completo)
    nome_detalhado = f"{nome_base}_transcricao_detalhada.txt"
    caminho_detalhado = os.path.join(pasta_saida, nome_detalhado)

    # Inicializa os arquivos com cabeçalho
    with open(caminho_completo, 'w', encoding='utf-8') as f:
        f.write("🎵 TRANSCRIÇÃO COMPLETA DO ÁUDIO (ATUALIZANDO...)\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Arquivo original: {arquivo_entrada}\n")
        f.write(f"Total de segmentos: {len(segmentos)}\n")
        f.write(f"Modelo usado: faster-whisper\n")
        f.write(f"Status: Processando segmentos...\n\n")
        f.write("=" * 50 + "\n\n")

    transcrições = []
    segmentos_info = []

    # Barra de progresso
    with tqdm(total=len(segmentos), desc="🎵 Transcrevendo", unit="segmento") as pbar:
        for i, (segmento, duracao) in enumerate(segmentos, 1):
            # Salva o segmento como WAV
            nome_arquivo = f"{nome_base}_parte_{i:02d}.wav"
            caminho_wav = os.path.join(pasta_saida, nome_arquivo)
            sf.write(caminho_wav, segmento, 48000)  # Usa sample rate padrão

            # Transcreve com faster-whisper
            print(f"\n🔄 Processando segmento {i:02d}/{len(segmentos)}...")
            segments, info = modelo_whisper.transcribe(caminho_wav, language="pt")
            texto_transcrito = " ".join([seg.text.strip() for seg in segments])

            if texto_transcrito:
                # Adiciona timestamp aproximado
                timestamp = f"[{i:02d}] {texto_transcrito}"
                transcrições.append(timestamp)
                segmentos_info.append({
                    'numero': i,
                    'duracao': duracao,
                    'texto': texto_transcrito,
                    'timestamp': timestamp
                })
                print(f"✅ Segmento {i:02d}: {texto_transcrito[:100]}...")
            else:
                print(f"⚠️ Segmento {i:02d}: Sem transcrição detectada")

            # Remove o arquivo WAV temporário
            if os.path.exists(caminho_wav):
                os.remove(caminho_wav)

            # Atualiza arquivo de transcrição incrementalmente
            transcricao_completa = "\n\n".join(transcrições)
            with open(caminho_completo, 'w', encoding='utf-8') as f:
                f.write("🎵 TRANSCRIÇÃO COMPLETA DO ÁUDIO (ATUALIZANDO...)\n")
                f.write("=" * 50 + "\n\n")
                f.write(f"Arquivo original: {arquivo_entrada}\n")
                f.write(f"Total de segmentos: {len(segmentos)}\n")
                f.write(f"Segmentos processados: {len(transcrições)}\n")
                f.write(f"Modelo usado: faster-whisper\n")
                f.write(f"Status: {len(transcrições)}/{len(segmentos)} segmentos transcritos\n\n")
                f.write("=" * 50 + "\n\n")
                f.write(transcricao_completa)

            pbar.update(1)

    # Atualização final com informações completas
    duracao_total = sum(s['duracao'] for s in segmentos_info)
    with open(caminho_completo, 'w', encoding='utf-8') as f:
        f.write("🎵 TRANSCRIÇÃO COMPLETA DO ÁUDIO\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Arquivo original: {arquivo_entrada}\n")
        f.write(f"Total de segmentos: {len(segmentos)}\n")
        f.write(f"Duração total: {duracao_total:.1f} segundos\n")
        f.write(f"Modelo usado: faster-whisper\n")
        f.write(f"Status: ✅ COMPLETO - {len(transcrições)}/{len(segmentos)} segmentos transcritos\n\n")
        f.write("=" * 50 + "\n\n")
        f.write(transcricao_completa)

    # Salva arquivo detalhado final
    with open(caminho_detalhado, 'w', encoding='utf-8') as f:
        f.write("🎵 TRANSCRIÇÃO DETALHADA DO ÁUDIO\n")
        f.write("=" * 60 + "\n\n")
        for info in segmentos_info:
            f.write(f"SEGMENTO {info['numero']:02d}\n")
            f.write("-" * 30 + "\n")
            f.write(f"Duração: {info['duracao']:.1f} segundos\n")
            f.write(f"Texto: {info['texto']}\n\n")

    print(f"\n🎉 Transcrição completa finalizada!")
    print(f"📄 Arquivo principal: {nome_arquivo_completo}")
    print(f"📄 Arquivo detalhado: {nome_detalhado}")
    print(f"📊 Total de segmentos processados: {len(segmentos)}")

    return True


def transcrever_com_diarizacao(arquivo_entrada, modelo_whisper, pipeline_diarizacao, pasta_saida, nome_base):
    """
    Transcreve um arquivo de áudio com identificação de falantes.

    Args:
        arquivo_entrada: Caminho do arquivo de áudio
        modelo_whisper: Modelo faster-whisper carregado
        pipeline_diarizacao: Pipeline Pyannote carregado
        pasta_saida: Pasta onde salvar os resultados
        nome_base: Nome base para os arquivos

    Returns:
        True se sucesso, False caso contrário
    """
    print(f"\n🎤 Iniciando transcrição com identificação de falantes...")
    print("=" * 60)

    # Arquivos de saída
    nome_arquivo_completo = f"{nome_base}_transcricao_com_falantes.txt"
    caminho_completo = os.path.join(pasta_saida, nome_arquivo_completo)
    nome_detalhado = f"{nome_base}_transcricao_detalhada_falantes.txt"
    caminho_detalhado = os.path.join(pasta_saida, nome_detalhado)

    try:
        # Passo 1: Diarização
        print("\n👥 Passo 1/3: Identificando falantes...")
        segmentos_diarizacao = diarizar_audio(arquivo_entrada, pipeline_diarizacao)

        # Mapeia para nomes amigáveis
        segmentos_diarizacao, mapeamento = mapear_falantes_para_nomes(segmentos_diarizacao)
        print(f"✅ {len(mapeamento)} falantes identificados: {', '.join(mapeamento.values())}")

        # Passo 2: Transcrição com timestamps
        print("\n📝 Passo 2/3: Transcrevendo áudio...")
        segments, info = modelo_whisper.transcribe(arquivo_entrada, language="pt")

        # Coleta segmentos de transcrição com timestamps
        segmentos_transcricao = []
        for seg in segments:
            if seg.text.strip():
                segmentos_transcricao.append({
                    'inicio': seg.start,
                    'fim': seg.end,
                    'texto': seg.text.strip()
                })
        print(f"✅ {len(segmentos_transcricao)} segmentos de texto transcritos")

        # Passo 3: Combinar diarização + transcrição
        print("\n🔗 Passo 3/3: Associando texto aos falantes...")
        segmentos_combinados = combinar_diarizacao_transcricao(
            segmentos_diarizacao,
            segmentos_transcricao
        )

        # Formata transcrição
        transcricao_formatada = formatar_transcricao_com_falantes(
            segmentos_combinados,
            incluir_timestamps=False
        )

        # Cria resumo de falantes
        resumo = criar_resumo_falantes(segmentos_combinados)

        # Salva arquivo completo
        with open(caminho_completo, 'w', encoding='utf-8') as f:
            f.write("🎵 TRANSCRIÇÃO COM IDENTIFICAÇÃO DE FALANTES\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Arquivo original: {arquivo_entrada}\n")
            f.write(f"Falantes identificados: {len(mapeamento)}\n")

            # Estatísticas por falante
            f.write("\n📊 ESTATÍSTICAS POR FALANTE:\n")
            f.write("-" * 30 + "\n")
            for falante, stats in resumo.items():
                tempo_min = stats['tempo_total'] / 60
                f.write(f"  {falante}: {stats['num_falas']} falas ({tempo_min:.1f} min)\n")

            f.write("\n" + "=" * 50 + "\n\n")
            f.write("📄 TRANSCRIÇÃO:\n\n")
            f.write(transcricao_formatada)

        # Salva arquivo detalhado
        with open(caminho_detalhado, 'w', encoding='utf-8') as f:
            f.write("🎵 TRANSCRIÇÃO DETALHADA COM FALANTES\n")
            f.write("=" * 60 + "\n\n")

            for i, seg in enumerate(segmentos_combinados, 1):
                f.write(f"SEGMENTO {i:02d}\n")
                f.write("-" * 30 + "\n")
                f.write(f"Tempo: {seg['inicio']:.1f}s - {seg['fim']:.1f}s\n")
                f.write(f"Falante: {seg.get('falante', 'DESCONHECIDO')}\n")
                f.write(f"Texto: {seg['texto']}\n\n")

        print(f"\n🎉 Transcrição com diarização finalizada!")
        print(f"📄 Arquivo principal: {nome_arquivo_completo}")
        print(f"📄 Arquivo detalhado: {nome_detalhado}")
        print(f"👥 Falantes identificados: {len(mapeamento)}")

        # Mostra preview da transcrição
        print("\n📝 Preview da transcrição:")
        print("-" * 40)
        linhas = transcricao_formatada.split('\n')[:10]
        for linha in linhas:
            if linha.strip():
                print(linha)
        if len(transcricao_formatada.split('\n')) > 10:
            print("...")

        return True

    except Exception as e:
        print(f"❌ Erro na transcrição com diarização: {e}")
        import traceback
        traceback.print_exc()
        return False


def dividir_e_transcrever_completa(arquivo_entrada, duracao_segmento_min=4, modelo_whisper=None):
    """Divide um arquivo de áudio e transcreve tudo em um único arquivo com barra de progresso."""
    try:
        print(f"🎵 Carregando arquivo: {arquivo_entrada}")

        # Carrega o arquivo de áudio
        audio_data, sample_rate = librosa.load(arquivo_entrada, sr=None)

        # Informações do arquivo
        duracao_total_segundos = len(audio_data) / sample_rate
        duracao_total_minutos = duracao_total_segundos / 60

        print(f"📊 Taxa de amostragem: {sample_rate} Hz")
        print(f"📊 Duração total: {duracao_total_minutos:.2f} minutos")
        print(f"📊 Duração total: {duracao_total_segundos:.2f} segundos")

        # Cria a pasta de saída
        pasta_saida = criar_pasta_saida(arquivo_entrada)
        nome_base = Path(arquivo_entrada).stem

        # Calcula a duração de cada segmento em amostras
        duracao_segmento_amostras = int(duracao_segmento_min * 60 * sample_rate)

        # Coleta todos os segmentos
        segmentos = []
        num_segmentos = int(len(audio_data) / duracao_segmento_amostras) + 1

        print(f"📁 Preparando {num_segmentos} segmentos de {duracao_segmento_min} minutos cada")
        print(f"📁 Arquivos serão salvos em formato WAV para melhor transcrição")

        for i in range(num_segmentos):
            inicio_amostra = i * duracao_segmento_amostras
            fim_amostra = min((i + 1) * duracao_segmento_amostras, len(audio_data))

            # Extrai o segmento
            segmento = audio_data[inicio_amostra:fim_amostra]
            duracao_segmento = len(segmento) / sample_rate

            segmentos.append((segmento, duracao_segmento))

        # Transcreve todos os segmentos com barra de progresso
        if modelo_whisper is None:
            print("❌ Modelo Whisper necessário para transcrição completa")
            return False

        sucesso = transcrever_completa_com_progresso(arquivo_entrada, modelo_whisper,
                                                   pasta_saida, nome_base, segmentos)

        if sucesso:
            print(f"\n🎉 Processo completo finalizado!")
            print(f"📁 Todos os arquivos salvos em: {pasta_saida}")
        return sucesso

    except Exception as e:
        print(f"❌ Erro no processamento: {str(e)}")
        return False

def dividir_audio(arquivo_entrada, duracao_segmento_min=4, transcrever=False, apenas_transcrever=False, modelo_whisper=None):
    """
    Divide um arquivo de áudio em segmentos menores e opcionalmente transcreve.
    
    Args:
        arquivo_entrada (str): Caminho para o arquivo de áudio
        duracao_segmento_min (int): Duração de cada segmento em minutos
        transcrever (bool): Se deve transcrever cada segmento
        apenas_transcrever (bool): Se deve apenas transcrever sem dividir
        modelo_whisper: Modelo Whisper carregado
    """
    try:
        print(f"🎵 Carregando arquivo: {arquivo_entrada}")
        
        # Carrega o arquivo de áudio
        audio_data, sample_rate = librosa.load(arquivo_entrada, sr=None)
        
        # Informações do arquivo
        duracao_total_segundos = len(audio_data) / sample_rate
        duracao_total_minutos = duracao_total_segundos / 60
        
        print(f"📊 Taxa de amostragem: {sample_rate} Hz")
        print(f"📊 Duração total: {duracao_total_minutos:.2f} minutos")
        print(f"📊 Duração total: {duracao_total_segundos:.2f} segundos")
        
        # Cria a pasta de saída
        pasta_saida = criar_pasta_saida(arquivo_entrada)
        
        # Se apenas transcrever, faz isso e retorna
        if apenas_transcrever:
            if modelo_whisper is None:
                print("❌ Modelo Whisper necessário para transcrição")
                return False
            
            print("🎤 Transcrevendo arquivo completo...")
            nome_base = Path(arquivo_entrada).stem
            sucesso = transcrever_audio(arquivo_entrada, modelo_whisper, pasta_saida, nome_base)
            
            if sucesso:
                print(f"\n🎉 Transcrição concluída! Arquivo salvo em '{pasta_saida}'")
            return sucesso
        
        # Calcula a duração de cada segmento em amostras
        duracao_segmento_amostras = int(duracao_segmento_min * 60 * sample_rate)
        
        # Calcula quantos segmentos serão criados
        num_segmentos = int(len(audio_data) / duracao_segmento_amostras) + 1
        
        print(f"📁 Criando {num_segmentos} segmentos de {duracao_segmento_min} minutos cada")
        print(f"📁 Salvando em: {pasta_saida}/")
        
        # Divide o áudio em segmentos
        for i in range(num_segmentos):
            inicio_amostra = i * duracao_segmento_amostras
            fim_amostra = min((i + 1) * duracao_segmento_amostras, len(audio_data))
            
            # Extrai o segmento
            segmento = audio_data[inicio_amostra:fim_amostra]
            
            # Nome do arquivo de saída
            nome_base = Path(arquivo_entrada).stem
            extensao = Path(arquivo_entrada).suffix
            
            # Sempre salvar como M4A para manter consistência
            extensao_saida = '.m4a'
            nome_arquivo = f"{nome_base}_parte_{i+1:02d}{extensao_saida}"
            caminho_saida = os.path.join(pasta_saida, nome_arquivo)
            
            # Converter numpy array para AudioSegment e salvar como M4A
            # Primeiro, normalizar o áudio para o formato correto
            if segmento.dtype != np.float32:
                segmento = segmento.astype(np.float32)
            
            # Converter para AudioSegment
            audio_segment = AudioSegment(
                segmento.tobytes(),
                frame_rate=sample_rate,
                sample_width=4,  # 32-bit float
                channels=1 if len(segmento.shape) == 1 else segmento.shape[1]
            )
            
            # Salvar como M4A
            audio_segment.export(caminho_saida, format="mp4")
            
            # Informações do segmento
            duracao_segmento_atual = len(segmento) / sample_rate
            print(f"✓ Parte {i+1:02d}: {nome_arquivo} ({duracao_segmento_atual:.1f}s)")
            
            # Transcrever se solicitado
            if transcrever and modelo_whisper is not None:
                # Para transcrição, usa o segmento numpy diretamente (mais confiável)
                caminho_wav = caminho_saida.replace('.m4a', '.wav')
                sf.write(caminho_wav, segmento, sample_rate)
                transcrever_audio(caminho_wav, modelo_whisper, pasta_saida, nome_base, i+1)
        
        print(f"\n🎉 Divisão concluída! {num_segmentos} arquivos criados em '{pasta_saida}'")
        
    except FileNotFoundError:
        print(f"❌ Erro: Arquivo não encontrado: {arquivo_entrada}")
        return False
    except Exception as e:
        print(f"❌ Erro ao processar o arquivo: {str(e)}")
        return False
    
    return True

def main():
    """Função principal do script."""
    print("🎵 Divisor de Arquivos de Áudio com Transcrição e Diarização")
    print("=" * 60)

    # Configura argumentos de linha de comando
    parser = argparse.ArgumentParser(description='Divide arquivos de áudio, transcreve com IA e identifica falantes')
    parser.add_argument('arquivo', help='Arquivo de áudio para processar')
    parser.add_argument('--transcrever', action='store_true', help='Transcrever cada segmento individualmente')
    parser.add_argument('--apenas-transcrever', action='store_true', help='Apenas transcrever arquivo completo')
    parser.add_argument('--transcrever-completa', action='store_true', help='Dividir e transcrever tudo em um arquivo único')
    parser.add_argument('--diarizar', action='store_true', help='Identificar falantes (requer token HF no .env)')
    parser.add_argument('--modelo', default='base',
                       choices=['tiny', 'base', 'small', 'medium', 'large', 'large-v1', 'large-v2', 'large-v3'],
                       help='Modelo Whisper a usar (padrão: base). Versões large: v1, v2, v3 (v3 é o mais recente)')
    parser.add_argument('--segmentos', type=int, default=4, help='Duração de cada segmento em minutos (padrão: 4 min/segmento)')

    args = parser.parse_args()

    # Verifica dependências
    if not verificar_dependencias():
        sys.exit(1)

    arquivo_entrada = args.arquivo

    # Verifica se o arquivo existe
    if not os.path.exists(arquivo_entrada):
        print(f"❌ Erro: Arquivo não encontrado: {arquivo_entrada}")
        sys.exit(1)

    # Verifica se é um arquivo de áudio
    extensoes_validas = ['.mp3', '.wav', '.m4a', '.aac', '.flac', '.ogg', '.wma']
    extensao_arquivo = Path(arquivo_entrada).suffix.lower()

    if extensao_arquivo not in extensoes_validas:
        print(f"⚠️  Aviso: Extensão '{extensao_arquivo}' pode não ser suportada.")
        print(f"   Extensões recomendadas: {', '.join(extensoes_validas)}")

    print(f"\n🎯 Processando: {arquivo_entrada}")
    print("-" * 40)

    # Verifica token HF se diarização solicitada
    pipeline_diarizacao = None
    if args.diarizar:
        if not verificar_token_configurado():
            print("❌ Token do Hugging Face não configurado!")
            print("   Crie um arquivo .env com: HF_TOKEN=seu_token")
            print("   Obtenha o token em: https://huggingface.co/settings/tokens")
            sys.exit(1)

        print("🔐 Token HF configurado. Carregando modelo de diarização...")
        try:
            pipeline_diarizacao = carregar_pipeline_diarizacao()
        except Exception as e:
            print(f"❌ Erro ao carregar pipeline de diarização: {e}")
            sys.exit(1)

    # Carrega modelo Whisper se necessário
    modelo_whisper = None
    if args.transcrever or args.apenas_transcrever or args.transcrever_completa or args.diarizar:
        modelo_whisper = carregar_modelo_whisper(args.modelo)
        if modelo_whisper is None:
            print("❌ Não foi possível carregar o modelo Whisper")
            sys.exit(1)

    # Executa a operação solicitada
    if args.diarizar:
        # Transcrição com identificação de falantes
        pasta_saida = criar_pasta_saida(arquivo_entrada)
        nome_base = Path(arquivo_entrada).stem
        sucesso = transcrever_com_diarizacao(
            arquivo_entrada,
            modelo_whisper,
            pipeline_diarizacao,
            pasta_saida,
            nome_base
        )
    elif args.transcrever_completa:
        # Dividir e transcrever tudo em um arquivo
        sucesso = dividir_e_transcrever_completa(arquivo_entrada, args.segmentos, modelo_whisper)
    else:
        sucesso = dividir_audio(arquivo_entrada, duracao_segmento_min=args.segmentos,
                               transcrever=args.transcrever,
                               apenas_transcrever=args.apenas_transcrever,
                               modelo_whisper=modelo_whisper)

    if sucesso:
        print("\n✅ Processo concluído com sucesso!")
    else:
        print("\n❌ Processo falhou!")
        sys.exit(1)

if __name__ == "__main__":
    main()