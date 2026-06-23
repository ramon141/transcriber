import streamlit as st


def stepper(passo_atual: int) -> None:
    etapas = ["Arquivo", "Configurações", "Corte", "Processar", "Notion"]
    partes: list[str] = []

    for i, nome in enumerate(etapas, 1):
        if i < passo_atual:
            cls = "step step-done"
            num_html = "✓"
        elif i == passo_atual:
            cls = "step step-active"
            num_html = str(i)
        else:
            cls = "step step-pending"
            num_html = str(i)

        partes.append(
            f'<div class="{cls}">'
            f'<div class="step-num">{num_html}</div>'
            f'<div class="step-label">{nome}</div>'
            f"</div>"
        )
        if i < len(etapas):
            line_cls = "step-line step-line-done" if i < passo_atual else "step-line"
            partes.append(f'<div class="{line_cls}"></div>')

    st.markdown(
        f'<div class="stepper">{"".join(partes)}</div>',
        unsafe_allow_html=True,
    )


def section_header(titulo: str, subtitulo: str = "") -> None:
    html = f'<div class="section-header">{titulo}</div>'
    if subtitulo:
        html += f'<div class="section-sub">{subtitulo}</div>'
    st.markdown(html, unsafe_allow_html=True)


def fmt_mmss(segundos: float) -> str:
    m = int(segundos // 60)
    s = int(segundos % 60)
    return f"{m:02d}:{s:02d}"


def obter_cor_falante(falante: str) -> str:
    cores: dict[str, str] = {
        "FALANTE 1": "#1f77b4",
        "FALANTE 2": "#ff7f0e",
        "FALANTE 3": "#2ca02c",
        "FALANTE 4": "#d62728",
        "FALANTE 5": "#9467bd",
        "FALANTE 6": "#8c564b",
        "FALANTE 7": "#e377c2",
        "FALANTE 8": "#7f7f7f",
        "DESCONHECIDO": "#bcbd22",
    }
    return cores.get(falante, "#17becf")
