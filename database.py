"""HomeVisit Pro - 数据库层
负责DB连接、建表、迁移和所有CRUD操作。
所有公开函数返回统一格式: {"success": bool, "data": Any, "message": str}
"""
import sqlite3
import hashlib
from datetime import datetime
from config import DB_PATH, DEFAULT_ADMIN_USERNAME, DEFAULT_ADMIN_PASSWORD, DEFAULT_ADMIN_DISPLAY_NAME


# ============================================================
# 连接管理
# ============================================================

def get_connection():
    """获取数据库连接 (WAL模式, Row工厂, 10s超时)"""
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def _now_iso():
    """返回当前 ISO 8601 时间字符串"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _hash_password(username, password):
    """SHA-256 哈希 (用户名作为盐)"""
    raw = f"{username}:{password}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


# ============================================================
# 迁移系统
# ============================================================

MIGRATIONS = [
    # V1: 初始建表
    """
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        display_name TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'user',
        invitation_code TEXT DEFAULT '',
        created_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS dishes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT DEFAULT '',
        image_url TEXT DEFAULT '',
        rating INTEGER NOT NULL DEFAULT 3,
        is_available INTEGER NOT NULL DEFAULT 1,
        sort_order INTEGER NOT NULL DEFAULT 0,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS bookings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        visit_date TEXT NOT NULL,
        guest_count INTEGER NOT NULL DEFAULT 1,
        dietary_notes TEXT DEFAULT '',
        status TEXT NOT NULL DEFAULT 'pending',
        admin_remark TEXT DEFAULT '',
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        UNIQUE(user_id, visit_date),
        FOREIGN KEY (user_id) REFERENCES users(id)
    );

    CREATE TABLE IF NOT EXISTS booking_dishes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        booking_id INTEGER NOT NULL,
        dish_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL DEFAULT 1,
        FOREIGN KEY (booking_id) REFERENCES bookings(id),
        FOREIGN KEY (dish_id) REFERENCES dishes(id)
    );

    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        is_read INTEGER NOT NULL DEFAULT 0,
        related_booking_id INTEGER,
        created_at TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (related_booking_id) REFERENCES bookings(id)
    );
    """,
]


def _run_migrations(conn):
    """执行数据库迁移"""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS schema_version (
            version INTEGER PRIMARY KEY,
            applied_at TEXT NOT NULL
        )
    """)
    row = conn.execute("SELECT MAX(version) as v FROM schema_version").fetchone()
    current_version = row["v"] if row["v"] is not None else 0

    for i, sql in enumerate(MIGRATIONS, start=1):
        if i > current_version:
            for statement in sql.split(";"):
                statement = statement.strip()
                if statement:
                    conn.execute(statement)
            conn.execute(
                "INSERT INTO schema_version (version, applied_at) VALUES (?, ?)",
                (i, _now_iso()),
            )
    conn.commit()


def _seed_admin(conn):
    """种子默认管理员 (若不存在)"""
    row = conn.execute(
        "SELECT id FROM users WHERE username = ?", (DEFAULT_ADMIN_USERNAME,)
    ).fetchone()
    if row is None:
        conn.execute(
            """INSERT INTO users (username, password_hash, display_name, role, created_at)
               VALUES (?, ?, ?, 'admin', ?)""",
            (
                DEFAULT_ADMIN_USERNAME,
                _hash_password(DEFAULT_ADMIN_USERNAME, DEFAULT_ADMIN_PASSWORD),
                DEFAULT_ADMIN_DISPLAY_NAME,
                _now_iso(),
            ),
        )
        conn.commit()


def init_db():
    """初始化数据库: 运行迁移 + 种子管理员"""
    conn = get_connection()
    try:
        _run_migrations(conn)
        _seed_admin(conn)
    finally:
        conn.close()


# ============================================================
# 用户 CRUD
# ============================================================

