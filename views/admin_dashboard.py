"""HomeVisit Pro - 管理员后台"""
import streamlit as st
import base64
import database as db
from utils.ui_components import (
    render_page_header, render_dish_card, render_booking_card, render_empty_state
)


def render():
    """渲染管理员后台页面"""
    render_page_header("⚙️ 管理面板", "菜单管理与预约审核")

    tab_menu, tab_bookings = st.tabs(["🍽️ 菜单管理", "📋 预约审核"])

    with tab_menu:
        _render_menu_management()

    with tab_bookings:
        _render_booking_management()


# ============================================================
# 菜单管理
# ============================================================

def _render_menu_management():
    """菜单管理标签页"""

    # 添加/编辑菜品表单
    editing_id = st.session_state.get("admin_editing_dish_id")

    if editing_id:
        _render_dish_form(editing_id)
    else:
        if st.button("➕ 添加新菜品", key="add_dish_btn", use_container_width=True, type="primary"):
            st.session_state.admin_editing_dish_id = "new"
            st.rerun()

    st.divider()

    # 菜品列表
    result = db.get_all_dishes(include_unavailable=True)
    if not result["success"]:
        st.error(result["message"])
        return

    dishes = result["data"]
    if not dishes:
        render_empty_state("🍳", "暂无菜品，点击上方按钮添加")
        return

    cols = st.columns(2)
    for idx, dish in enumerate(dishes):
        with cols[idx % 2]:
            render_dish_card(dish, show_admin_actions=True)


def _render_dish_form(editing_id):
    """菜品添加/编辑表单"""
    is_new = editing_id == "new"
    form_title = "添加新菜品" if is_new else "编辑菜品"

    # 加载现有数据
    existing = {}
    if not is_new:
        result = db.get_dish_by_id(editing_id)
        if result["success"]:
            existing = result["data"]

    st.subheader(form_title)

    with st.form("dish_form", clear_on_submit=False):
        name = st.text_input("菜品名称 *", value=existing.get("name", ""), key="dish_name")
        description = st.text_area(
            "菜品描述", value=existing.get("description", ""), key="dish_desc"
        )
        rating = st.slider(
            "推荐指数", min_value=1, max_value=5,
            value=existing.get("rating", 3), key="dish_rating"
        )
        sort_order = st.number_input(
            "排序权重 (越小越靠前)", min_value=0, max_value=999,
            value=existing.get("sort_order", 0), key="dish_sort"
        )

        # 图片: URL 或 上传
        image_url = st.text_input(
            "图片URL (可选)", value=existing.get("image_url", ""), key="dish_img_url",
            placeholder="输入图片网址，或在下方上传图片",
        )

        uploaded_file = st.file_uploader(
            "或上传图片", type=["jpg", "jpeg", "png", "webp"], key="dish_img_upload"
        )

        col_save, col_cancel = st.columns(2)
        with col_save:
            submitted = st.form_submit_button("保存", use_container_width=True, type="primary")
        with col_cancel:
            cancelled = st.form_submit_button("取消", use_container_width=True)

    if cancelled:
        st.session_state.admin_editing_dish_id = None
        st.rerun()

    if submitted:
        if not name.strip():
            st.error("菜品名称不能为空")
            return

        # 处理上传图片 -> base64
        final_image_url = image_url.strip()
        if uploaded_file is not None:
            # 检查大小 (2MB)
            if uploaded_file.size > 2 * 1024 * 1024:
                st.error("图片大小不超过 2MB")
                return
            img_bytes = uploaded_file.read()
            b64 = base64.b64encode(img_bytes).decode("utf-8")
            mime = uploaded_file.type or "image/jpeg"
            final_image_url = f"data:{mime};base64,{b64}"

        with st.spinner("保存中..."):
            if is_new:
                result = db.create_dish(
                    name=name.strip(),
                    description=description.strip(),
                    image_url=final_image_url,
                    rating=rating,
                    sort_order=sort_order,
                )
            else:
                result = db.update_dish(
                    dish_id=editing_id,
                    name=name.strip(),
                    description=description.strip(),
                    image_url=final_image_url,
                    rating=rating,
                    sort_order=sort_order,
                )

        if result["success"]:
            st.session_state.admin_editing_dish_id = None
            st.toast(result["message"], icon="✅")
            st.rerun()
        else:
            st.error(result["message"])


# ============================================================
# 预约审核
# ============================================================

def _render_booking_management():
    """预约审核标签页"""
    from config import STATUS_PENDING, STATUS_APPROVED, STATUS_REJECTED

    # 状态筛选
    filter_option = st.selectbox(
        "筛选状态",
        ["全部", "待审核", "已通过", "已拒绝"],
        key="admin_booking_filter",
    )

    status_map = {
        "全部": None,
        "待审核": STATUS_PENDING,
        "已通过": STATUS_APPROVED,
        "已拒绝": STATUS_REJECTED,
    }
    status_filter = status_map[filter_option]

    result = db.get_all_bookings(status_filter=status_filter)
    if not result["success"]:
        st.error(result["message"])
        return

    bookings = result["data"]
    if not bookings:
        render_empty_state("📭", "暂无预约记录")
        return

    st.markdown(f"共 **{len(bookings)}** 条预约")
    st.divider()

    for booking in bookings:
        render_booking_card(
            booking,
            show_user_info=True,
            show_admin_actions=True,
        )
