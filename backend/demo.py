"""使用示例 —— 完整走一遍 AI 写作流程"""
import requests
import json

BASE = "http://localhost:8000/api"


def demo():
    print("=" * 50)
    print("  AI Writer 使用演示")
    print("=" * 50)

    # 1. 创建项目
    print("\n📁 1. 创建项目...")
    r = requests.post(f"{BASE}/projects", json={"name": "技术博客", "workspace_type": "wechat"})
    project = r.json()
    pid = project["id"]
    print(f"   项目ID: {pid} — {project['name']}")

    # 2. 创建文章
    print("\n📝 2. 创建文章...")
    r = requests.post(f"{BASE}/projects/{pid}/articles", json={"title": "Python 入门指南"})
    article = r.json()
    aid = article["id"]
    print(f"   文章ID: {aid} — {article['title']}")

    # 3. 写需求
    print("\n🎯 3. 设置写作需求...")
    requests.patch(f"{BASE}/articles/{aid}", json={
        "brief": "面向零基础读者的 Python 学习路线文章，3000字左右，口语化"
    })
    print("   需求已保存")

    # 4. AI 对话（快速模式）
    print("\n🤖 4. AI 对话（快速模式）...")
    print("   等待 AI 回复（流式输出）:")
    print("   ", end="", flush=True)

    r = requests.post(
        f"{BASE}/articles/{aid}/chat",
        json={"content": "帮我写一篇 Python 入门指南，面向零基础读者", "mode": "fast"},
        stream=True,
        timeout=60,
    )

    for line in r.iter_lines():
        if not line:
            continue
        line = line.decode("utf-8")
        if line.startswith("data: "):
            data = json.loads(line[6:])
            if "token" in data:
                print(data["token"], end="", flush=True)
            elif data.get("done"):
                print("\n\n   ✅ AI 回复完成！")
            elif "error" in data:
                print(f"\n   ❌ 错误: {data['error']}")

    # 5. 查文章状态
    print("\n📊 5. 文章当前状态...")
    r = requests.get(f"{BASE}/articles/{aid}")
    a = r.json()
    print(f"   标题: {a['title']}")
    print(f"   步骤: {a['workflow_step']}")
    print(f"   模式: {a['writing_mode']}")
    print(f"   字数: {a['word_count']}")

    # 6. 查看历史消息
    print(f"\n💬 6. 对话记录...")
    r = requests.get(f"{BASE}/articles/{aid}/messages")
    messages = r.json()
    for m in messages:
        role = "👤 你" if m["role"] == "user" else "🤖 AI"
        preview = m["content"][:60].replace("\n", " ")
        print(f"   {role}: {preview}...")

    print(f"\n{'=' * 50}")
    print(f"  完成！一共 {len(messages)} 条消息")
    print(f"{'=' * 50}")


if __name__ == "__main__":
    demo()
