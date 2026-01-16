#!/usr/bin/env python3
"""
Módulo de diarização (identificação de falantes) para o Transcriber.
Usa Pyannote.audio para identificar quem fala quando no áudio.
"""

import os
from typing import List, Dict, Optional, Tuple
from dotenv import load_dotenv

# Carrega variáveis de ambiente do arquivo .env
load_dotenv()


def obter_token_huggingface() -> Optional[str]:
    """
    Obtém o token do Hugging Face do arquivo .env.

    Returns:
        Token HF ou None se não configurado
    """
    return os.getenv("HF_TOKEN")


def verificar_token_configurado() -> bool:
    """
    Verifica se o token do Hugging Face está configurado.

    Returns:
        True se configurado, False caso contrário
    """
    token = obter_token_huggingface()
    return token is not None and len(token) > 0


def carregar_pipeline_diarizacao(token: Optional[str] = None):
    """
    Carrega o pipeline de diarização do Pyannote.

    Args:
        token: Token do Hugging Face (opcional, usa .env se não fornecido)

    Returns:
        Pipeline de diarização carregado

    Raises:
        ValueError: Se o token não estiver configurado
        ImportError: Se pyannote.audio não estiver instalado
    """
    try:
        from pyannote.audio import Pipeline
    except ImportError:
        raise ImportError(
            "pyannote.audio não está instalado. "
            "Execute: pip install pyannote.audio"
        )

    # Usa token fornecido ou do .env
    hf_token = token or obter_token_huggingface()

    if not hf_token:
        raise ValueError(
            "Token do Hugging Face não configurado. "
            "Crie um arquivo .env com HF_TOKEN=seu_token ou passe o token como parâmetro. "
            "Obtenha seu token em: https://huggingface.co/settings/tokens"
        )

    print("Carregando pipeline de diarização Pyannote...")
    pipeline = Pipeline.from_pretrained(
        "pyannote/speaker-diarization-3.1",
        token=hf_token
    )

    # Tenta mover para GPU se disponível
    try:
        import torch
        if torch.cuda.is_available():
            pipeline.to(torch.device("cuda"))
            print("Pipeline de diarização usando GPU (CUDA)")
        elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            pipeline.to(torch.device("mps"))
            print("Pipeline de diarização usando GPU (Apple MPS)")
        else:
            print("Pipeline de diarização usando CPU")
    except Exception as e:
        print(f"Aviso: Não foi possível usar GPU para diarização: {e}")

    print("Pipeline de diarização carregado com sucesso!")
    return pipeline


def diarizar_audio(
    arquivo_audio: str,
    pipeline,
    num_falantes: Optional[int] = None
) -> List[Dict]:
    """
    Executa diarização em um arquivo de áudio.

    Args:
        arquivo_audio: Caminho do arquivo de áudio
        pipeline: Pipeline de diarização carregado
        num_falantes: Número de falantes esperado (opcional)

    Returns:
        Lista de segmentos com informações de falante:
        [
            {
                'inicio': 0.0,
                'fim': 5.5,
                'falante': 'SPEAKER_00'
            },
            ...
        ]
    """
    print(f"Executando diarização em: {arquivo_audio}")

    # Configura parâmetros de diarização
    params = {}
    if num_falantes is not None:
        params['num_speakers'] = num_falantes

    # Executa diarização
    resultado = pipeline(arquivo_audio, **params)

    # Converte resultado para lista de segmentos
    # Pyannote 4.x retorna DiarizeOutput com atributo speaker_diarization
    # Versões anteriores retornam Annotation diretamente
    segmentos = []

    # Pyannote 4.x: DiarizeOutput tem atributo speaker_diarization
    if hasattr(resultado, 'speaker_diarization'):
        diarizacao = resultado.speaker_diarization
    else:
        diarizacao = resultado

    # Usa itertracks para extrair segmentos
    if hasattr(diarizacao, 'itertracks'):
        for turn, _, speaker in diarizacao.itertracks(yield_label=True):
            segmentos.append({
                'inicio': turn.start,
                'fim': turn.end,
                'falante': speaker
            })
    else:
        raise ValueError(f"Formato de saída de diarização não reconhecido: {type(diarizacao)}")

    # Ordena por tempo de início
    segmentos.sort(key=lambda x: x['inicio'])

    print(f"Diarização concluída: {len(segmentos)} segmentos identificados")

    # Conta falantes únicos
    falantes_unicos = set(s['falante'] for s in segmentos)
    print(f"Falantes identificados: {len(falantes_unicos)}")

    return segmentos


def mapear_falantes_para_nomes(segmentos: List[Dict]) -> Tuple[List[Dict], Dict[str, str]]:
    """
    Mapeia identificadores de falantes (SPEAKER_00) para nomes amigáveis (FALANTE 1).

    Args:
        segmentos: Lista de segmentos com falantes

    Returns:
        Tupla com (segmentos atualizados, mapeamento de nomes)
    """
    # Coleta falantes únicos na ordem de aparição
    falantes_ordem = []
    for seg in segmentos:
        if seg['falante'] not in falantes_ordem:
            falantes_ordem.append(seg['falante'])

    # Cria mapeamento
    mapeamento = {}
    for i, falante in enumerate(falantes_ordem, 1):
        mapeamento[falante] = f"FALANTE {i}"

    # Atualiza segmentos
    segmentos_atualizados = []
    for seg in segmentos:
        seg_atualizado = seg.copy()
        seg_atualizado['falante'] = mapeamento[seg['falante']]
        segmentos_atualizados.append(seg_atualizado)

    return segmentos_atualizados, mapeamento


