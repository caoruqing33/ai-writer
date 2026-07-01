"""格式化接口 —— Markdown 转各平台格式"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.core.database import get_db
from app.models import Article
from app.services.wechat_formatter import markdown_to_wechat_html

router = APIRouter(tags=["格式化"])


class FormatResponse(BaseModel):
    """返回格式化后的 HTML"""
    html: str
    title: str


@router.get("/articles/{article_id}/wechat-export", response_model=FormatResponse)
def export_wechat(article_id: int, db: Session = Depends(get_db)):
    """导出文章为微信格式 HTML，可直接复制粘贴到公众号编辑器"""
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="文章不存在")

    if not article.draft:
        raise HTTPException(status_code=400, detail="文章还没有草稿内容，请先写作")

    html = markdown_to_wechat_html(article.draft, title=article.title)
    return {"html": html, "title": article.title}


class ArbitraryFormatRequest(BaseModel):
    """任意 Markdown 文本格式化请求"""
    markdown: str
    title: str = ""

@router.post("/format/wechat", response_model=FormatResponse)
def format_arbitrary_markdown(data: ArbitraryFormatRequest):
    """将任意 Markdown 文本转为微信格式（不依赖文章ID）"""
    if not data.markdown.strip():
        raise HTTPException(status_code=400, detail="Markdown 内容不能为空")
    html = markdown_to_wechat_html(data.markdown, title=data.title)
    return {"html": html, "title": data.title or "微信文章"}
