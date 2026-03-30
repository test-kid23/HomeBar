"""HomeVisit Pro - 认证与权限模块"""
import streamlit as st
import database as db
from config import PAGE_HOME


def init_session_state():
    """初始化 session_state 中的认证字段"""
    defaults = {
        "logged_in": False,
        "user_id": None,
        "username": "",
        "display_name": "",
        "role": "",
        "current_page": PAGE_HOME,
        "auth_mode": "login",  # 'login' or 'register'
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


def login(username, password):
    """执行登录，成功则设置 session_state

    Returns:
        (bool, str): (是否成功, 提示消息)
    """
    result = db.authenticate_user(username, password)
    if result["success"]:
        user = result["data"]
        st.session_state.logged_in = True
        st.session_state.user_id = user["id"]
        st.session_state.username = user["username"]
        st.session_state.display_name = user["display_name"]
        st.session_state.role = user["role"]
        st.session_state.current_page = PAGE_HOME
        return True, result["message"]
    return False, result["message"]


def logout():
    """退出登录，清除 session_state"""
    keys_to_clear = [
        "logged_in", "user_id", "username", "display_name",
        "role", "current_page", "auth_mode",
    ]
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]
    init_session_state()


def is_admin():
    """当前用户是否是管理员"""
    return st.session_state.get("role") == "admin"


def require_login():
    """检查是否已登录

    Returns:
        bool: True 表示已登录，False 表示未登录 (会渲染登录/注册表单)
    """
    if st.session_state.get("logged_in"):
        return True
    render_auth_page()
    return False


def render_auth_page():
    """渲染登录/注册页面"""
    st.markdown(
        """
        <div style="text-align:center; padding: 2rem 0 1rem;">
            <h1 style="color:#FF8C00; margin-bottom:0.2rem;">🏠 HomeVisit Pro</h1>
            <p style="color:#888; font-size:1.1rem;">家庭预约接待系统</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        tab_login, tab_register = st.tabs(["登录", "注册"])

        with tab_login:
            _render_login_form()

        with tab_register:
            _render_register_form()


def _render_login_form():
    """登录表单"""
    with st.form("login_form", clear_on_submit=False):
        username = st.text_input("用户名", placeholder="请输入用户名", key="login_username")
        password = st.text_input("密码", type="password", placeholder="请输入密码", key="login_password")
        submitted = st.form_submit_button("登 录", use_container_width=True)

    if submitted:
        if not username or not password:
            st.error("请填写用户名和密码")
            return
        with st.spinner("登录中..."):
            ok, msg = login(username.strip(), password)
        if ok:
            st.toast(f"欢迎回来，{st.session_state.display_name}！", icon="✅")
            st.rerun()
        else:
            st.error(msg)


def _render_register_form():
    """注册表单"""
    from utils.validators import (
        validate_username,
        validate_password,
        validate_display_name,
        validate_invitation_code,
    )

    with st.form("register_form", clear_on_submit=False):
        username = st.text_input("用户名", placeholder="3-20位字母/数字/下划线", key="reg_username")
        display_name = st.text_input("昵称", placeholder="您的显示名称", key="reg_display_name")
        password = st.text_input("密码", type="password", placeholder="至少6位", key="reg_password")
        password2 = st.text_input("确认密码", type="password", placeholder="再次输入密码", key="reg_password2")
        invitation_code = st.text_input("邀请码", placeholder="请输入邀请码", key="reg_invite")
        submitted = st.form_submit_button("注 册", use_container_width=True)

    if submitted:
        # 逐项校验
        ok, msg = validate_username(username)
        if not ok:
            st.error(msg)
            return
        ok, msg = validate_display_name(display_name)
        if not ok:
            st.error(msg)
            return
        ok, msg = validate_password(password)
        if not ok:
            st.error(msg)
            return
        if password != password2:
            st.error("两次密码不一致")
            return
        ok, msg = validate_invitation_code(invitation_code)
        if not ok:
            st.error(msg)
            return

        with st.spinner("注册中..."):
            result = db.create_user(username.strip(), password, display_name.strip(), invitation_code.strip())
        if result["success"]:
            st.toast("注册成功，请登录！", icon="✅")
            st.info("注册成功！请切换到「登录」标签页进行登录。")
        else:
            st.error(result["message"])
