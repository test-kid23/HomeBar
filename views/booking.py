"""HomeVisit Pro - 预约提交页"""
import streamlit as st
from datetime import date, timedelta
import database as db
from config import PAGE_MY_ORDERS, MAX_GUEST_COUNT, MAX_DISH_QUANTITY
from utils.ui_components import render_page_header, render_success_page, render_star_rating
from utils.validators import validate_booking_date, validate_guest_count, validate_dish_quantities


def render():
    """渲染预约下单页面"""
    # 检查是否刚提交成功 (flag-then-rerun 模式)
    if st.session_state.get("booking_success"):
        booking_date = st.session_state.pop("booking_success_date", "")
        del st.session_state["booking_success"]
        st.toast("预约提交成功！", icon="✅")
        render_success_page(
            title="预约提交成功！",
            detail=f"到访日期: {booking_date}，请等待主人审核",
            button_label="查看我的预约",
            target_page=PAGE_MY_ORDERS,
        )
        return

    render_page_header("📝 预约下单", "选择日期和喜欢的菜品，提交您的拜访预约")

    user_id = st.session_state.get("user_id")

    # 获取可用菜品
    dish_result = db.get_all_dishes(include_unavailable=False)
    if not dish_result["success"] or not dish_result["data"]:
        st.warning("暂无可选菜品，请稍后再来。")
        return

    dishes = dish_result["data"]

    # 预约表单
    with st.form("booking_form", clear_on_submit=False):
        st.subheader("到访信息")

        # 日期选择
        tomorrow = date.today() + timedelta(days=1)
        visit_date = st.date_input(
            "到访日期",
            value=tomorrow,
            min_value=tomorrow,
            key="booking_date",
            help="请选择明天或之后的日期",
        )

        # 人数
        guest_count = st.number_input(
            "来访人数",
            min_value=1,
            max_value=MAX_GUEST_COUNT,
            value=1,
            step=1,
            key="booking_guests",
        )

        st.divider()
        st.subheader("选择菜品")
        st.caption("为每道您想品尝的菜品选择份数")

        # 预选菜品
        preselect_id = st.session_state.pop("booking_preselect_dish_id", None)

        # 菜品选择器
        dish_quantities = {}
        for dish in dishes:
            col1, col2 = st.columns([3, 1])
            with col1:
                stars = render_star_rating(dish["rating"])
                st.markdown(f"**{dish['name']}** {stars}")
                if dish["description"]:
                    st.caption(dish["description"])
            with col2:
                default_qty = 1 if dish["id"] == preselect_id else 0
                qty = st.number_input(
                    "份数",
                    min_value=0,
                    max_value=MAX_DISH_QUANTITY,
                    value=default_qty,
                    key=f"dish_qty_{dish['id']}",
                    label_visibility="collapsed",
                )
                dish_quantities[dish["id"]] = qty

        st.divider()

        # 备注
        dietary_notes = st.text_area(
            "饮食备注（过敏、忌口等）",
            placeholder="如有特殊需求请在此说明...",
            key="booking_notes",
        )

        submitted = st.form_submit_button("提交预约", use_container_width=True, type="primary")

    # 表单提交处理 (在 form 块外)
    if submitted:
        _handle_submit(user_id, visit_date, guest_count, dietary_notes, dish_quantities)


def _handle_submit(user_id, visit_date, guest_count, dietary_notes, dish_quantities):
    """处理预约提交"""
    # 校验
    ok, msg = validate_booking_date(visit_date)
    if not ok:
        st.error(msg)
        return

    ok, msg = validate_guest_count(guest_count)
    if not ok:
        st.error(msg)
        return

    # 过滤有效菜品
    selected = {k: v for k, v in dish_quantities.items() if v > 0}
    ok, msg = validate_dish_quantities(selected)
    if not ok:
        st.error(msg)
        return

    # 提交到数据库
    date_str = visit_date.isoformat() if hasattr(visit_date, "isoformat") else str(visit_date)

    with st.spinner("正在提交预约..."):
        result = db.create_booking(user_id, date_str, guest_count, dietary_notes, selected)

    if result["success"]:
        st.session_state["booking_success"] = True
        st.session_state["booking_success_date"] = date_str
        st.rerun()
    else:
        st.toast(result["message"], icon="⚠️")
        st.error(result["message"])
