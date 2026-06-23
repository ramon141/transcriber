import sys
from pathlib import Path

from fastapi import APIRouter, HTTPException

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.models import (  # noqa: E402
    ConexaoAtual,
    ConexaoPayload,
    ConfigStatus,
    IntegracoesAtual,
    IntegracoesPayload,
)
from config_store import (  # noqa: E402
    ChaveConexao,
    ChaveIntegracao,
    conexao_configurada,
    obter_conexao,
    obter_integracao,
    salvar_conexao,
    salvar_integracoes,
    testar_conexao,
)
from diarization import (  # noqa: E402
    validar_token_huggingface,
    verificar_token_configurado,
)
from notion_integration import (  # noqa: E402
    obter_token_notion,
    validar_parent_notion,
    validar_token_notion,
    verificar_notion_configurado,
)

router = APIRouter()


@router.get("/status", response_model=ConfigStatus)
async def status() -> ConfigStatus:
    return ConfigStatus(
        conexao_ok=conexao_configurada(),
        hf_ok=verificar_token_configurado(),
        notion_ok=verificar_notion_configurado(),
    )


@router.get("/conexao", response_model=ConexaoAtual)
async def get_conexao() -> ConexaoAtual:
    return ConexaoAtual(
        supabase_url=obter_conexao(ChaveConexao.SUPABASE_URL) or "",
        supabase_key=obter_conexao(ChaveConexao.SUPABASE_KEY) or "",
        database_url=obter_conexao(ChaveConexao.DATABASE_URL) or "",
    )


@router.post("/conexao", response_model=ConfigStatus)
async def post_conexao(payload: ConexaoPayload) -> ConfigStatus:
    # Campo vazio = manter o valor já salvo (edição sem redigitar segredos).
    url = payload.supabase_url.strip() or (obter_conexao(ChaveConexao.SUPABASE_URL) or "")
    key = payload.supabase_key.strip() or (obter_conexao(ChaveConexao.SUPABASE_KEY) or "")
    db = payload.database_url.strip() or (obter_conexao(ChaveConexao.DATABASE_URL) or "")

    ok, mensagem = testar_conexao(supabase_url=url, supabase_key=key, database_url=db)
    if not ok:
        raise HTTPException(status_code=400, detail=mensagem)

    salvar_conexao(supabase_url=url, supabase_key=key, database_url=db)

    return ConfigStatus(
        conexao_ok=True,
        hf_ok=verificar_token_configurado(),
        notion_ok=verificar_notion_configurado(),
    )


@router.get("/integracoes", response_model=IntegracoesAtual)
async def get_integracoes() -> IntegracoesAtual:
    return IntegracoesAtual(
        hf_token=obter_integracao(ChaveIntegracao.HF_TOKEN) or "",
        notion_token=obter_integracao(ChaveIntegracao.NOTION_TOKEN) or "",
        notion_parent_id=obter_integracao(ChaveIntegracao.NOTION_PARENT_ID) or "",
    )


def _validar_integracoes(payload: IntegracoesPayload) -> dict[str, str]:
    erros: dict[str, str] = {}

    if payload.hf_token:
        erro_hf = validar_token_huggingface(payload.hf_token.strip())
        if erro_hf:
            erros[ChaveIntegracao.HF_TOKEN.value] = erro_hf

    if payload.notion_token:
        erro_token = validar_token_notion(payload.notion_token.strip())
        if erro_token:
            erros[ChaveIntegracao.NOTION_TOKEN.value] = erro_token

    if payload.notion_parent_id:
        token = (payload.notion_token or "").strip() or obter_token_notion()
        if not token:
            erros[ChaveIntegracao.NOTION_PARENT_ID.value] = (
                "Informe o NOTION_TOKEN para validar a página."
            )
        elif ChaveIntegracao.NOTION_TOKEN.value not in erros:
            erro_pai = validar_parent_notion(token, payload.notion_parent_id.strip())
            if erro_pai:
                erros[ChaveIntegracao.NOTION_PARENT_ID.value] = erro_pai

    return erros


@router.post("/integracoes", response_model=ConfigStatus)
async def post_integracoes(payload: IntegracoesPayload) -> ConfigStatus:
    if not conexao_configurada():
        raise HTTPException(
            status_code=503,
            detail="Configure a conexão com o banco antes das integrações.",
        )

    erros = _validar_integracoes(payload)
    if erros:
        raise HTTPException(status_code=422, detail={"campo_erros": erros})

    valores: dict[ChaveIntegracao, str] = {}
    if payload.hf_token:
        valores[ChaveIntegracao.HF_TOKEN] = payload.hf_token.strip()
    if payload.notion_token:
        valores[ChaveIntegracao.NOTION_TOKEN] = payload.notion_token.strip()
    if payload.notion_parent_id:
        valores[ChaveIntegracao.NOTION_PARENT_ID] = payload.notion_parent_id.strip()

    try:
        salvar_integracoes(valores)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

    return ConfigStatus(
        conexao_ok=True,
        hf_ok=verificar_token_configurado(),
        notion_ok=verificar_notion_configurado(),
    )
