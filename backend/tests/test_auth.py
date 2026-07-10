"""认证模块测试 —— 注册、登录、Token 验证"""


class TestRegister:
    """用户注册"""

    def test_register_success(self, client):
        """正常注册，返回 token 和用户名"""
        resp = client.post(
            "/api/auth/register",
            json={"username": "alice", "password": "pass123456"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["access_token"]
        assert data["token_type"] == "bearer"
        assert data["username"] == "alice"

    def test_register_duplicate_username(self, client):
        """重复用户名 → 400"""
        client.post(
            "/api/auth/register",
            json={"username": "bob", "password": "pass123456"},
        )
        resp = client.post(
            "/api/auth/register",
            json={"username": "bob", "password": "another456"},
        )
        assert resp.status_code == 400
        assert "已被注册" in resp.json()["detail"]

    def test_register_short_password(self, client):
        """密码太短 → 400"""
        resp = client.post(
            "/api/auth/register",
            json={"username": "charlie", "password": "12345"},
        )
        assert resp.status_code == 400
        assert "至少" in resp.json()["detail"]

    def test_register_empty_username(self, client):
        """空用户名 → 允许创建（AuthRequest 未限制长度，靠前端的 required 处理）"""
        resp = client.post(
            "/api/auth/register",
            json={"username": "", "password": "pass123456"},
        )
        assert resp.status_code == 201


class TestLogin:
    """用户登录"""

    def test_login_success(self, auth_client):
        """正常登录 → 返回 token"""
        client, token, username = auth_client
        assert token
        assert username == "testuser"

    def test_login_wrong_password(self, client):
        """密码错误 → 401"""
        # 先注册
        client.post(
            "/api/auth/register",
            json={"username": "dave", "password": "correct123"},
        )
        # 用错密码登录
        resp = client.post(
            "/api/auth/login",
            json={"username": "dave", "password": "wrongpassword"},
        )
        assert resp.status_code == 401
        assert "用户名或密码错误" in resp.json()["detail"]

    def test_login_not_exist(self, client):
        """用户不存在 → 401"""
        resp = client.post(
            "/api/auth/login",
            json={"username": "ghost", "password": "whatever"},
        )
        assert resp.status_code == 401


class TestGetMe:
    """获取当前用户"""

    def test_get_me_with_token(self, auth_client):
        """有效 token → 返回用户信息"""
        client, token, username = auth_client
        resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["username"] == username
        assert "id" in data

    def test_get_me_without_token(self, client):
        """无 token → 403"""
        resp = client.get("/api/auth/me")
        assert resp.status_code == 403

    def test_get_me_bad_token(self, client):
        """无效 token → 401"""
        resp = client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer this-is-fake-token"},
        )
        assert resp.status_code == 401