def calcular_sobreposicao(inicio1: float, fim1: float, inicio2: float, fim2: float) -> float:
    """Calcula a sobreposição entre dois intervalos de tempo."""
    inicio_comum = max(inicio1, inicio2)
    fim_comum = min(fim1, fim2)
    return max(0, fim_comum - inicio_comum)


def combinar_diarizacao_transcricao(
    segmentos_diarizacao: List[Dict],
    segmentos_transcricao: List[Dict]
) -> List[Dict]:
    """
    Combina resultados de diarização com transcrição.
    Associa cada trecho transcrito ao falante correspondente.
    Usa sobreposição temporal para melhor precisão.

    Args:
        segmentos_diarizacao: Segmentos da diarização com 'inicio', 'fim', 'falante'
        segmentos_transcricao: Segmentos da transcrição com 'inicio', 'fim', 'texto'

    Returns:
        Lista de segmentos combinados:
        [
            {
                'inicio': 0.0,
                'fim': 5.5,
                'falante': 'FALANTE 1',
                'texto': 'Olá, como vai?'
            },
            ...
        ]
    """
    segmentos_combinados = []

    for seg_trans in segmentos_transcricao:
        trans_inicio = seg_trans['inicio']
        trans_fim = seg_trans['fim']

        # Calcula sobreposição com cada segmento de diarização
        melhor_falante = "DESCONHECIDO"
        maior_sobreposicao = 0.0

        for seg_diar in segmentos_diarizacao:
            sobreposicao = calcular_sobreposicao(
                trans_inicio, trans_fim,
                seg_diar['inicio'], seg_diar['fim']
            )
            if sobreposicao > maior_sobreposicao:
                maior_sobreposicao = sobreposicao
                melhor_falante = seg_diar['falante']

        # Se não houve sobreposição, usa o falante mais próximo no tempo
        if melhor_falante == "DESCONHECIDO" and segmentos_diarizacao:
            ponto_medio = (trans_inicio + trans_fim) / 2
            menor_distancia = float('inf')

            for seg_diar in segmentos_diarizacao:
                # Distância do ponto médio ao segmento de diarização
                if ponto_medio < seg_diar['inicio']:
                    distancia = seg_diar['inicio'] - ponto_medio
                elif ponto_medio > seg_diar['fim']:
                    distancia = ponto_medio - seg_diar['fim']
                else:
                    distancia = 0

                if distancia < menor_distancia:
                    menor_distancia = distancia
                    melhor_falante = seg_diar['falante']

        segmentos_combinados.append({
            'inicio': seg_trans['inicio'],
            'fim': seg_trans['fim'],
            'falante': melhor_falante,
            'texto': seg_trans['texto']
        })

    return segmentos_combinados


def formatar_tempo(segundos: float) -> str:
    """
    Formata segundos em formato MM:SS ou HH:MM:SS.

    Args:
        segundos: Tempo em segundos

    Returns:
        String formatada
    """
    horas = int(segundos // 3600)
    minutos = int((segundos % 3600) // 60)
    segs = int(segundos % 60)

    if horas > 0:
        return f"{horas:02d}:{minutos:02d}:{segs:02d}"
    return f"{minutos:02d}:{segs:02d}"


def formatar_transcricao_com_falantes(
    segmentos: List[Dict],
    incluir_timestamps: bool = False
) -> str:
    """
    Formata a transcrição com identificação de falantes.

    Args:
        segmentos: Lista de segmentos com 'falante' e 'texto'
        incluir_timestamps: Se deve incluir timestamps no formato

    Returns:
        String formatada com a transcrição
    """
    linhas = []
    falante_anterior = None

    for seg in segmentos:
        falante = seg['falante']
        texto = seg['texto'].strip()

        if not texto:
            continue

        # Adiciona quebra de linha extra quando muda o falante
        if falante_anterior is not None and falante != falante_anterior:
            linhas.append("")

        if incluir_timestamps:
            timestamp = f"({formatar_tempo(seg['inicio'])} - {formatar_tempo(seg['fim'])})"
            linhas.append(f"[{falante}] {timestamp} {texto}")
        else:
            linhas.append(f"[{falante}] {texto}")

        falante_anterior = falante

    return "\n".join(linhas)


def criar_resumo_falantes(segmentos: List[Dict]) -> Dict:
    """
    Cria um resumo estatístico dos falantes.

    Args:
        segmentos: Lista de segmentos com informações de falante

    Returns:
        Dict com estatísticas por falante
    """
    estatisticas = {}

    for seg in segmentos:
        falante = seg['falante']
        duracao = seg['fim'] - seg['inicio']

        if falante not in estatisticas:
            estatisticas[falante] = {
                'tempo_total': 0.0,
                'num_falas': 0,
                'textos': []
            }

        estatisticas[falante]['tempo_total'] += duracao
        estatisticas[falante]['num_falas'] += 1
        if 'texto' in seg:
            estatisticas[falante]['textos'].append(seg['texto'])

    return estatisticas
