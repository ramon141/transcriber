import streamlit as st

from ui.state import init_state
from supabase_integration import (
    buscar_transcricoes,
    verificar_supabase_configurado,
)

init_state()

st.markdown("## 🔍 Busca Avançada")
st.caption("Pesquise transcrições por nome de arquivo, data ou modelo.")

if not verificar_supabase_configurado():
    st.warning(
        "Supabase não configurado. Adicione `SUPABASE_URL` e `SUPABASE_KEY` no `.env`."
    )
    st.stop()

with st.form("form_busca"):
    col_nome, col_modelo = st.columns(2)
    with col_nome:
        termo: str = st.text_input("Nome do arquivo", placeholder="ex: reuniao.mp3")
    with col_modelo:
        modelo_filtro: str = st.selectbox(
            "Modelo Whisper",
            options=["Todos", "tiny", "base", "small", "medium", "large", "large-v3"],
        )

    col_d1, col_d2 = st.columns(2)
    with col_d1:
        data_inicio = st.date_input("Data início", value=None)
    with col_d2:
        data_fim = st.date_input("Data fim", value=None)

    buscar = st.form_submit_button("🔍 Buscar", type="primary", use_container_width=True)

if not buscar:
    st.stop()

modelo_param = "" if modelo_filtro == "Todos" else modelo_filtro
data_inicio_str = data_inicio.isoformat() if data_inicio else None
data_fim_str = data_fim.isoformat() if data_fim else None

try:
    resultados = buscar_transcricoes(
        termo=termo.strip(),
        modelo=modelo_param,
        data_inicio=data_inicio_str,
        data_fim=data_fim_str,
    )
except Exception as e:
    st.error(f"Erro na busca: {e}")
    st.stop()

st.divider()

if not resultados:
    st.info("Nenhuma transcrição encontrada com os critérios informados.")
    st.stop()

st.success(f"**{len(resultados)} resultado(s)** encontrado(s).")

for reg in resultados:
    nome = reg.get("nome_arquivo", "—")
    modelo = reg.get("modelo_whisper", "—")
    duracao = reg.get("duracao_total", 0)
    diarizado = reg.get("diarizacao_ativada", False)
    criado_em = reg.get("created_at", "")
    data_fmt = criado_em[:10] if criado_em else "—"

    with st.expander(f"🎵 {nome}  ·  {data_fmt}  ·  {modelo}"):
        col_a, col_b = st.columns(2)
        with col_a:
            st.metric("Duração", f"{duracao:.1f} min")
        with col_b:
            st.metric("Diarização", "Sim" if diarizado else "Não")

        transcricao: str = reg.get("transcricao_completa", "")
        if transcricao:
            st.text_area(
                "Transcrição",
                value=transcricao,
                height=200,
                key=f"busca_{reg.get('hash_arquivo', nome)}",
            )

        if st.button(
            "▶️ Carregar nos resultados",
            key=f"busca_load_{reg.get('hash_arquivo', nome)}",
        ):
            st.session_state.results = {
                "sucesso": True,
                "transcricao_completa": transcricao,
                "segmentos": [],
                "segmentos_com_falantes": reg.get("segmentos_com_falantes") or [],
                "resumo_falantes": reg.get("resumo_falantes") or {},
                "diarizacao_ativada": diarizado,
                "arquivo_completo": "",
                "arquivo_detalhado": "",
                "pasta_saida": "",
                "duracao_total": float(duracao),
                "_from_cache": True,
            }
            st.session_state.wizard_step = 4
            st.switch_page("ui/pages/fazer_transcricao.py")
