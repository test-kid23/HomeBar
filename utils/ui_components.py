"""HomeVisit Pro - 通用UI组件
封装所有重复使用的 UI 逻辑：侧边栏、菜品卡片、订单卡片、状态徽章等。
"""
import os
import streamlit as st
import database as db
from config import (
    APP_TITLE, APP_ICON,
    PAGE_HOME, PAGE_BOOKING, PAGE_MY_ORDERS, PAGE_MESSAGES, PAGE_ADMIN,
    STATUS_PENDING, STATUS_APPROVED, STATUS_REJECTED,
    STATUS_LABELS, STATUS_COLORS,
)


# ============================================================
# CSS 注入
# ============================================================

def apply_custom_css():
    """读取并注入自定义 CSS"""
    css_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "style.css")
    if os.path.exists(css_path):
        with open(css_path, "r", encoding="utf-8") as f:
            css = f.read()
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


# ============================================================
# 侧边栏导航
# ============================================================

def render_sidebar():
    """渲染侧边栏导航，含未读消息红点

    根据角色显示不同菜单项，返回值通过 session_state.current_page 控制。
    """
    user_id = st.session_state.get("user_id")
    role = st.session_state.get("role", "user")
    display_name = st.session_state.get("display_name", "")

    with st.sidebar:
        st.markdown(
            f"<div style='text-align:center; padding:1rem 0;'>"
            f"<span style='font-size:1.8rem;'>{APP_ICON}</span><br>"
            f"<strong style='font-size:1.1rem; color:#FF8C00;'>{APP_TITLE}</strong>"
            f"</div>",
            unsafe_allow_html=True,
        )

        st.markdown(
            f"<div style='text-align:center; padding:0.5rem; background:#FFF0E0; "
            f"border-radius:8px; margin-bottom:1rem;'>"
            f"<span style='font-size:0.85rem; color:#888;'>当前用户</span><br>"
            f"<strong style='color:#333;'>{display_name}</strong>"
            f"<span style='font-size:0.75rem; color:#FF8C00; margin-left:0.3rem;'>"
            f"{'(管理员)' if role == 'admin' else ''}</span>"
            f"</div>",
            unsafe_allow_html=True,
        )

        st.divider()

        # 获取未读消息数
        unread = 0
        if user_id:
            result = db.get_unread_count(user_id)
            if result["success"]:
                unread = result["data"]

        # 导航项定义
        if role == "admin":
            nav_items = [
                (PAGE_HOME, "🏠 菜单浏览", False),
                (PAGE_ADMIN, "⚙️ 管理面板", False),
                (PAGE_MESSAGES, "🔔 消息中心", True),
            ]
        else:
            nav_items = [
                (PAGE_HOME, "🏠 菜单浏览", False),
                (PAGE_BOOKING, "📝 预约下单", False),
                (PAGE_MY_ORDERS, "📋 我的预约", False),
                (PAGE_MESSAGES, "🔔 消息中心", True),
            ]

        current = st.session_state.get("current_page", PAGE_HOME)

        for page_key, label, show_badge in nav_items:
            badge_html = ""
            if show_badge and unread > 0:
                badge_html = f" 🔴 {unread}"

            btn_label = f"{label}{badge_html}"
            btn_type = "primary" if current == page_key else "secondary"

            if st.button(btn_label, key=f"nav_{page_key}", use_container_width=True, type=btn_type):
                st.session_state.current_page = page_key
                st.rerun()

        st.divider()

        if st.button("🚪 退出登录", key="nav_logout", use_container_width=True):
            from utils.auth import logout
            logout()
            st.rerun()


# ============================================================
# 页面标题
# ============================================================

def render_page_header(title, subtitle=None):
    """渲染统一的页面标题"""
    sub_html = f"<p>{subtitle}</p>" if subtitle else ""
    st.markdown(
        f'<div class="page-header"><h2>{title}</h2>{sub_html}</div>',
        unsafe_allow_html=True,
    )


