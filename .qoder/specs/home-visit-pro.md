# HomeVisit Pro - 家庭预约接待系统 实现计划

## Context

在 `d:\aitesta` 空目录中从零构建一个 Streamlit Web 应用，用于家庭主人邀请访客预约拜访的场景。访客选择日期、人数和菜品，主人后台审核并准备接待。要求模块化架构、移动端优先、温馨暖色设计风格。

## 目录结构

```
d:\aitesta\
├── main.py                     # 入口 (<100行): 路由、Session、布局
├── config.py                   # 常量配置
├── database.py                 # SQLite CRUD + 迁移
├── utils/
│   ├── auth.py                 # 登录注册、权限
│   ├── ui_components.py        # 通用UI组件
│   └── validators.py           # 数据校验
├── pages/
│   ├── home.py                 # 菜单展示
│   ├── booking.py              # 预约提交
│   ├── my_orders.py            # 用户预约记录
│   ├── admin_dashboard.py      # 管理后台
│   └── messages.py             # 消息中心
├── assets/
│   └── style.css               # 移动端适配CSS
├── .streamlit/
│   └── config.toml             # Streamlit主题配置
└── requirements.txt
```

## 数据库设计 (SQLite)

6张表，统一使用迁移系统管理：

1. **users**: id, username(UNIQUE), password_hash, display_name, role('admin'/'user'), invitation_code, created_at
2. **dishes**: id, name, description, image_url, rating(1-5), is_available, sort_order, created_at, updated_at
3. **bookings**: id, user_id(FK), visit_date, guest_count, dietary_notes, status('pending'/'approved'/'rejected'), admin_remark, created_at, updated_at  
   - UNIQUE约束: `(user_id, visit_date)` 防止同日重复预约
4. **booking_dishes**: id, booking_id(FK), dish_id(FK), quantity
5. **messages**: id, user_id(FK), title, content, is_read(0/1), related_booking_id, created_at
6. **schema_version**: version, applied_at (迁移版本追踪)

所有DB函数返回 `{"success": bool, "data": Any, "message": str}`。

## 核心技术决策

| 决策 | 方案 | 理由 |
|------|------|------|
| 路由方式 | 手动Router (session_state.current_page) | 需要统一认证门控和角色导航 |
| 密码哈希 | hashlib.sha256(username+password) | 家用场景足够，无需额外依赖 |
| 图片存储 | base64存SQLite 或 URL | 菜品数量有限，简单可靠 |
| 并发处理 | WAL模式 + timeout=10 | SQLite最佳实践 |
| 表单提交 | st.form() + flag-then-rerun模式 | 防误触 + Toast反馈存活 |
| 重复预约 | DB UNIQUE约束 + IntegrityError捕获 | 数据库层面强保证 |

## 实现步骤

### Phase 1: 基础架构
1. 创建 `requirements.txt` (streamlit>=1.30)
2. 创建 `config.py` - 所有常量(DB路径、邀请码、页面标识、颜色)
3. 创建 `database.py` - 连接管理(WAL)、迁移系统、建表、种子Admin、全部CRUD函数
4. 创建 `.streamlit/config.toml` - 暖色主题

### Phase 2: 工具层
5. 创建 `utils/validators.py` - 纯函数校验(用户名/密码/日期/人数/菜品)
6. 创建 `utils/auth.py` - Session初始化、login/logout、登录注册表单
7. 创建 `assets/style.css` - 移动端媒体查询、触控优化、卡片圆角阴影
8. 创建 `utils/ui_components.py` - 侧边栏(含红点)、菜品卡片、订单卡片、状态徽章、星级、CSS注入

### Phase 3: 页面实现
9. 创建 `pages/home.py` - 响应式菜品卡片网格，无价格
10. 创建 `pages/booking.py` - 日期/人数/菜品选择表单，防重提交，Loading+Toast+自动跳转
11. 创建 `pages/my_orders.py` - 合并展示订单卡片，备注不重复，状态标签
12. 创建 `pages/messages.py` - 消息列表，展开即已读，全部标已读按钮
13. 创建 `pages/admin_dashboard.py` - 两个Tab(菜单CRUD+预约审核)，审核自动发消息

### Phase 4: 入口整合
14. 创建 `main.py` - set_page_config、init_db、认证门控、CSS注入、侧边栏、路由分发

### Phase 5: 测试验证
15. 启动应用验证完整流程

## 关键交互流程

### 预约提交流程
```
填写表单 → 提交 → validators校验 → [失败则st.error]
→ with st.spinner → database.create_booking()
→ [IntegrityError] → toast"当天已预约"
→ [成功] → session_state设标记 → rerun → toast"提交成功" → 跳转我的预约
```

### 管理员审核流程
```
点击通过/拒绝 → database.update_booking_status()
→ database.create_message(通知访客)
→ toast反馈 → rerun刷新列表
```

### 消息已读流程
```
展开消息 → database.mark_message_read() → rerun
侧边栏每次render → database.get_unread_count() → 显示/隐藏红点
```

## 移动端适配要点
- 按钮最小高度44px，输入框字体16px+
- 图片 width:100% height:auto
- @media(max-width:768px) 适配padding和布局
- st.columns最多2-3列
- initial_sidebar_state="collapsed" 适配手机

## 验证方式
1. `pip install -r requirements.txt`
2. `streamlit run main.py`
3. 测试流程: 默认admin登录 → 添加菜品 → 注册新用户(用邀请码) → 浏览菜单 → 提交预约 → 同日再提交(验证防重) → admin审核 → 用户查看消息 → 标记已读
4. 浏览器F12手机模式验证移动端适配
