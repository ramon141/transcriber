import streamlit as st


def inject_sidebar_css() -> None:
    st.markdown("""
<style>
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #1E1B4B 0%, #2D2B69 100%) !important;
    border-right: 1px solid rgba(255,255,255,0.08) !important;
}

section[data-testid="stSidebar"] > div:first-child {
    padding-top: 0 !important;
    display: flex !important;
    flex-direction: column !important;
}

section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] {
    order: -1 !important;
    padding-top: 0 !important;
    flex-shrink: 0 !important;
}

.sidebar-brand {
    padding: 1.4rem 1.2rem 1.1rem;
    border-bottom: 1px solid rgba(255,255,255,0.1);
    margin-bottom: 0.3rem;
}

.sidebar-brand .brand-title {
    color: white !important;
    font-size: 1.2rem !important;
    font-weight: 700 !important;
    margin: 0 !important;
    letter-spacing: -0.2px;
}

.sidebar-brand .brand-sub {
    color: rgba(255,255,255,0.45) !important;
    font-size: 0.7rem !important;
    margin-top: 0.25rem;
    line-height: 1.4;
}

[data-testid="stSidebarNav"] ul {
    padding: 0 0.6rem;
    gap: 2px;
    list-style: none;
}

[data-testid="stSidebarNav"] li a,
section[data-testid="stSidebar"] nav a {
    border-radius: 10px !important;
    padding: 0.55rem 0.9rem !important;
    color: rgba(255,255,255,0.65) !important;
    font-weight: 500 !important;
    font-size: 0.875rem !important;
    transition: all 0.2s ease !important;
    text-decoration: none !important;
    display: flex !important;
    align-items: center !important;
    gap: 0.5rem !important;
}

[data-testid="stSidebarNav"] li a:hover,
section[data-testid="stSidebar"] nav a:hover {
    background: rgba(255,255,255,0.09) !important;
    color: white !important;
}

[data-testid="stSidebarNav"] li a[aria-current="page"],
section[data-testid="stSidebar"] nav a[aria-current="page"] {
    background: linear-gradient(135deg, #667eea, #764ba2) !important;
    color: white !important;
    box-shadow: 0 4px 14px rgba(108,99,255,0.3) !important;
}

section[data-testid="stSidebar"] hr {
    border-color: rgba(255,255,255,0.1) !important;
    margin: 0.4rem 1rem !important;
}

section[data-testid="stSidebar"] p {
    color: rgba(255,255,255,0.35) !important;
    font-size: 0.68rem !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 1.1px !important;
}
</style>
""", unsafe_allow_html=True)
