# HomeBar
 Streamlit Web 应用，用于家庭主人邀请访客预约拜访的场景。访客选择日期、人数和菜品，主人后台审核并准备接待。
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