# ============================================================
# 星级评分
# ============================================================

def render_star_rating(rating, max_stars=5):
    """返回星级评分 HTML 字符串"""
    full = min(int(rating), max_stars)
    empty = max_stars - full
    stars = "⭐" * full + "☆" * empty
    return stars


# ============================================================
# 状态徽章
# ============================================================

def render_status_badge(status):
    """返回状态徽章 HTML"""
    label = STATUS_LABELS.get(status, status)
    css_class = status
    return f'<span class="status-badge {css_class}">{label}</span>'


# ============================================================
# 菜品卡片
# ============================================================

def render_dish_card(dish, show_select_button=False, show_admin_actions=False):
    """渲染单个菜品卡片

    Args:
        dish: 菜品 dict
        show_select_button: 是否显示"选这道菜"按钮 (用户首页)
        show_admin_actions: 是否显示管理按钮 (管理后台)
    """
    name = dish.get("name", "未知菜品")
    desc = dish.get("description", "")
    image_url = dish.get("image_url", "")
    rating = dish.get("rating", 3)
    is_available = dish.get("is_available", 1)
    dish_id = dish.get("id", 0)

    # 下架菜品灰色标识
    opacity = "1" if is_available else "0.5"

    st.markdown(f'<div class="dish-card" style="opacity:{opacity};">', unsafe_allow_html=True)

    # 图片
    if image_url:
        st.image(image_url, use_container_width=True)

    # 名称 + 星级
    unavail_tag = " <span style='color:#F44336; font-size:0.8rem;'>[已下架]</span>" if not is_available else ""
    st.markdown(
        f'<div class="dish-name">{name}{unavail_tag}</div>'
        f'<div class="dish-rating">{render_star_rating(rating)}</div>',
        unsafe_allow_html=True,
    )

    # 描述
    if desc:
        st.markdown(f'<div class="dish-desc">{desc}</div>', unsafe_allow_html=True)

    # 用户选菜按钮
    if show_select_button and is_available:
        if st.button("去预约这道菜 →", key=f"select_dish_{dish_id}", use_container_width=True):
            st.session_state.booking_preselect_dish_id = dish_id
            st.session_state.current_page = PAGE_BOOKING
            st.rerun()

    # 管理按钮
    if show_admin_actions:
        col_edit, col_toggle = st.columns(2)
        with col_edit:
            if st.button("✏️ 编辑", key=f"edit_dish_{dish_id}", use_container_width=True):
                st.session_state.admin_editing_dish_id = dish_id
                st.rerun()
        with col_toggle:
            toggle_label = "⬇️ 下架" if is_available else "⬆️ 上架"
            if st.button(toggle_label, key=f"toggle_dish_{dish_id}", use_container_width=True):
                result = db.toggle_dish_availability(dish_id)
                if result["success"]:
                    st.toast(result["message"], icon="✅")
                    st.rerun()
                else:
                    st.toast(result["message"], icon="❌")

    st.markdown("</div>", unsafe_allow_html=True)


# ============================================================
# 订单卡片
# ============================================================

