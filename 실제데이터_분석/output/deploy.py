import streamlit as st
from pathlib import Path

st.set_page_config(page_title="대서양 중앙해령 3D 지형", layout="wide")

# 예전 버전은 거대한 HTML/JS를 파이썬 문자열(''' ... ''') 안에 통째로 붙여넣었는데,
# 그 안에 포함된 압축된 JS 코드에 "\u" 같은 문자가 섞여 있어서 파이썬이 이걸
# 유니코드 이스케이프로 잘못 해석해 "SyntaxError: truncated \uXXXX escape"가 났었다.
# -> HTML은 파이썬 소스에 넣지 않고, 그냥 파일 그대로 읽어서 그대로 보여주는 방식으로 수정.
html_path = Path(__file__).parent / "12_ridge_focused_3d_heightmap.html"
html_content = html_path.read_text(encoding="utf-8")

st.components.v1.html(html_content, height=1000, scrolling=True)
