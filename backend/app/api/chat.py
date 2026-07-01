"""AI 对话接口 —— 历史消息查询 + SSE 流式聊天（核心功能）"""
import json
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
import httpx
from openai import OpenAI
from app.core.database import get_db
from app.core.config import AI_API_KEY, AI_BASE_URL, AI_MODEL
from app.models import Article, Message

router = APIRouter(tags=["AI 对话"])


# ============ 请求/响应模型 ============

class ChatRequest(BaseModel):
    """用户发消息的内容 + 可选指定模式"""
    content: str = Field(..., min_length=1, max_length=10000)
    mode: Literal["coach", "fast", "hybrid"] | None = None  # 不传就用文章当前模式


class MessageResponse(BaseModel):
    """单条消息"""
    id: int
    role: str
    content: str
    created_at: str

    model_config = {"from_attributes": True}


# ============ 历史消息查询 ============

@router.get("/articles/{article_id}/messages", response_model=list[MessageResponse])
def list_messages(article_id: int, db: Session = Depends(get_db)):
    """获取某篇文章的历史对话"""
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="文章不存在")

    messages = db.query(Message).filter(
        Message.article_id == article_id
    ).order_by(Message.created_at).all()

    return [
        {
            "id": m.id,
            "role": m.role,
            "content": m.content,
            "created_at": m.created_at.isoformat(),
        }
        for m in messages
    ]


@router.delete("/articles/{article_id}/messages", status_code=204)
def clear_messages(article_id: int, db: Session = Depends(get_db)):
    """清空某篇文章的所有对话记录，重新开始"""
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="文章不存在")

    deleted = db.query(Message).filter(
        Message.article_id == article_id
    ).delete()
    db.commit()
    return None


# ============ AI 对话（SSE 流式）⭐ 核心 ============

# 系统提示词 —— 教练模式
COACH_SYSTEM_PROMPT = """你是一位专业的写作教练。你的职责是引导用户自己写出真实、有温度的文章，而不是替用户写。

## 核心原则
- **绝对禁止**：替用户生成任何可直接使用的段落、句子
- **绝对禁止**：说"我帮你写"、"你可以这样写"、提供示例段落
- **可以做**：提出引导问题、检查用户写的内容、给出修改建议、建议文章结构

## 对话方式
1. 先理解用户想写什么主题
2. 提出 3-5 个具体问题，引导用户回忆真实经历和感受
3. 用户回答后，引导用户自己把这些素材写成段落
4. 用户写完后，检查：是否有套话、"一方面...另一方面..."等 AI 句式、空洞描述
5. 指出问题，让用户自己修改

## 反 AI 检测规则
- 不要用"综上所述""经过分析""显著提升"等套话
- 不要用对称结构（"不仅...而且...""一方面...另一方面..."）
- 不要堆砌形容词
- 要求用户用具体数字、具体场景、具体细节

记住：你是教练，不是代笔。文章必须由用户自己写出来。"""

# 系统提示词 —— 快速模式
FAST_SYSTEM_PROMPT = """你是一位专业的文章写手。根据用户提供的需求和参考资料，生成高质量的文章初稿。

## 写作要求
1. **口语化**：用自然的中文口语写作，像朋友聊天一样
2. **结构化**：有清晰的开头、正文、结尾
3. **具体**：避免空洞描述，优先使用具体案例和数字
4. **简洁**：段落简短（手机阅读友好），每段不超过 150 字

## 降低 AI 痕迹
- 使用"说实话""确实""我发现"等口语化连接词
- 避免"综上所述""经过分析""显著提升"等套话
- 避免对称句式（"一方面...另一方面..."）
- 适当使用反问句和短句
- 使用具体的例子而非抽象描述

## 工作方式
用户会提供文章主题、大纲或写作需求。你直接生成初稿，生成完后列出建议补充或修改的地方。"""

