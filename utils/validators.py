"""HomeVisit Pro - 数据校验层
纯函数，无 Streamlit 依赖。
每个校验函数返回 (is_valid: bool, error_message: str)。
"""
from datetime import date, timedelta
from config import INVITATION_CODES, MAX_GUEST_COUNT, MAX_DISH_QUANTITY


def validate_username(username):
    """校验用户名: 3-20字符, 字母/数字/下划线"""
    if not username or len(username.strip()) < 3:
        return False, "用户名至少3个字符"
    if len(username) > 20:
        return False, "用户名不超过20个字符"
    if not all(c.isalnum() or c == "_" for c in username):
        return False, "用户名只能包含字母、数字和下划线"
    return True, ""


def validate_password(password):
    """校验密码: 至少6个字符"""
    if not password or len(password) < 6:
        return False, "密码至少6个字符"
    return True, ""


def validate_display_name(name):
    """校验显示名称: 1-20字符"""
    if not name or len(name.strip()) == 0:
        return False, "请输入昵称"
    if len(name) > 20:
        return False, "昵称不超过20个字符"
    return True, ""


def validate_invitation_code(code):
    """校验邀请码"""
    if not code or code.strip() not in INVITATION_CODES:
        return False, "邀请码无效"
    return True, ""


def validate_booking_date(visit_date):
    """校验预约日期: 必须是明天或之后"""
    if visit_date is None:
        return False, "请选择到访日期"
    today = date.today()
    if isinstance(visit_date, str):
        try:
            visit_date = date.fromisoformat(visit_date)
        except ValueError:
            return False, "日期格式无效"
    if visit_date <= today:
        return False, "到访日期必须是明天或之后"
    return True, ""


def validate_guest_count(count):
    """校验来访人数: 1-MAX_GUEST_COUNT"""
    if count is None or count < 1:
        return False, "来访人数至少1人"
    if count > MAX_GUEST_COUNT:
        return False, f"来访人数不超过{MAX_GUEST_COUNT}人"
    return True, ""


def validate_dish_quantities(dishes_qty):
    """校验菜品选择: 至少选一道菜, 数量合法

    Args:
        dishes_qty: dict {dish_id: quantity}
    """
    if not dishes_qty:
        return False, "请至少选择一道菜品"
    selected = {k: v for k, v in dishes_qty.items() if v > 0}
    if not selected:
        return False, "请至少选择一道菜品"
    for dish_id, qty in selected.items():
        if qty > MAX_DISH_QUANTITY:
            return False, f"单道菜品数量不超过{MAX_DISH_QUANTITY}份"
    return True, ""