def render_booking_card(booking, show_user_info=False, show_admin_actions=False):
    """渲染合并的订单卡片

    Args:
        booking: 预约 dict (含 dishes 列表)
        show_user_info: 是否显示用户信息 (管理后台)
        show_admin_actions: 是否显示审核按钮 (管理后台)
    """
    status = booking.get("status", STATUS_PENDING)
    visit_date = booking.get("visit_date", "")
    guest_count = booking.get("guest_count", 1)
    dietary_notes = booking.get("dietary_notes", "")
    dishes = booking.get("dishes", [])
    booking_id = booking.get("id", 0)
    created_at = booking.get("created_at", "")

    css_class = f"status-{status}" if status in (STATUS_APPROVED, STATUS_REJECTED) else ""

    st.markdown(f'<div class="booking-card {css_class}">', unsafe_allow_html=True)

    # 头部: 日期 + 状态
    header_html = f"""
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.5rem;">
        <strong style="font-size:1.05rem;">📅 {visit_date}</strong>
        {render_status_badge(status)}
    </div>
    """
    st.markdown(header_html, unsafe_allow_html=True)

    # 用户信息 (管理后台)
    if show_user_info:
        user_name = booking.get("user_display_name", booking.get("username", ""))
        st.markdown(f"**预约人：** {user_name}")

    # 来访人数
    st.markdown(f"**来访人数：** {guest_count} 人")

    # 菜品列表
    if dishes:
        st.markdown("**预选菜品：**")
        for d in dishes:
            st.markdown(f"- {d['name']} × {d['quantity']}")

    # 备注 (只显示一次)
    if dietary_notes:
        st.markdown(f"**备注：** {dietary_notes}")

    # 管理员备注
    admin_remark = booking.get("admin_remark", "")
    if admin_remark and status == STATUS_REJECTED:
        st.markdown(f"**拒绝原因：** {admin_remark}")

    # 提交时间
    if created_at:
        st.markdown(
            f'<div style="font-size:0.8rem; color:#aaa; margin-top:0.5rem;">提交于 {created_at}</div>',
            unsafe_allow_html=True,
        )

    # 管理员审核操作
    if show_admin_actions and status == STATUS_PENDING:
        st.divider()
        col_approve, col_reject = st.columns(2)
        with col_approve:
            if st.button("✅ 通过", key=f"approve_{booking_id}", use_container_width=True, type="primary"):
                _handle_booking_approval(booking, STATUS_APPROVED)
        with col_reject:
            remark_key = f"reject_remark_{booking_id}"
            if remark_key not in st.session_state:
                st.session_state[remark_key] = False

            if st.session_state[remark_key]:
                remark = st.text_input("拒绝原因 (可选)", key=f"remark_text_{booking_id}")
                if st.button("确认拒绝", key=f"confirm_reject_{booking_id}", use_container_width=True):
                    _handle_booking_approval(booking, STATUS_REJECTED, remark)
            else:
                if st.button("❌ 拒绝", key=f"reject_{booking_id}", use_container_width=True):
                    st.session_state[remark_key] = True
                    st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)


def _handle_booking_approval(booking, new_status, admin_remark=""):
    """处理预约审核 (通过/拒绝) + 自动发送消息通知"""
    booking_id = booking["id"]
    user_id = booking["user_id"]
    visit_date = booking["visit_date"]

    result = db.update_booking_status(booking_id, new_status, admin_remark)
    if result["success"]:
        # 发送消息通知
        if new_status == STATUS_APPROVED:
            title = "预约已通过 ✅"
            content = f"您 {visit_date} 的预约已通过，欢迎到访！"
        else:
            title = "预约未通过 ❌"
            content = f"您 {visit_date} 的预约未通过。"
            if admin_remark:
                content += f"\n原因：{admin_remark}"

        db.create_message(user_id, title, content, booking_id)
        st.toast(f"已{STATUS_LABELS[new_status]}", icon="✅")
        st.rerun()
    else:
        st.toast(result["message"], icon="❌")


# ============================================================
# 空状态
# ============================================================

def render_empty_state(icon, message):
    """渲染空状态提示"""
    st.markdown(
        f'<div class="empty-state">'
        f'<div class="empty-icon">{icon}</div>'
        f'<div>{message}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


# ============================================================
# 成功页面
# ============================================================

def render_success_page(title, detail="", button_label="返回首页", target_page=PAGE_HOME):
    """渲染操作成功反馈页"""
    st.markdown(
        f'<div class="success-page">'
        f'<div class="success-icon">✅</div>'
        f'<div class="success-title">{title}</div>'
        f'<div class="success-detail">{detail}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button(button_label, key="success_back", use_container_width=True, type="primary"):
            st.session_state.current_page = target_page
            st.rerun()
