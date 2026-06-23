import subprocess

MAX_CHARS = 10000
MODELO = "claude-opus-4-8"

PROMPT = """\
Você é um assistente especializado em análise de reuniões. Resuma a transcrição abaixo em português.

Estruture o resumo com estas seções:
## Pontos Principais
## Decisões Tomadas
## Próximos Passos

Seja objetivo e conciso. Transcrição:

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
