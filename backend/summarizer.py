import subprocess
from typing import Dict, List

MAX_CHARS = 10000
MODELO = "claude-opus-4-8"

PROMPT = """\
Você é um assistente especializado em análise de reuniões. Analise a transcrição abaixo em português com máxima atenção aos detalhes.

Seja EXTREMAMENTE detalhista: não deixe passar nenhum ponto discutido, nenhuma decisão tomada, nenhuma dúvida levantada, nenhuma tarefa mencionada — mesmo que pareça menor.

Estruture a análise com estas seções:
## Pontos Principais
Liste TODOS os assuntos discutidos, com contexto suficiente para entender cada um.

## Decisões Tomadas
Liste todas as decisões, mesmo as informais ou implícitas.

## Dúvidas e Pendências
Liste questões que ficaram em aberto ou que precisam de esclarecimento.

## Próximos Passos
Liste todas as ações mencionadas, quem é responsável (se citado) e prazo (se mencionado).

Transcrição:

{transcricao}"""


def resumir_transcricao(transcricao: str) -> str:
    texto = transcricao[:MAX_CHARS]
    if len(transcricao) > MAX_CHARS:
        texto += "\n\n[... transcrição truncada para resumo ...]"

    prompt = PROMPT.format(transcricao=texto)

    proc = subprocess.run(
        ["claude", "--model", MODELO, "-p", prompt],
        capture_output=True,
        text=True,
        timeout=120,
    )

    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or "Erro ao gerar resumo via Claude CLI")

    return proc.stdout.strip()


PROMPT_ATIVIDADES = """\
Analise a transcrição abaixo e extraia TODAS as tarefas, atividades e compromissos mencionados para cada participante.

Retorne SOMENTE no formato abaixo, sem texto adicional:

FALANTE: [nome real se identificável na transcrição, senão "Falante 1", "Falante 2", etc.]
- tarefa ou atividade identificada
- outra tarefa

FALANTE: [próximo participante]
- tarefa

Se não houver tarefas, responda exatamente: SEM_ATIVIDADES

Transcrição:

{transcricao}"""


def _parsear_atividades(texto: str) -> Dict[str, List[str]]:
    if "SEM_ATIVIDADES" in texto:
        return {}
    resultado: Dict[str, List[str]] = {}
    falante_atual: str | None = None
    for linha in texto.split("\n"):
        linha = linha.strip()
        if linha.startswith("FALANTE:"):
            falante_atual = linha[8:].strip()
            resultado[falante_atual] = []
        elif linha.startswith("- ") and falante_atual:
            tarefa = linha[2:].strip()
            if tarefa:
                resultado[falante_atual].append(tarefa)
    return {k: v for k, v in resultado.items() if v}


def extrair_atividades(transcricao: str) -> Dict[str, List[str]]:
    texto = transcricao[:MAX_CHARS]
    prompt = PROMPT_ATIVIDADES.format(transcricao=texto)

    proc = subprocess.run(
        ["claude", "--model", MODELO, "-p", prompt],
        capture_output=True,
        text=True,
        timeout=120,
    )

    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or "Erro ao extrair atividades via Claude CLI")

    return _parsear_atividades(proc.stdout.strip())
