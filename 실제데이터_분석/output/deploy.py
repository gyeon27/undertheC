from pathlib import Path

import streamlit as st

st.set_page_config(
    page_title="북대서양 자기 이상 탐색기",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    #MainMenu, header, footer {visibility: hidden;}
    .stApp {background: #edf3f7;}
    .block-container {
        max-width: 1540px;
        padding: 0.65rem 1rem 1rem;
    }
    [data-testid="stIFrame"] {
        border: 0;
        border-radius: 18px;
        box-shadow: 0 18px 45px rgba(20, 46, 70, 0.10);
        background: transparent;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

html_path = Path(__file__).with_name("12_ridge_focused_3d_heightmap.html")
st.components.v1.html(
    html_path.read_text(encoding="utf-8"),
    height=1120,
    scrolling=False,
)
