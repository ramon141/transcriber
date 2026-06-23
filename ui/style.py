import streamlit as st

from ui.helpers import fmt_mmss, obter_cor_falante, section_header, stepper

__all__ = ["inject_css", "stepper", "section_header", "fmt_mmss", "obter_cor_falante"]


def inject_css() -> None:
    st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="st-"] {
    font-family: 'Inter', sans-serif !important;
}

.main .block-container {
    padding-top: 1.5rem;
    padding-bottom: 3rem;
    max-width: 1050px;
}

.stepper {
    display: flex;
    align-items: center;
    justify-content: center;
    margin: 0 0 2rem 0;
    padding: 1.2rem 2rem;
    background: white;
    border-radius: 16px;
    box-shadow: 0 2px 16px rgba(0,0,0,0.07);
    border: 1px solid #EAECF0;
}

.step {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 6px;
    min-width: 72px;
}

.step-num {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 700;
    font-size: 14px;
    transition: all 0.3s ease;
}

.step-done .step-num { background: #6C63FF; color: white; }

.step-active .step-num {
    background: linear-gradient(135deg, #667eea, #764ba2);
    color: white;
    box-shadow: 0 4px 16px rgba(108,99,255,0.5);
    transform: scale(1.08);
}

.step-pending .step-num { background: #F1F3F5; color: #ADB5BD; }

.step-label { font-size: 11px; font-weight: 500; color: #9CA3AF; text-align: center; }
.step-active .step-label { color: #6C63FF; font-weight: 700; }
.step-done .step-label { color: #6B7280; font-weight: 600; }

.step-line {
    flex: 1;
    height: 2px;
    background: #E5E7EB;
    margin: 0 4px;
    margin-bottom: 18px;
    min-width: 24px;
}
.step-line-done { background: linear-gradient(90deg, #667eea, #764ba2); }

.card {
    background: white;
    border-radius: 16px;
    padding: 1.5rem 1.8rem;
    box-shadow: 0 2px 16px rgba(0,0,0,0.07);
    border: 1px solid #EAECF0;
    margin-bottom: 1.2rem;
}

.section-header {
    font-size: 1.35rem;
    font-weight: 700;
    color: #111827;
    margin-bottom: 0.3rem;
    letter-spacing: -0.3px;
}
.section-sub {
    font-size: 0.88rem;
    color: #6B7280;
    margin-bottom: 1.5rem;
    line-height: 1.5;
}

.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    font-size: 0.92rem !important;
    padding: 0.55rem 1.4rem !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 4px 14px rgba(108,99,255,0.35) !important;
}
.stButton > button[kind="primary"]:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 20px rgba(108,99,255,0.45) !important;
}
.stButton > button[kind="primary"]:active { transform: translateY(0) !important; }

.stButton > button[kind="secondary"] {
    border-radius: 10px !important;
    font-weight: 500 !important;
    border-color: #D1D5DB !important;
    color: #374151 !important;
}
.stButton > button[kind="secondary"]:hover {
    border-color: #6C63FF !important;
    color: #6C63FF !important;
}

[data-testid="metric-container"] {
    background: white;
    border-radius: 12px;
    padding: 1rem 1.2rem;
    border: 1px solid #EAECF0;
    box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}
[data-testid="metric-container"] [data-testid="stMetricLabel"] {
    font-size: 0.78rem;
    color: #6B7280;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    font-size: 1.2rem;
    font-weight: 700;
    color: #111827;
}

.stProgress > div > div > div > div {
    background: linear-gradient(90deg, #667eea, #764ba2) !important;
    border-radius: 4px;
}

.stTabs [data-baseweb="tab-list"] {
    gap: 4px;
    background: #F9FAFB;
    padding: 4px;
    border-radius: 12px;
    border: 1px solid #EAECF0;
}
.stTabs [data-baseweb="tab"] { border-radius: 8px; font-weight: 500; font-size: 0.88rem; }
.stTabs [aria-selected="true"] {
    background: white !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.1) !important;
}

[data-baseweb="notification"] { border-radius: 10px !important; }
.stSelectbox > div > div { border-radius: 8px !important; }
.stNumberInput > div > div > input { border-radius: 8px !important; }

[data-testid="stFileUploader"] > div {
    border-radius: 14px !important;
    border: 2px dashed #D1D5DB !important;
    transition: border-color 0.2s !important;
}
[data-testid="stFileUploader"] > div:hover { border-color: #6C63FF !important; }

[data-testid="stExpander"] {
    border-radius: 10px !important;
    border: 1px solid #EAECF0 !important;
}

hr { border-color: #E5E7EB !important; margin: 1.2rem 0 !important; }
.stCode { border-radius: 10px !important; }

[data-baseweb="slider"] [data-testid="stTickBarMin"],
[data-baseweb="slider"] [data-testid="stTickBarMax"] {
    font-size: 0.8rem;
    color: #9CA3AF;
}

.info-box {
    background: #EEF2FF;
    border-left: 4px solid #6C63FF;
    border-radius: 8px;
    padding: 0.8rem 1rem;
    margin: 0.8rem 0;
    font-size: 0.9rem;
    color: #3730A3;
}

.success-box {
    background: #ECFDF5;
    border-left: 4px solid #10B981;
    border-radius: 8px;
    padding: 0.8rem 1rem;
    margin: 0.8rem 0;
    font-size: 0.9rem;
    color: #065F46;
}

.speaker-bubble {
    border-radius: 10px;
    padding: 0.6rem 1rem;
    margin: 0.3rem 0;
    font-size: 0.9rem;
    line-height: 1.5;
    background: #F9FAFB;
    border: 1px solid #E5E7EB;
}
</style>
""", unsafe_allow_html=True)
