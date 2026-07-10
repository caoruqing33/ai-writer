"""文章模块测试 —— 创建、更新、自动字数统计、删除"""

from .conftest import auth_headers


# ── 辅助：创建一个有项目的测试环境 ──
def _create_project_and_article(auth_client):
    """创建项目 + 文章，返回 (client, token, project_id, article_id)"""
    client, token, _ = auth_client
    h = auth_headers(token)

    proj_resp = client.post(
        "/api/projects", json={"name": "测试项目"}, headers=h
    )
    pid = proj_resp.json()["id"]

    art_resp = client.post(
        f"/api/projects/{pid}/articles",
        json={"title": "测试文章"},
        headers=h,
    )
    aid = art_resp.json()["id"]
    return client, token, pid, aid


class TestCreateArticle:
    """创建文章"""

    def test_create_success(self, auth_client):
        """在项目下创建文章"""
        client, token, pid, _ = _create_project_and_article(auth_client)
        h = auth_headers(token)

        resp = client.post(
            f"/api/projects/{pid}/articles",
            json={"title": "Python 入门指南"},
            headers=h,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["title"] == "Python 入门指南"
        assert data["status"] == "draft"
        assert data["workflow_step"] == "specify"
        assert data["word_count"] == 0

    def test_create_in_nonexistent_project(self, auth_client):
        """在不存在项目下创建 → 404"""
        client, token, _ = auth_client
        resp = client.post(
            "/api/projects/99999/articles",
            json={"title": "Ghost Article"},
            headers=auth_headers(token),
        )
        assert resp.status_code == 404


class TestListArticles:
    """查询文章列表"""

    def test_list(self, auth_client):
        """列出项目下所有文章"""
        client, token, pid, _ = _create_project_and_article(auth_client)
        h = auth_headers(token)

        resp = client.get(f"/api/projects/{pid}/articles", headers=h)
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["title"] == "测试文章"


class TestUpdateArticle:
    """更新文章"""

    def test_update_title(self, auth_client):
        """更新标题"""
        client, token, _, aid = _create_project_and_article(auth_client)
        h = auth_headers(token)

        resp = client.patch(
            f"/api/articles/{aid}",
            json={"title": "新标题"},
            headers=h,
        )
        assert resp.status_code == 200
        assert resp.json()["title"] == "新标题"

    def test_update_status_and_mode(self, auth_client):
        """更新状态和写作模式"""
        client, token, _, aid = _create_project_and_article(auth_client)
        h = auth_headers(token)

        resp = client.patch(
            f"/api/articles/{aid}",
            json={"status": "writing", "writing_mode": "coach"},
            headers=h,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "writing"
        assert data["writing_mode"] == "coach"

    def test_auto_word_count(self, auth_client):
        """保存草稿时自动统计字数（非空白字符）"""
        client, token, _, aid = _create_project_and_article(auth_client)
        h = auth_headers(token)

        # 30 个非空白字符（中文每个字算 1 个）
        text = "Python 是一门优雅的语言。" * 2  # 13*2=26 chars, 22 non-space
        resp = client.patch(
            f"/api/articles/{aid}",
            json={"draft": text},
            headers=h,
        )
        assert resp.status_code == 200
        word_count = resp.json()["word_count"]
        # 应该自动计算了，不为 0
        assert word_count > 0

    def test_partial_update_only_changes_sent_fields(self, auth_client):
        """PATCH 只更新传了的字段，不传的不变"""
        client, token, _, aid = _create_project_and_article(auth_client)
        h = auth_headers(token)

        # 只改标题，状态应该保持不变
        resp = client.patch(
            f"/api/articles/{aid}",
            json={"title": "只改标题"},
            headers=h,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["title"] == "只改标题"
        assert data["status"] == "draft"  # 没变
        assert data["workflow_step"] == "specify"  # 没变


class TestDeleteArticle:
    """删除文章"""

    def test_delete_success(self, auth_client):
        """删除 → 204"""
        client, token, _, aid = _create_project_and_article(auth_client)
        h = auth_headers(token)

        resp = client.delete(f"/api/articles/{aid}", headers=h)
        assert resp.status_code == 204

        # 确认已删除
        resp = client.get(f"/api/articles/{aid}", headers=h)
        assert resp.status_code == 404
