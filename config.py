"""HomeVisit Pro - 配置文件"""
import os

# ============ 路径配置 ============
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "homevisit.db")

# ============ 应用信息 ============
APP_TITLE = "HomeVisit Pro"
APP_SUBTITLE = "家庭预约接待系统"
APP_ICON = "\U0001F3E0"

# ============ 默认管理员 ============
DEFAULT_ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_PASSWORD = "admin123"
DEFAULT_ADMIN_DISPLAY_NAME = "管理员"

# ============ 邀请码 ============
INVITATION_CODES = ["WELCOME2024", "HOMEFOOD", "VISIT888"]

# ============ 页面标识 ============
PAGE_HOME = "home"
PAGE_BOOKING = "booking"
PAGE_MY_ORDERS = "my_orders"
PAGE_MESSAGES = "messages"
PAGE_ADMIN = "admin_dashboard"

# ============ 状态常量 ============
STATUS_PENDING = "pending"
STATUS_APPROVED = "approved"
STATUS_REJECTED = "rejected"

STATUS_LABELS = {
    STATUS_PENDING: "待审核",
    STATUS_APPROVED: "已通过",
    STATUS_REJECTED: "已拒绝",
}

STATUS_COLORS = {
    STATUS_PENDING: "#FF8C00",
    STATUS_APPROVED: "#4CAF50",
    STATUS_REJECTED: "#F44336",
}

# ============ 业务限制 ============
MAX_GUEST_COUNT = 20
MAX_DISH_QUANTITY = 10

# ============ 主题色 ============
THEME_PRIMARY = "#FF8C00"
THEME_SUCCESS = "#4CAF50"
THEME_DANGER = "#F44336"
THEME_BG_WARM = "#FFFAF5"
THEME_SIDEBAR_BG = "#FFF0E0"