# 系统提示词 —— 半教练模式（混合模式）
HYBRID_SYSTEM_PROMPT = """你是一位贴心的写作伙伴，采用"先聊后写"的工作方式。

## 工作流程

### 阶段一：聊天摸底（像教练）
1. 理解用户想写什么主题
2. 提出 3-5 个具体问题，挖掘用户的真实经历、独特观点、具体案例
3. 根据用户的回答，和用户一起确定文章大纲和结构
4. 大纲要包含：每个段落的主题、要用到的真实素材、字数分配

### 阶段二：根据大纲写作（像写手）
**当用户确认大纲后**，根据大纲和聊天中收集的素材，生成完整初稿。

### 写作要求
1. **口语化**：用自然的中文口语，像朋友聊天
2. **必须用上用户提供的素材**：把用户说的真实经历、具体数字、独特观点全部融进去
3. **段落简短**：每段不超过 150 字，手机阅读友好
4. **降低 AI 痕迹**：
   - 用"说实话""确实""我发现""有意思的是"等口语连接词
   - 避免"综上所述""经过分析""一方面...另一方面..."
   - 用用户自己的话风，不要突然变书面
5. 生成完成后，列出你觉得用户可能需要补充的地方

### 关键原则
- 阶段一绝不写正文，只聊天和列大纲
- 必须等用户说"确认""可以""就这个大纲"之后，才能进入阶段二
- 进入阶段二后，基于大纲和用户素材一次性写完"""


def _get_system_prompt(mode: str | None) -> str:
    """根据写作模式返回对应的 System Prompt"""
    if mode == "fast":
        return FAST_SYSTEM_PROMPT
    elif mode == "hybrid":
        return HYBRID_SYSTEM_PROMPT
    else:
        return COACH_SYSTEM_PROMPT  # 默认教练模式


@router.post("/articles/{article_id}/chat")
async def chat_with_ai(article_id: int, data: ChatRequest, db: Session = Depends(get_db)):
    """发消息给 AI，SSE 流式返回回复。这是整个应用最核心的接口。"""

    # 1. 检查文章是否存在
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="文章不存在")

    # 2. 确定写作模式（优先用请求里传的，否则用文章当前模式）
    mode = data.mode or article.writing_mode or "coach"

    # 3. 保存用户消息
    user_msg = Message(article_id=article_id, role="user", content=data.content)
    db.add(user_msg)
    db.commit()

    # 4. 构建上下文：system prompt + 历史消息
    history = db.query(Message).filter(
        Message.article_id == article_id
    ).order_by(Message.created_at).all()

    context = [{"role": "system", "content": _get_system_prompt(mode)}]

    # 如果有 brief，作为额外上下文注入
    if article.brief:
        context.append({"role": "system", "content": f"用户的需求说明：{article.brief}"})

    # 如果有草稿，告诉 AI
    if article.draft:
        context.append({"role": "system", "content": f"当前草稿内容：{article.draft}"})

    # 拼接历史消息（取最近 30 条，防止超出 token 限制）
    for m in history[-30:]:
        context.append({"role": m.role, "content": m.content})

    # 5. 检查 API Key
    if not AI_API_KEY or AI_API_KEY == "your-deepseek-api-key-here":
        raise HTTPException(status_code=500, detail="请先在 .env 文件中配置 AI_API_KEY")

    # 6. 调 AI，流式返回
    client = OpenAI(
        api_key=AI_API_KEY,
        base_url=AI_BASE_URL,
        http_client=httpx.Client(proxy=None, timeout=60.0),  # 不走代理，避免超时
    )

    # 只有快速模式才将 AI 输出写入右侧编辑器（因为 AI 直接生成文章正文）
    # 教练/半教练模式的输出是"对话"，应显示在左侧对话框
    stream_to_editor = mode == "fast"

    async def generate():
        """SSE 生成器 —— 逐字推送 AI 回复"""
        full_response = ""
        first_token = True

        try:
            stream = client.chat.completions.create(
                model=AI_MODEL,
                messages=context,
                stream=True,
                temperature=0.7,
                max_tokens=4096,
                extra_body={"thinking": {"type": "disabled"}},  # 禁用深度思考，直接出正文
            )

            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    token = chunk.choices[0].delta.content
                    full_response += token
                    payload = {"token": token, "stream_to_editor": stream_to_editor}
                    yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
                    first_token = False

            # 流结束，发送完成信号
            yield f"data: {json.dumps({'done': True, 'full_text': full_response, 'stream_to_editor': stream_to_editor}, ensure_ascii=False)}\n\n"

            # 7. 保存 AI 回复到数据库
            assistant_msg = Message(article_id=article_id, role="assistant", content=full_response)
            db.add(assistant_msg)
            db.commit()

        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # 禁用 nginx 缓冲（部署时有用）
        },
    )