def create_user(username, password, display_name, invitation_code):
    """创建新用户

    Args:
        username: 用户名 (唯一)
        password: 明文密码 (函数内部哈希)
        display_name: 显示名称
        invitation_code: 邀请码

    Returns:
        {"success": bool, "data": user_id | None, "message": str}
    """
    conn = get_connection()
    try:
        conn.execute(
            """INSERT INTO users (username, password_hash, display_name, role, invitation_code, created_at)
               VALUES (?, ?, ?, 'user', ?, ?)""",
            (
                username,
                _hash_password(username, password),
                display_name,
                invitation_code,
                _now_iso(),
            ),
        )
        conn.commit()
        user_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        return {"success": True, "data": user_id, "message": "注册成功"}
    except sqlite3.IntegrityError:
        return {"success": False, "data": None, "message": "用户名已存在"}
    except Exception as e:
        return {"success": False, "data": None, "message": f"注册失败: {e}"}
    finally:
        conn.close()


def authenticate_user(username, password):
    """验证用户登录

    Returns:
        {"success": bool, "data": dict(user_info) | None, "message": str}
    """
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM users WHERE username = ? AND password_hash = ?",
            (username, _hash_password(username, password)),
        ).fetchone()
        if row:
            return {
                "success": True,
                "data": dict(row),
                "message": "登录成功",
            }
        return {"success": False, "data": None, "message": "用户名或密码错误"}
    except Exception as e:
        return {"success": False, "data": None, "message": f"登录失败: {e}"}
    finally:
        conn.close()


def get_user_by_id(user_id):
    """根据ID获取用户信息"""
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        if row:
            return {"success": True, "data": dict(row), "message": ""}
        return {"success": False, "data": None, "message": "用户不存在"}
    finally:
        conn.close()


# ============================================================
# 菜品 CRUD
# ============================================================

def get_all_dishes(include_unavailable=False):
    """获取菜品列表

    Args:
        include_unavailable: 是否包含已下架菜品

    Returns:
        {"success": bool, "data": list[dict], "message": str}
    """
    conn = get_connection()
    try:
        if include_unavailable:
            rows = conn.execute(
                "SELECT * FROM dishes ORDER BY sort_order, id"
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM dishes WHERE is_available = 1 ORDER BY sort_order, id"
            ).fetchall()
        return {"success": True, "data": [dict(r) for r in rows], "message": ""}
    except Exception as e:
        return {"success": False, "data": [], "message": f"查询菜品失败: {e}"}
    finally:
        conn.close()


def get_dish_by_id(dish_id):
    """根据ID获取单个菜品"""
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM dishes WHERE id = ?", (dish_id,)).fetchone()
        if row:
            return {"success": True, "data": dict(row), "message": ""}
        return {"success": False, "data": None, "message": "菜品不存在"}
    finally:
        conn.close()


