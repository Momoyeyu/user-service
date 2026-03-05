# User Service

独立用户服务 -- 为所有微服务提供统一认证与用户管理。

## Features

- JWT 鉴权（access_token + refresh_token rotation）
- 用户注册（邮箱验证码，基于 Resend）
- 登录、登出、密码找回与重置
- 用户信息管理
- 多租户支持
- 邀请码机制
- 内部服务间 API Key 鉴权
- 业务服务零网络开销鉴权（JWT 本地验证）

## Tech Stack

- **Framework**: FastAPI
- **Database**: PostgreSQL (asyncpg + SQLAlchemy 2.0 async)
- **Cache**: Redis
- **Migration**: Alembic
- **Auth**: PyJWT + bcrypt
- **Email**: Resend
- **Logging**: Loguru

## Quick Start

```bash
# 安装依赖
uv sync

# 复制环境变量
cp .env.example .env

# 启动 PostgreSQL + Redis
make docker-up

# 数据库迁移
make migrate

# 启动服务
make run
```

## Project Structure

```
user-service/
├── src/
│   ├── main.py              # FastAPI 入口
│   ├── conf/                # 配置
│   │   ├── config.py        # Pydantic Settings
│   │   ├── db.py            # 数据库连接
│   │   ├── logging.py       # Loguru 日志配置
│   │   └── openapi.py       # OpenAPI 元数据
│   ├── middleware/           # 中间件
│   │   ├── auth.py          # JWT 鉴权
│   │   └── logging.py       # 请求日志
│   ├── common/              # 公共工具
│   │   ├── error.py         # 异常辅助
│   │   └── email.py         # Resend 邮件
│   ├── auth/                # 认证模块
│   │   ├── dto.py           # 请求/响应 schemas
│   │   ├── service.py       # 业务逻辑
│   │   └── handler.py       # 路由
│   ├── user/                # 用户模块
│   │   ├── model.py         # SQLAlchemy 模型
│   │   ├── dto.py
│   │   ├── service.py
│   │   └── handler.py
│   ├── tenant/              # 租户模块
│   │   ├── model.py
│   │   ├── dto.py
│   │   ├── service.py
│   │   └── handler.py
│   └── invitation/          # 邀请码模块
│       ├── model.py
│       ├── service.py
│       └── handler.py
├── migration/               # Alembic 数据库迁移
├── tests/                   # 测试
│   ├── unit/
│   └── integration/
├── scripts/                 # 运维脚本
├── pyproject.toml
├── Makefile
├── Dockerfile
├── docker-compose.yml
└── .env.example
```

## Makefile Commands

```bash
make help       # 查看所有命令
make run        # 启动开发服务器
make migrate    # 执行数据库迁移
make lint       # 代码检查
make test       # 运行测试
make deploy     # 部署应用
```

## API Overview

| Method | Path                             | Auth        | Description    |
| ------ | -------------------------------- | ----------- | -------------- |
| POST   | /api/v1/auth/register            | -           | 发起注册       |
| POST   | /api/v1/auth/register/verify     | -           | 验证码确认注册 |
| POST   | /api/v1/auth/login               | -           | 登录           |
| POST   | /api/v1/auth/token/refresh       | -           | 刷新 token     |
| POST   | /api/v1/auth/logout              | -           | 登出           |
| POST   | /api/v1/auth/password/forgot     | -           | 忘记密码       |
| POST   | /api/v1/auth/password/reset      | -           | 重置密码       |
| GET    | /api/v1/users/me                 | JWT         | 获取个人信息   |
| PUT    | /api/v1/users/me                 | JWT         | 更新个人信息   |
| PUT    | /api/v1/users/me/password        | JWT         | 修改密码       |
| GET    | /api/v1/tenants/current          | JWT         | 获取租户信息   |
| PUT    | /api/v1/tenants/current          | JWT (owner) | 更新租户信息   |
| GET    | /api/v1/internal/users/{user_id} | API Key     | 内部查询用户   |
| POST   | /api/v1/internal/users/batch     | API Key     | 内部批量查询   |
