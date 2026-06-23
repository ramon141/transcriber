import streamlit as st

from ui.helpers import section_header, stepper
from ui.state import guard_arquivo, wizard_nav
from audio_processor import obter_info_modelo
from diarization import verificar_token_configurado


def render() -> None:
    guard_arquivo()
    stepper(2)
    section_header(
        "⚙️ Configurações de transcrição",
        "Escolha o modelo, duração dos segmentos e se deve identificar falantes.",
    )

    modelo_nome = _secao_modelo()
    duracao_segmentos = _secao_segmentos()
    diarizar = _secao_diarizacao()
    _navegacao(modelo_nome, duracao_segmentos, diarizar)


def _secao_modelo() -> str:
    st.subheader("Modelo Whisper")

    modelo_nome: str = st.select_slider(
        "Modelo",
        options=["tiny", "base", "small", "medium", "large", "large-v1", "large-v2", "large-v3"],
        value=st.session_state.cfg_modelo_nome,
        help="large-v3 é o mais preciso; tiny é o mais rápido.",
    )

    info = obter_info_modelo(modelo_nome)
    col_q, col_v, col_t = st.columns(3)
    with col_q:
        st.metric("Qualidade", info["qualidade"])
    with col_v:
        st.metric("Velocidade", info["velocidade"])
    with col_t:
        st.metric("Tempo estimado", info["tempo_estimado"])

    st.caption(f"_{info['descricao']}_")
    st.divider()
    return modelo_nome


def _secao_segmentos() -> int:
    st.subheader("Divisão de segmentos")

    duracao: int = st.number_input(
        "Duração de cada segmento (minutos)",
        min_value=1,
        max_value=10,
        value=st.session_state.cfg_duracao_segmentos,
        help="Segmentos menores usam menos memória e permitem retomar de onde parou.",
    )

    st.divider()
    return int(duracao)


def _secao_diarizacao() -> bool:
    st.subheader("Identificação de falantes (diarização)")

    token_configurado = verificar_token_configurado()
    diarizar: bool = st.checkbox(
        "Identificar quem fala em cada trecho",
        value=st.session_state.cfg_diarizar if token_configurado else False,
        help="Requer token do Hugging Face configurado no .env",
        disabled=not token_configurado,
    )

    if token_configurado and diarizar:
        st.success("Token HF configurado — diarização disponível.")
        st.caption("Resultado: **[FALANTE 1]** texto... **[FALANTE 2]** outro texto...")
    elif not token_configurado:
        st.warning(
            "**Token HF não configurado.** Para ativar a diarização:\n\n"
            "1. Crie uma conta em [huggingface.co](https://huggingface.co)\n"
            "2. Gere um token em **Settings → Access Tokens**\n"
            "3. Aceite os termos em [pyannote/speaker-diarization-3.1](https://huggingface.co/pyannote/speaker-diarization-3.1)\n"
            "4. Adicione `HF_TOKEN=seu_token` no arquivo `.env`"
        )

    if diarizar:
        st.info("⚠️ A diarização é mais lenta. GPU recomendada para melhor desempenho.")

    return diarizar


def _navegacao(modelo_nome: str, duracao_segmentos: int, diarizar: bool) -> None:
    st.divider()
    col_back, _, col_next = st.columns([1, 4, 1])

    with col_back:
        if st.button("← Voltar", use_container_width=True):
            wizard_nav(1)

    with col_next:
        if st.button("Avançar →", type="primary", use_container_width=True):
            st.session_state.cfg_modelo_nome = modelo_nome
            st.session_state.cfg_duracao_segmentos = duracao_segmentos
            st.session_state.cfg_diarizar = diarizar
            wizard_nav(3)
