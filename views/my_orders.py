"""HomeVisit Pro - 我的预约/订单记录"""
import streamlit as st
import database as db
from config import STATUS_PENDING, STATUS_APPROVED, STATUS_REJECTED
from utils.ui_components import render_page_header, render_booking_card, render_empty_state


def render():
    """渲染用户预约记录页面"""
    render_page_header("📋 我的预约", "查看您的所有预约记录和审核状态")

    user_id = st.session_state.get("user_id")
    result = db.get_user_bookings(user_id)

    if not result["success"]:
        st.error(result["message"])
        return

    bookings = result["data"]

    if not bookings:
        render_empty_state("📭", "暂无预约记录，快去预约吧！")
        return

    # 状态过滤标签页
    tab_all, tab_pending, tab_approved, tab_rejected = st.tabs([
        f"全部 ({len(bookings)})",
        f"待审核 ({sum(1 for b in bookings if b['status'] == STATUS_PENDING)})",
        f"已通过 ({sum(1 for b in bookings if b['status'] == STATUS_APPROVED)})",
        f"已拒绝 ({sum(1 for b in bookings if b['status'] == STATUS_REJECTED)})",
    ])

    with tab_all:
        _render_booking_list(bookings)

    with tab_pending:
        filtered = [b for b in bookings if b["status"] == STATUS_PENDING]
        _render_booking_list(filtered, "没有待审核的预约")

    with tab_approved:
        filtered = [b for b in bookings if b["status"] == STATUS_APPROVED]
        _render_booking_list(filtered, "没有已通过的预约")

    with tab_rejected:
        filtered = [b for b in bookings if b["status"] == STATUS_REJECTED]
        _render_booking_list(filtered, "没有已拒绝的预约")


def _render_booking_list(bookings, empty_msg="暂无记录"):
    """渲染预约列表"""
    if not bookings:
        render_empty_state("📭", empty_msg)
        return

    for booking in bookings:
        render_booking_card(booking)
