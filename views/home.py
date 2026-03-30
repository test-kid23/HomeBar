"""HomeVisit Pro - 首页/菜单展示"""
import streamlit as st
import database as db
from utils.ui_components import render_page_header, render_dish_card, render_empty_state


def render():
    """渲染菜单浏览页面"""
    render_page_header("🍽️ 菜单浏览", "精心准备的家庭美食，等你来品尝")

    result = db.get_all_dishes(include_unavailable=False)

    if not result["success"]:
        st.error(result["message"])
        return

    dishes = result["data"]

    if not dishes:
        render_empty_state("🍳", "菜单正在准备中，敬请期待！")
        return

    # 响应式网格: 使用2列布局 (手机端Streamlit自动堆叠)
    cols = st.columns(2)
    for idx, dish in enumerate(dishes):
        with cols[idx % 2]:
            render_dish_card(dish, show_select_button=True)
