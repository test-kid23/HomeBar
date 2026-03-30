"""HomeVisit Pro - 消息中心"""
import streamlit as st
import database as db
from utils.ui_components import render_page_header, render_empty_state


def render():
    """渲染消息中心页面"""
    render_page_header("🔔 消息中心", "查看系统通知和预约审核结果")

    user_id = st.session_state.get("user_id")
    result = db.get_user_messages(user_id)

    if not result["success"]:
        st.error(result["message"])
        return

    messages = result["data"]

    if not messages:
        render_empty_state("📭", "暂无消息")
        return

    # 未读数量
    unread_count = sum(1 for m in messages if not m["is_read"])

    # "全部标记已读"按钮
    if unread_count > 0:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"共 **{len(messages)}** 条消息，**{unread_count}** 条未读")
        with col2:
            if st.button("全部已读", key="mark_all_read", use_container_width=True):
                mark_result = db.mark_all_read(user_id)
                if mark_result["success"]:
                    st.toast("已全部标记为已读", icon="✅")
                    st.rerun()
    else:
        st.markdown(f"共 **{len(messages)}** 条消息，全部已读")

    st.divider()

    # 消息列表
    for msg in messages:
        _render_message_item(msg)


def _render_message_item(msg):
    """渲染单条消息"""
    msg_id = msg["id"]
    is_read = msg["is_read"]
    title = msg["title"]
    content = msg["content"]
    created_at = msg["created_at"]

    # 未读消息高亮
    icon = "📩" if not is_read else "📧"
    bold_start = "**" if not is_read else ""
    bold_end = "**" if not is_read else ""

    with st.expander(f"{icon} {bold_start}{title}{bold_end}　　{created_at}", expanded=False):
        st.markdown(content)

        if not is_read:
            if st.button("标记为已读", key=f"read_msg_{msg_id}", use_container_width=True):
                mark_result = db.mark_message_read(msg_id)
                if mark_result["success"]:
                    st.toast("已标记为已读", icon="✅")
                    st.rerun()
