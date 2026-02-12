"""
[記憶庫] 負責管理 Session State（對話紀錄、登入狀態等）。
"""
import streamlit as st


def get_api_key():
    return st.session_state.get("api_key")


def set_api_key(value):
    st.session_state["api_key"] = value


def get_use_demo():
    return st.session_state.get("use_demo", False)


def set_use_demo(value):
    st.session_state["use_demo"] = value


def ensure_session_defaults():
    """確保 use_demo 等鍵存在（主程式啟動時呼叫一次）。"""
    if "use_demo" not in st.session_state:
        st.session_state.use_demo = False
