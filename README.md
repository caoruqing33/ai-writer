# ✍️ AI Writer — 智能写作助手

> AI 驱动的写作伙伴，助你写出**真实、有温度**的公众号/自媒体文章

<p align="center">
  <img src="https://img.shields.io/badge/python-3.11+-blue?logo=python" alt="Python">
  <img src="https://img.shields.io/badge/FastAPI-0.115-green?logo=fastapi" alt="FastAPI">
  <img src="https://img.shields.io/badge/AI-DeepSeek-536DFE" alt="DeepSeek">
  <img src="https://img.shields.io/badge/SSE-流式输出-orange" alt="SSE">
  <img src="https://img.shields.io/badge/license-MIT-lightgrey" alt="License">
</p>

---

## 🎯 核心理念

**AI 不是你的代笔，而是你的写作伙伴。**

市面上的 AI 写作工具直接帮你"生成"文章——写出来的东西千篇一律、AI 痕迹重、没有个人风格。AI Writer 走另一条路：

| 传统 AI 写作 | AI Writer |
|---|---|
| AI 替你写，你复制粘贴 | AI 引导你，你写出自己的东西 |
| 套话连篇，"一方面…另一方面…" | 口语化、具体、有个性 |
| 一次生成，改都不知道怎么改 | 教练式互动，一步步打磨 |

---

## ✨ 三种写作模式

### 🧑‍🏫 教练模式（Coach）
AI 化身写作教练，**只提问引导，绝不代写**。帮你挖掘真实经历和独特观点，让你亲手写出有温度的文字。

### ⚡ 快速模式（Fast）
提供主题和需求，AI **直接生成初稿**。内置反 AI 检测规则，生成内容口语化、段落短、手机阅读友好。

### 🤝 混合模式（Hybrid）
**先聊后写**。阶段一：AI 像教练一样和你聊，收集素材、敲定大纲。阶段二：确认大纲后，基于你的素材一次性生成完整文章。

---

## 🔧 主要功能

- 🤖 **SSE 流式对话** — 逐字实时输出，像 ChatGPT 一样的打字机体验
- 📱 **微信格式化导出** — Markdown 一键转为微信公众号兼容 HTML（内联样式，可直粘贴）
- 🔐 **JWT 用户认证** — 注册/登录，每人独立工作区
- 📂 **项目 & 文章管理** — 多项目、多文章，随时切换
- 📊 **自动字数统计** — 保存草稿时自动计算
- 🧹 **反 AI 检测** — System Prompt 精心设计，降低"AI 味"

---

## 🏗️ 技术栈

| 层级 | 技术 |
|------|------|
| 后端框架 | FastAPI |
| 大模型 | DeepSeek（兼容 OpenAI 格式，可轻松换模型） |
| 流式输出 | SSE（Server-Sent Events） |
| 数据库 | SQLite + SQLAlchemy 2.0 ORM |
| 认证 | bcrypt + JWT |
| 格式化 | Python-Markdown + Pygments 代码高亮 |
| 前端 | 原生 HTML/CSS/JS（单页应用，零依赖框架） |

---

## 📁 项目结构

```
ai-writer/
└── backend/
    ├── app/
    │   ├── main.py              # FastAPI 入口
    │   ├── api/                 # 路由层
    │   │   ├── auth.py          # 注册/登录
    │   │   ├── projects.py      # 项目 CRUD
    │   │   ├── articles.py      # 文章 CRUD
    │   │   ├── chat.py          # ⭐ AI 流式对话（核心）
    │   │   └── format.py        # 微信格式化导出
    │   ├── core/                # 基础设施
    │   │   ├── config.py        # 配置管理
    │   │   ├── database.py      # 数据库连接
    │   │   └── auth.py          # JWT 认证
    │   ├── models/              # 数据模型
    │   │   ├── user.py          # 用户表
    │   │   ├── project.py       # 项目表
    │   │   ├── article.py       # 文章表
    │   │   └── message.py       # 对话消息表
    │   └── services/
    │       └── wechat_formatter.py  # Markdown→微信 HTML
    ├── static/
    │   └── index.html           # 前端 SPA
    ├── demo.py                  # 命令行演示脚本
    └── requirements.txt
```

---

## 🚀 快速开始

### 1. 环境准备

```bash
# Python 3.11+
git clone git@github.com:caoruqing33/ai-writer.git
cd ai-writer/backend

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置 API Key

```bash
# 创建 .env 文件
cat > .env << EOF
AI_API_KEY=你的DeepSeek_API_Key
AI_BASE_URL=https://api.deepseek.com
AI_MODEL=deepseek-chat
JWT_SECRET_KEY=换个复杂的随机字符串
EOF
```

> 💡 DeepSeek API Key 可以在 [platform.deepseek.com](https://platform.deepseek.com) 免费获取。也可以用任何兼容 OpenAI 格式的模型。

### 3. 启动

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

浏览器打开 **http://localhost:8000**，注册账号即可使用。

API 文档自动生成在 **http://localhost:8000/docs**（Swagger UI）。

### 4. 命令行演示

```bash
# 先启动服务，再运行演示脚本
python demo.py
```

---

## 📡 API 概要

| 方法 | 路径 | 说明 | 需要登录 |
|------|------|------|----------|
| POST | `/api/auth/register` | 注册 | ❌ |
| POST | `/api/auth/login` | 登录 | ❌ |
| GET | `/api/projects` | 项目列表 | ✅ |
| POST | `/api/projects` | 创建项目 | ✅ |
| GET | `/api/projects/{id}/articles` | 文章列表 | ✅ |
| POST | `/api/projects/{id}/articles` | 创建文章 | ✅ |
| PATCH | `/api/articles/{id}` | 更新文章 | ✅ |
| POST | `/api/articles/{id}/chat` | ⭐ AI 对话（SSE 流式） | ✅ |
| GET | `/api/articles/{id}/wechat-export` | 微信格式导出 | ✅ |

---

## 🔮 后续计划

- [ ] Vue 3 前端（前后端分离）
- [ ] RAG 知识库检索 — 自动查资料、引经据典
- [ ] 多平台导出（知乎、头条、小红书）
- [ ] Agent 模式 — AI 自主规划写作任务
- [ ] PostgreSQL 支持

---

## 📄 License

MIT © caoruqing33
