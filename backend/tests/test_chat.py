"""AI 对话模块测试 —— 核心功能，Mock OpenAI 避免真实 API 调用"""
import json
from unittest.mock import patch, MagicMock

from .conftest import auth_headers


# ── 辅助：Mock OpenAI 流式响应 ──
def _mock_stream_chunks(tokens: list[str]):
    """生成假的 SSE chunk 对象列表，模拟 OpenAI streaming 返回"""
    chunks = []
    for t in tokens:
        chunk = MagicMock()
        # 模拟 chunk.choices[0].delta.content
        delta = MagicMock()
        delta.content = t
        choice = MagicMock()
        choice.delta = delta
        chunk.choices = [choice]
        chunks.append(chunk)
    return chunks


# ── 辅助：创建文章 + 准备聊天 ──
def _setup_chat(auth_client, mode="coach"):
    """创建项目 + 文章，返回 (client, token, article_id)"""
    client, token, _ = auth_client
    h = auth_headers(token)

    proj = client.post("/api/projects", json={"name": "写作测试"}, headers=h)
    pid = proj.json()["id"]

    art = client.post(
        f"/api/projects/{pid}/articles",
        json={"title": "AI 对话测试文章"},
        headers=h,
    )
    aid = art.json()["id"]

    # 设置写作模式
    if mode != "coach":
        client.patch(
            f"/api/articles/{aid}",
            json={"writing_mode": mode},
            headers=h,
        )

    return client, token, aid


class TestChatStreaming:
    """SSE 流式对话"""

    def test_coach_mode_returns_sse_stream(self, auth_client):
        """教练模式：发消息 → 收到 SSE 流式 token → AI 回复保存到数据库"""
        client, token, aid = _setup_chat(auth_client, "coach")
        h = auth_headers(token)

        with patch("app.api.chat.OpenAI") as mock_openai_cls:
            # 设置 mock
            mock_instance = MagicMock()
            mock_instance.chat.completions.create.return_value = _mock_stream_chunks(
                ["你", "想", "写", "什", "么", "主", "题", "呢", "？"]
            )
            mock_openai_cls.return_value = mock_instance

            resp = client.post(
                f"/api/articles/{aid}/chat",
                json={"content": "我想写一篇技术文章"},
                headers=h,
            )

            # 断言 SSE content-type
            assert resp.status_code == 200
            assert "text/event-stream" in resp.headers["content-type"]

            # 解析 SSE 事件
            tokens = []
            for line in resp.iter_lines():
                if line and line.startswith("data: "):
                    data = json.loads(line[6:])
                    if "token" in data:
                        tokens.append(data["token"])
                    elif data.get("done"):
                        break

            # 断言 token 正确
            full = "".join(tokens)
            assert "你想写什么主题呢" in full
            assert data.get("done") is True

    def test_fast_mode_stream_to_editor(self, auth_client):
        """快速模式：stream_to_editor 标记为 True"""
        client, token, aid = _setup_chat(auth_client, "fast")
        h = auth_headers(token)

        with patch("app.api.chat.OpenAI") as mock_openai_cls:
            mock_instance = MagicMock()
            mock_instance.chat.completions.create.return_value = _mock_stream_chunks(
                ["#", " ", "Python", "入", "门"]
            )
            mock_openai_cls.return_value = mock_instance

            resp = client.post(
                f"/api/articles/{aid}/chat",
                json={"content": "写一篇 Python 入门"},
                headers=h,
            )

            # 检查第一个 token 带有 stream_to_editor
            first_event = None
            for line in resp.iter_lines():
                if line and line.startswith("data: "):
                    first_event = json.loads(line[6:])
                    break

            assert first_event is not None
            # 快速模式应该 stream_to_editor=True
            assert first_event.get("stream_to_editor") is True

    def test_coach_mode_stream_to_chat_panel(self, auth_client):
        """教练模式：stream_to_editor 为 False（输出到对话框）"""
        client, token, aid = _setup_chat(auth_client, "coach")
        h = auth_headers(token)

        with patch("app.api.chat.OpenAI") as mock_openai_cls:
            mock_instance = MagicMock()
            mock_instance.chat.completions.create.return_value = _mock_stream_chunks(
                ["你", "好"]
            )
            mock_openai_cls.return_value = mock_instance

            resp = client.post(
                f"/api/articles/{aid}/chat",
                json={"content": "你好"},
                headers=h,
            )

            first_event = None
            for line in resp.iter_lines():
                if line and line.startswith("data: "):
                    first_event = json.loads(line[6:])
                    break

            # 教练模式 stream_to_editor=False
            assert first_event.get("stream_to_editor") is False


