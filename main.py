"""HomeVisit Pro - 主入口
仅负责页面配置、数据库初始化、认证门控、CSS注入和路由分发。
"""
import streamlit as st
from config import APP_TITLE, APP_ICON, PAGE_HOME, PAGE_BOOKING, PAGE_MY_ORDERS, PAGE_MESSAGES, PAGE_ADMIN

# ---- 页面配置 (必须是第一个 Streamlit 调用) ----
st.set_page_config(
    page_title=APP_TITLE,
    page_icon=APP_ICON,
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---- 数据库初始化 ----
from database import init_db
init_db()

# ---- Session 初始化 ----
from utils.auth import init_session_state, require_login
init_session_state()

# ---- 注入自定义 CSS ----
from utils.ui_components import apply_custom_css, render_sidebar
apply_custom_css()

# ---- 认证门控 ----
if not require_login():
    st.stop()

# ---- 侧边栏导航 ----
render_sidebar()

# ---- 页面路由 ----
current_page = st.session_state.get("current_page", PAGE_HOME)

if current_page == PAGE_HOME:
    from views.home import render
elif current_page == PAGE_BOOKING:
    from views.booking import render
elif current_page == PAGE_MY_ORDERS:
    from views.my_orders import render
elif current_page == PAGE_MESSAGES:
    from views.messages import render
elif current_page == PAGE_ADMIN:
    from views.admin_dashboard import render
else:
    from views.home import render

render()
