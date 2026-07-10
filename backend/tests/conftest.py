"""pytest 公共配置 —— 测试数据库、客户端、认证工具"""
import os
import tempfile

import pytest
from fastapi.testclient import TestClient

# ⚠️ 必须在导入 app 之前覆盖环境变量（config.py 在 import 时读取）
# 用临时文件数据库，避免 SQLite :memory: 的连接隔离问题
_TEST_DB = os.path.join(tempfile.gettempdir(), "ai_writer_test.db")
os.environ["DATABASE_URL"] = f"sqlite:///{_TEST_DB}"
os.environ["JWT_SECRET_KEY"] = "test-jwt-secret"
os.environ["AI_API_KEY"] = "test-api-key-for-mocking"
os.environ["REGISTRATION_ENABLED"] = "true"

from app.main import app
from app.core.database import engine, Base, SessionLocal


@pytest.fixture(autouse=True)
def setup_database():
    """每个测试前新建表，测试后销毁，保证测试隔离"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    """未登录的测试客户端"""
    return TestClient(app)


@pytest.fixture
def auth_client(client):
    """已登录的测试客户端 —— 自动注册 testuser 并返回 (client, token, username)"""
    client.post(
        "/api/auth/register",
        json={"username": "testuser", "password": "test123456"},
    )
    resp = client.post(
        "/api/auth/login",
        json={"username": "testuser", "password": "test123456"},
    )
    token = resp.json()["access_token"]
    return client, token, "testuser"


def auth_headers(token: str) -> dict:
    """快捷方法：生成带 Authorization 的请求头"""
    return {"Authorization": f"Bearer {token}"}
