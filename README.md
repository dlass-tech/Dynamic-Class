📋 Dynamic Class - 智能班级管理解决方案

<div align="center">

https://img.shields.io/badge/Python-3.8+-blue.svg
https://img.shields.io/badge/Flask-2.3+-green.svg
https://img.shields.io/badge/Socket.IO-4.0+-orange.svg

现代化、实时、高效的班级管理与信息发布系统

</div>

🚀 项目简介

白板系统是一款专为教育场景设计的智能班级管理平台，通过现代化的 Web 界面和实时通信技术，为教师和学生提供高效的信息发布与接收体验。

✨ 核心价值

· 实时同步: 教师发布内容即时推送到所有客户端
· 多端适配: 支持 Web 管理端和命令行客户端
· 权限管理: 精细化的角色权限控制
· 离线缓存: 客户端支持离线查看历史数据

🌟 功能特性

教师端功能

· 📝 作业管理 - 发布、更新、删除学科作业
· ✅ 任务分配 - 创建班级任务，跟踪完成状态
· 📢 公告发布 - 实时推送重要通知
· 👥 班级管理 - 多教师协作，学科分配
· 📊 状态监控 - 实时查看白板在线状态

学生端功能

· 🔔 实时接收 - 即时获取作业、任务、公告
· 📱 多平台支持 - Web、命令行、移动端
· ⏰ 智能提醒 - 截止日期提醒，状态跟踪
· 📚 学科分类 - 按学科查看相关作业
· 💾 历史查询 - 按日期筛选历史内容

🛠 技术栈

后端技术

· 框架: Flask + Flask-SocketIO
· 数据库: SQLAlchemy + SQLite/PostgreSQL
· 实时通信: Socket.IO
· 认证: Casdoor OAuth2
· 任务调度: APScheduler

前端技术

· Web管理端: Jinja2 + Bootstrap
· API接口: RESTful + WebSocket
· 客户端: Python + Socket.IO Client

辅助技术

· 前端: Deepseek你值得拥有！
· Debug: Deepseek你值得拥有！

🚀 快速开始

环境要求

· Python 3.8+
· PostgreSQL 12+

安装步骤

1. 克隆项目

```bash
git clone https://github.com/Super-Yyt/Dynamic-Class.git
cd Dynamic-Class
```

1. 安装依赖

```bash
pip install -r requirements.txt
```

1. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，配置数据库和认证信息
```

1. 初始化数据库

```bash
flask db upgrade
```

1. 启动服务

```bash
python app.py
```

客户端使用

暂未开发哦

📖 使用说明

教师操作流程

1. 创建班级
   · 登录 Web 管理端
   · 创建新班级，获取班级代码
2. 设置白板
   · 为班级创建白板
   · 获取白板凭证 (board_id, secret_key)
3. 发布内容
   · 发布作业、任务、公告
   · 实时推送到所有连接的客户端

Web客户端

· 响应式设计，支持移动端
· 实时通知提醒

🏗 项目结构

```
Dynamic-Class/
├── app.py                 # 应用入口
├── config.py             # 配置文件
├── requirements.txt      # 依赖列表
├── extensions.py         # 扩展初始化
├── models/               # 数据模型
│   ├── user.py
│   ├── class_models.py
│   ├── whiteboard.py
│   ├── task.py
│   ├── assignment.py
│   └── announcement.py
├── blueprints/           # 蓝图模块
│   ├── auth.py
│   ├── main.py
│   ├── classes.py
│   ├── whiteboards.py
│   ├── tasks.py
│   ├── assignments.py
│   ├── announcements.py
│   ├── api.py
│   └── settings.py
├── events/               # Socket.IO 事件处理
│   └── socketio_events.py
├── utils/                # 工具函数
│   ├── auth_utils.py
│   ├── time_utils.py
│   ├── code_utils.py
│   └── casdoor_utils.py
├── templates/            # 前端模板
├── static/               # 静态资源
└── clients/              # 客户端实现
    └── command_line_client.py
```

🔌 API 文档

认证方式

```http
X-Board-ID: your_board_id
X-Secret-Key: your_secret_key
```

主要接口

· GET /api/whiteboard/assignments - 获取作业列表
· GET /api/whiteboard/tasks - 获取任务列表
· GET /api/whiteboard/announcements - 获取公告列表
· GET /api/whiteboard/all - 获取所有内容
· POST /api/whiteboard/tasks/{id}/acknowledge - 确认任务
· POST /api/whiteboard/tasks/{id}/complete - 完成任务

实时事件

· new_task - 新任务通知
· new_assignment - 新作业通知
· new_announcement - 新公告通知
· task_updated - 任务状态更新

🤝 贡献指南

我们欢迎所有形式的贡献！请阅读以下指南：

报告问题

· 使用 Issue 模板
· 描述清晰的问题现象和复现步骤

提交代码

1. Fork 本项目
2. 创建功能分支 (git checkout -b feature/AmazingFeature)
3. 提交更改 (git commit -m 'Add some AmazingFeature')
4. 推送到分支 (git push origin feature/AmazingFeature)
5. 开启 Pull Request

开发规范

· 遵循 PEP 8 代码规范
· 添加适当的注释和文档
· 编写单元测试
· 确保所有测试通过

📄 许可证

暂无，待我考虑

📞 联系方式

· 项目主页: https://dlass.tech
· 问题反馈: GitHub Issues
· 邮箱联系: zhaishis06@163.com
· 技术交流群: 745977590

🙏 致谢

感谢所有为这个项目做出贡献的开发者！

---

<div align="center">

如果这个项目对你有帮助，请给个 ⭐️ 支持一下！

⬆ 返回顶部

</div>

[![Powered by DartNode](https://dartnode.com/branding/DN-Open-Source-sm.png)](https://dartnode.com "Powered by DartNode - Free VPS for Open Source")