class TestChatMessageHistory:
    """消息历史"""

    def test_save_user_message_and_ai_reply(self, auth_client):
        """发消息后，数据库中保存了 user + assistant 两条消息"""
        client, token, aid = _setup_chat(auth_client, "fast")
        h = auth_headers(token)

        with patch("app.api.chat.OpenAI") as mock_openai_cls:
            mock_instance = MagicMock()
            mock_instance.chat.completions.create.return_value = _mock_stream_chunks(
                ["AI", "回", "复"]
            )
            mock_openai_cls.return_value = mock_instance

            # 发消息
            client.post(
                f"/api/articles/{aid}/chat",
                json={"content": "帮我写"},
                headers=h,
            )

        # 查历史
        resp = client.get(f"/api/articles/{aid}/messages", headers=h)
        assert resp.status_code == 200
        messages = resp.json()
        assert len(messages) >= 2
        assert messages[0]["role"] == "user"
        assert messages[0]["content"] == "帮我写"
        assert messages[1]["role"] == "assistant"
        assert "AI回复" in messages[1]["content"]

    def test_clear_messages(self, auth_client):
        """清空消息 → 历史为空"""
        client, token, aid = _setup_chat(auth_client, "fast")
        h = auth_headers(token)

        # 先发一条
        with patch("app.api.chat.OpenAI") as mock_openai_cls:
            mock_instance = MagicMock()
            mock_instance.chat.completions.create.return_value = _mock_stream_chunks(
                ["OK"]
            )
            mock_openai_cls.return_value = mock_instance
            client.post(
                f"/api/articles/{aid}/chat",
                json={"content": "test"},
                headers=h,
            )

        # 清空
        resp = client.delete(f"/api/articles/{aid}/messages", headers=h)
        assert resp.status_code == 204

        # 确认空了
        resp = client.get(f"/api/articles/{aid}/messages", headers=h)
        assert resp.json() == []


class TestChatEdgeCases:
    """边界情况"""

    def test_chat_no_api_key(self, auth_client):
        """未配置 API Key → 500"""
        client, token, aid = _setup_chat(auth_client)
        h = auth_headers(token)

        # 临时清空 AI_API_KEY
        import app.api.chat as chat_module
        import app.core.config as config

        original_key = config.AI_API_KEY
        config.AI_API_KEY = ""
        # 也需要更新 chat 模块中的引用（因为 from import 是快照）
        chat_module.AI_API_KEY = ""

        try:
            resp = client.post(
                f"/api/articles/{aid}/chat",
                json={"content": "test"},
                headers=h,
            )
            assert resp.status_code == 500
            assert "AI_API_KEY" in resp.json()["detail"]
        finally:
            # 恢复
            config.AI_API_KEY = original_key
            chat_module.AI_API_KEY = original_key

    def test_chat_article_not_found(self, auth_client):
        """对话不存在的文章 → 404"""
        client, token, _ = auth_client
        resp = client.post(
            "/api/articles/99999/chat",
            json={"content": "hello"},
            headers=auth_headers(token),
        )
        assert resp.status_code == 404

    def test_chat_empty_content(self, auth_client):
        """空内容 → 422"""
        client, token, aid = _setup_chat(auth_client)
        resp = client.post(
            f"/api/articles/{aid}/chat",
            json={"content": ""},
            headers=auth_headers(token),
        )
        assert resp.status_code == 422