def create_dish(name, description="", image_url="", rating=3, sort_order=0):
    """添加新菜品

    Returns:
        {"success": bool, "data": dish_id | None, "message": str}
    """
    conn = get_connection()
    try:
        now = _now_iso()
        conn.execute(
            """INSERT INTO dishes (name, description, image_url, rating, sort_order, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (name, description, image_url, rating, sort_order, now, now),
        )
        conn.commit()
        dish_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        return {"success": True, "data": dish_id, "message": "菜品添加成功"}
    except Exception as e:
        return {"success": False, "data": None, "message": f"添加菜品失败: {e}"}
    finally:
        conn.close()


def update_dish(dish_id, name=None, description=None, image_url=None, rating=None, sort_order=None):
    """更新菜品信息 (只更新非None字段)

    Returns:
        {"success": bool, "data": None, "message": str}
    """
    conn = get_connection()
    try:
        fields = []
        values = []
        if name is not None:
            fields.append("name = ?")
            values.append(name)
        if description is not None:
            fields.append("description = ?")
            values.append(description)
        if image_url is not None:
            fields.append("image_url = ?")
            values.append(image_url)
        if rating is not None:
            fields.append("rating = ?")
            values.append(rating)
        if sort_order is not None:
            fields.append("sort_order = ?")
            values.append(sort_order)

        if not fields:
            return {"success": False, "data": None, "message": "没有需要更新的字段"}

        fields.append("updated_at = ?")
        values.append(_now_iso())
        values.append(dish_id)

        sql = f"UPDATE dishes SET {', '.join(fields)} WHERE id = ?"
        conn.execute(sql, values)
        conn.commit()
        return {"success": True, "data": None, "message": "菜品更新成功"}
    except Exception as e:
        return {"success": False, "data": None, "message": f"更新菜品失败: {e}"}
    finally:
        conn.close()


def toggle_dish_availability(dish_id):
    """切换菜品上下架状态

    Returns:
        {"success": bool, "data": bool(new_state), "message": str}
    """
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT is_available FROM dishes WHERE id = ?", (dish_id,)
        ).fetchone()
        if not row:
            return {"success": False, "data": None, "message": "菜品不存在"}
        new_state = 0 if row["is_available"] else 1
        conn.execute(
            "UPDATE dishes SET is_available = ?, updated_at = ? WHERE id = ?",
            (new_state, _now_iso(), dish_id),
        )
        conn.commit()
        label = "已上架" if new_state else "已下架"
        return {"success": True, "data": bool(new_state), "message": label}
    except Exception as e:
        return {"success": False, "data": None, "message": f"操作失败: {e}"}
    finally:
        conn.close()


# ============================================================
# 预约 CRUD
# ============================================================

def create_booking(user_id, visit_date, guest_count, dietary_notes, dishes_with_qty):
    """创建预约 (事务性: booking + booking_dishes)

    Args:
        user_id: 用户ID
        visit_date: 到访日期 (YYYY-MM-DD)
        guest_count: 来访人数
        dietary_notes: 饮食备注
        dishes_with_qty: dict {dish_id: quantity, ...}

    Returns:
        {"success": bool, "data": booking_id | None, "message": str}
    """
    conn = get_connection()
    try:
        now = _now_iso()
        cursor = conn.execute(
            """INSERT INTO bookings (user_id, visit_date, guest_count, dietary_notes, status, created_at, updated_at)
               VALUES (?, ?, ?, ?, 'pending', ?, ?)""",
            (user_id, visit_date, guest_count, dietary_notes, now, now),
        )
        booking_id = cursor.lastrowid

        for dish_id, qty in dishes_with_qty.items():
            if qty > 0:
                conn.execute(
                    "INSERT INTO booking_dishes (booking_id, dish_id, quantity) VALUES (?, ?, ?)",
                    (booking_id, int(dish_id), int(qty)),
                )
        conn.commit()
        return {"success": True, "data": booking_id, "message": "预约提交成功"}
    except sqlite3.IntegrityError:
        conn.rollback()
        return {"success": False, "data": None, "message": "您当天已有预约，请勿重复提交"}
    except Exception as e:
        conn.rollback()
        return {"success": False, "data": None, "message": f"预约失败: {e}"}
    finally:
        conn.close()


def get_user_bookings(user_id):
    """获取用户的所有预约 (含菜品信息, 按日期倒序)

    Returns:
        {"success": bool, "data": list[dict], "message": str}
        data中每项: {booking基本信息..., "dishes": [{name, quantity}, ...]}
    """
    conn = get_connection()
    try:
        bookings = conn.execute(
            "SELECT * FROM bookings WHERE user_id = ? ORDER BY visit_date DESC, created_at DESC",
            (user_id,),
        ).fetchall()

        result = []
        for b in bookings:
            bdict = dict(b)
            dishes = conn.execute(
                """SELECT bd.quantity, d.name, d.image_url
                   FROM booking_dishes bd
                   JOIN dishes d ON bd.dish_id = d.id
                   WHERE bd.booking_id = ?""",
                (b["id"],),
            ).fetchall()
            bdict["dishes"] = [dict(d) for d in dishes]
            result.append(bdict)

        return {"success": True, "data": result, "message": ""}
    except Exception as e:
        return {"success": False, "data": [], "message": f"查询预约失败: {e}"}
    finally:
        conn.close()


def get_all_bookings(status_filter=None):
    """获取所有预约 (管理员用, 含用户和菜品信息)

    Args:
        status_filter: 可选状态过滤 ('pending'/'approved'/'rejected')

    Returns:
        {"success": bool, "data": list[dict], "message": str}
    """
    conn = get_connection()
    try:
        if status_filter:
            bookings = conn.execute(
                """SELECT b.*, u.display_name as user_display_name, u.username
                   FROM bookings b JOIN users u ON b.user_id = u.id
                   WHERE b.status = ?
                   ORDER BY b.created_at DESC""",
                (status_filter,),
            ).fetchall()
        else:
            bookings = conn.execute(
                """SELECT b.*, u.display_name as user_display_name, u.username
                   FROM bookings b JOIN users u ON b.user_id = u.id
                   ORDER BY b.created_at DESC"""
            ).fetchall()

        result = []
        for b in bookings:
            bdict = dict(b)
            dishes = conn.execute(
                """SELECT bd.quantity, d.name
                   FROM booking_dishes bd
                   JOIN dishes d ON bd.dish_id = d.id
                   WHERE bd.booking_id = ?""",
                (b["id"],),
            ).fetchall()
            bdict["dishes"] = [dict(d) for d in dishes]
            result.append(bdict)

        return {"success": True, "data": result, "message": ""}
    except Exception as e:
        return {"success": False, "data": [], "message": f"查询预约失败: {e}"}
    finally:
        conn.close()


def update_booking_status(booking_id, status, admin_remark=""):
    """更新预约状态 (管理员审核)

    Returns:
        {"success": bool, "data": dict(booking) | None, "message": str}
    """
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE bookings SET status = ?, admin_remark = ?, updated_at = ? WHERE id = ?",
            (status, admin_remark, _now_iso(), booking_id),
        )
        conn.commit()
        row = conn.execute(
            "SELECT b.*, u.display_name as user_display_name FROM bookings b JOIN users u ON b.user_id = u.id WHERE b.id = ?",
            (booking_id,),
        ).fetchone()
        return {"success": True, "data": dict(row) if row else None, "message": "状态更新成功"}
    except Exception as e:
        conn.rollback()
        return {"success": False, "data": None, "message": f"更新失败: {e}"}
    finally:
        conn.close()


# ============================================================
# 消息 CRUD
# ============================================================

def create_message(user_id, title, content, related_booking_id=None):
    """创建系统消息

    Returns:
        {"success": bool, "data": message_id | None, "message": str}
    """
    conn = get_connection()
    try:
        conn.execute(
            """INSERT INTO messages (user_id, title, content, related_booking_id, created_at)
               VALUES (?, ?, ?, ?, ?)""",
            (user_id, title, content, related_booking_id, _now_iso()),
        )
        conn.commit()
        msg_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        return {"success": True, "data": msg_id, "message": "消息已发送"}
    except Exception as e:
        return {"success": False, "data": None, "message": f"发送消息失败: {e}"}
    finally:
        conn.close()


def get_user_messages(user_id, unread_only=False):
    """获取用户消息列表

    Returns:
        {"success": bool, "data": list[dict], "message": str}
    """
    conn = get_connection()
    try:
        if unread_only:
            rows = conn.execute(
                "SELECT * FROM messages WHERE user_id = ? AND is_read = 0 ORDER BY created_at DESC",
                (user_id,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM messages WHERE user_id = ? ORDER BY created_at DESC",
                (user_id,),
            ).fetchall()
        return {"success": True, "data": [dict(r) for r in rows], "message": ""}
    except Exception as e:
        return {"success": False, "data": [], "message": f"查询消息失败: {e}"}
    finally:
        conn.close()


def get_unread_count(user_id):
    """获取未读消息数量

    Returns:
        {"success": bool, "data": int, "message": str}
    """
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT COUNT(*) as cnt FROM messages WHERE user_id = ? AND is_read = 0",
            (user_id,),
        ).fetchone()
        return {"success": True, "data": row["cnt"], "message": ""}
    except Exception as e:
        return {"success": False, "data": 0, "message": f"查询失败: {e}"}
    finally:
        conn.close()


def mark_message_read(message_id):
    """标记单条消息为已读

    Returns:
        {"success": bool, "data": None, "message": str}
    """
    conn = get_connection()
    try:
        conn.execute("UPDATE messages SET is_read = 1 WHERE id = ?", (message_id,))
        conn.commit()
        return {"success": True, "data": None, "message": "已标记为已读"}
    except Exception as e:
        return {"success": False, "data": None, "message": f"操作失败: {e}"}
    finally:
        conn.close()


def mark_all_read(user_id):
    """标记用户所有消息为已读

    Returns:
        {"success": bool, "data": None, "message": str}
    """
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE messages SET is_read = 1 WHERE user_id = ? AND is_read = 0",
            (user_id,),
        )
        conn.commit()
        return {"success": True, "data": None, "message": "全部已读"}
    except Exception as e:
        return {"success": False, "data": None, "message": f"操作失败: {e}"}
    finally:
        conn.close()
