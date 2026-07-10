"""项目模块测试 —— 创建、查询、删除"""

from .conftest import auth_headers


class TestCreateProject:
    """创建项目"""

    def test_create_default(self, auth_client):
        """创建项目，默认工作区类型"""
        client, token, _ = auth_client
        resp = client.post(
            "/api/projects",
            json={"name": "技术博客"},
            headers=auth_headers(token),
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "技术博客"
        assert data["workspace_type"] == "wechat"
        assert data["article_count"] == 0
        assert "id" in data

    def test_create_video_type(self, auth_client):
        """创建视频脚本工作区"""
        client, token, _ = auth_client
        resp = client.post(
            "/api/projects",
            json={"name": "视频号", "workspace_type": "video"},
            headers=auth_headers(token),
        )
        assert resp.status_code == 201
        assert resp.json()["workspace_type"] == "video"

    def test_create_empty_name(self, auth_client):
        """空项目名 → 422"""
        client, token, _ = auth_client
        resp = client.post(
            "/api/projects",
            json={"name": ""},
            headers=auth_headers(token),
        )
        assert resp.status_code == 422

    def test_create_without_auth(self, client):
        """未登录 → 403"""
        resp = client.post("/api/projects", json={"name": "test"})
        assert resp.status_code == 403


class TestListProjects:
    """查询项目列表"""

    def test_list_empty(self, auth_client):
        """无项目时返回空列表"""
        client, token, _ = auth_client
        resp = client.get("/api/projects", headers=auth_headers(token))
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_multiple(self, auth_client):
        """创建多个项目后能列出"""
        client, token, _ = auth_client
        h = auth_headers(token)
        client.post("/api/projects", json={"name": "项目A"}, headers=h)
        client.post("/api/projects", json={"name": "项目B"}, headers=h)

        resp = client.get("/api/projects", headers=h)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        assert data[0]["name"] == "项目A"
        assert data[1]["name"] == "项目B"


class TestGetProject:
    """获取单个项目"""

    def test_get_existing(self, auth_client):
        """存在的项目 → 返回详情"""
        client, token, _ = auth_client
        h = auth_headers(token)
        created = client.post("/api/projects", json={"name": "测试项目"}, headers=h)
        pid = created.json()["id"]

        resp = client.get(f"/api/projects/{pid}", headers=h)
        assert resp.status_code == 200
        assert resp.json()["name"] == "测试项目"

    def test_get_not_found(self, auth_client):
        """不存在的项目 → 404"""
        client, token, _ = auth_client
        resp = client.get("/api/projects/99999", headers=auth_headers(token))
        assert resp.status_code == 404


class TestDeleteProject:
    """删除项目"""

    def test_delete_success(self, auth_client):
        """删除 → 204，再次查询返回 404"""
        client, token, _ = auth_client
        h = auth_headers(token)
        created = client.post("/api/projects", json={"name": "待删除"}, headers=h)
        pid = created.json()["id"]

        resp = client.delete(f"/api/projects/{pid}", headers=h)
        assert resp.status_code == 204

        # 确认删掉了
        resp = client.get(f"/api/projects/{pid}", headers=h)
        assert resp.status_code == 404

    def test_delete_not_found(self, auth_client):
        """删除不存在的 → 404"""
        client, token, _ = auth_client
        resp = client.delete("/api/projects/99999", headers=auth_headers(token))
        assert resp.status_code == 404
