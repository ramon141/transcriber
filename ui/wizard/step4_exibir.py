import os
import io
import zipfile
from pathlib import Path

import streamlit as st

from ui.helpers import obter_cor_falante
from ui.state import wizard_nav
from ui.types import ResultadoTranscricao


def exibir_resultados(resultados: ResultadoTranscricao) -> None:
    diarizacao: bool = resultados.get("diarizacao_ativada", False)
    resumo: dict = resultados.get("resumo_falantes", {})

    st.success("✅ Transcrição concluída!")
    _metricas_resultado(resultados, resumo, diarizacao)

    if diarizacao:
        tab1, tab2, tab3, tab4 = st.tabs(
            ["📄 Completa", "👥 Por Falante", "📁 Segmentos", "⬇️ Downloads"]
        )
        with tab1:
            _tab_transcricao(resultados, diarizacao)
        with tab2:
            _tab_falantes(resumo)
        with tab3:
            _tab_segmentos(resultados)
        with tab4:
            _tab_downloads(resultados)
    else:
        tab1, tab2, tab3 = st.tabs(["📄 Completa", "📁 Segmentos", "⬇️ Downloads"])
        with tab1:
            _tab_transcricao(resultados, diarizacao)
        with tab2:
            _tab_segmentos(resultados)
        with tab3:
            _tab_downloads(resultados)

    st.divider()
    col_back, _, col_notion = st.columns([1, 4, 1])
    with col_back:
        if st.button("← Voltar", use_container_width=True, key="voltar_pos_resultado"):
            wizard_nav(3)
    with col_notion:
        if st.button("📝 Enviar ao Notion →", type="primary", use_container_width=True):
            wizard_nav(5)


def _metricas_resultado(resultados: ResultadoTranscricao, resumo: dict, diarizacao: bool) -> None:
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Segmentos", len(resultados.get("segmentos", [])))
    with col2:
        st.metric("Duração", f"{resultados.get('duracao_total', 0):.1f} min")
    with col3:
        st.metric("Falantes", len(resumo) if diarizacao else "—")
    with col4:
        pasta = resultados.get("pasta_saida", "")
        st.metric("Pasta", Path(pasta).name if pasta else "—")


def _tab_transcricao(resultados: ResultadoTranscricao, diarizacao: bool) -> None:
    if diarizacao:
        segs_falantes: list = resultados.get("segmentos_com_falantes", [])
        for seg in segs_falantes:
            falante = seg.get("falante", "DESCONHECIDO")
            cor = obter_cor_falante(falante)
            texto = seg.get("texto", "")
            st.markdown(
                f'<div class="speaker-bubble">'
                f'<span style="color:{cor};font-weight:700;">[{falante}]</span> {texto}'
                f"</div>",
                unsafe_allow_html=True,
            )
        if not segs_falantes:
            st.text_area("Texto", value=resultados.get("transcricao_completa", ""), height=400)
    else:
        st.text_area(
            "Texto transcrito",
            value=resultados.get("transcricao_completa", ""),
            height=400,
            help="Selecione tudo (Ctrl+A) e copie (Ctrl+C)",
        )


def _tab_falantes(resumo: dict) -> None:
    if not resumo:
        st.info("Nenhum falante identificado.")
        return

    for falante, stats in resumo.items():
        cor = obter_cor_falante(falante)
        tempo_min = stats.get("tempo_total", 0) / 60
        with st.expander(f"👤 {falante} — {stats.get('num_falas', 0)} falas ({tempo_min:.1f} min)"):
            st.markdown(
                f'<div style="border-left:4px solid {cor};padding-left:12px;">',
                unsafe_allow_html=True,
            )
            for texto in stats.get("textos", []):
                st.write(f"• {texto}")
            st.markdown("</div>", unsafe_allow_html=True)


def _tab_segmentos(resultados: ResultadoTranscricao) -> None:
    for seg in resultados.get("segmentos", []):
        with st.expander(f"🎵 Segmento {seg.get('numero', 0):02d} ({seg.get('duracao', 0):.1f}s)"):
            st.write(seg.get("texto", ""))


def _tab_downloads(resultados: ResultadoTranscricao) -> None:
    arq_completo: str = resultados.get("arquivo_completo", "")
    arq_detalhado: str = resultados.get("arquivo_detalhado", "")
    diarizacao: bool = resultados.get("diarizacao_ativada", False)

    if os.path.exists(arq_completo):
        with open(arq_completo, "r", encoding="utf-8") as f:
            conteudo = f.read()
        label = "📄 Transcrição Completa (com falantes)" if diarizacao else "📄 Transcrição Completa"
        st.download_button(f"{label} (.txt)", data=conteudo, file_name=Path(arq_completo).name, mime="text/plain")

    if os.path.exists(arq_detalhado):
        with open(arq_detalhado, "r", encoding="utf-8") as f:
            conteudo_det = f.read()
        st.download_button(
            "📋 Transcrição Detalhada (.txt)",
            data=conteudo_det,
            file_name=Path(arq_detalhado).name,
            mime="text/plain",
        )

    st.divider()
    pasta_saida: str = resultados.get("pasta_saida", "")

    if pasta_saida and os.path.exists(pasta_saida):
        if st.button("📦 Criar ZIP com tudo", type="primary"):
            with st.spinner("Criando ZIP..."):
                zip_data = _criar_zip(pasta_saida)
            st.download_button(
                "⬇️ Baixar tudo (áudios + transcrições)",
                data=zip_data,
                file_name=f"{Path(pasta_saida).name}.zip",
                mime="application/zip",
            )
    else:
        st.caption("📦 ZIP não disponível para resultados carregados do cache.")


def _criar_zip(pasta_saida: str) -> bytes:
    buf = io.BytesIO()
    pasta = Path(pasta_saida)
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for arq in pasta.rglob("*"):
            if arq.is_file():
                zf.write(arq, arq.relative_to(pasta.parent))
    buf.seek(0)
    return buf.getvalue()
