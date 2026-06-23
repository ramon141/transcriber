import streamlit as st

from ui.state import init_state
from supabase_integration import (
    listar_transcricoes,
    verificar_supabase_configurado,
)

init_state()

st.markdown("## 📋 Listagem de Transcrições")
st.caption("Todas as transcrições salvas no Supabase.")

if not verificar_supabase_configurado():
    st.warning(
        "Supabase não configurado. Adicione `SUPABASE_URL` e `SUPABASE_KEY` no `.env`."
    )
    st.stop()

col_refresh, _ = st.columns([1, 5])
with col_refresh:
    if st.button("🔄 Atualizar", use_container_width=True):
        st.cache_data.clear()

try:
    registros = listar_transcricoes(limite=100)
except Exception as e:
    st.error(f"Erro ao carregar transcrições: {e}")
    st.stop()

if not registros:
    st.info("Nenhuma transcrição encontrada.")
    st.stop()

st.divider()

col_q1, col_q2, col_q3 = st.columns(3)
with col_q1:
    st.metric("Total", len(registros))
with col_q2:
    com_diar = sum(1 for r in registros if r.get("diarizacao_ativada"))
    st.metric("Com diarização", com_diar)
with col_q3:
    modelos = {r.get("modelo_whisper", "?") for r in registros}
    st.metric("Modelos usados", len(modelos))

st.divider()

for registro in registros:
    nome = registro.get("nome_arquivo", "—")
    modelo = registro.get("modelo_whisper", "—")
    duracao = registro.get("duracao_total", 0)
    diarizado = registro.get("diarizacao_ativada", False)
    criado_em = registro.get("created_at", "")

    badge_diar = "✅ Diarizado" if diarizado else "📝 Simples"
    data_fmt = criado_em[:10] if criado_em else "—"

    with st.expander(f"🎵 {nome}  ·  {data_fmt}"):
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.metric("Modelo", modelo)
        with col_b:
            st.metric("Duração", f"{duracao:.1f} min")
        with col_c:
            st.metric("Tipo", badge_diar)

        transcricao: str = registro.get("transcricao_completa", "")
        if transcricao:
            st.text_area(
                "Transcrição completa",
                value=transcricao,
                height=200,
                key=f"txt_{registro.get('hash_arquivo', nome)}",
            )

        if st.button(
            "▶️ Carregar nos resultados",
            key=f"load_{registro.get('hash_arquivo', nome)}",
        ):
            st.session_state.results = {
                "sucesso": True,
                "transcricao_completa": transcricao,
                "segmentos": [],
                "segmentos_com_falantes": registro.get("segmentos_com_falantes") or [],
                "resumo_falantes": registro.get("resumo_falantes") or {},
                "diarizacao_ativada": diarizado,
                "arquivo_completo": "",
                "arquivo_detalhado": "",
                "pasta_saida": "",
                "duracao_total": float(duracao),
                "_from_cache": True,
            }
            st.session_state.wizard_step = 4
            st.switch_page("ui/pages/fazer_transcricao.py")
