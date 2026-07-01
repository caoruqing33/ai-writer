"""文章相关接口 —— 增删改查，全挂载在 /api 下"""
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from app.core.database import get_db
from app.models import Project, Article

router = APIRouter(tags=["文章"])

# 允许的状态/步骤/模式值（防止写入脏数据）
ARTICLE_STATUSES = Literal["draft", "writing", "completed"]
WORKFLOW_STEPS = Literal["specify", "topic", "write", "review"]
WRITING_MODES = Literal["coach", "fast", "hybrid"]

# ============ Pydantic 请求/响应模型 ============

class ArticleCreate(BaseModel):
    """创建文章时只需要一个标题"""
    title: str = Field(..., min_length=1, max_length=200)


class ArticleUpdate(BaseModel):
    """更新文章 —— 所有字段都是可选的，传哪个改哪个"""
    title: str | None = Field(None, min_length=1, max_length=200)
    status: ARTICLE_STATUSES | None = None           # draft / writing / completed
    workflow_step: WORKFLOW_STEPS | None = None       # 当前步骤
    writing_mode: WRITING_MODES | None = None          # coach / fast / hybrid
    brief: str | None = None             # 需求说明
    draft: str | None = None             # 正文草稿
    word_count: int | None = Field(None, ge=0)        # 字数统计


class ArticleResponse(BaseModel):
    """返回给前端的文章数据"""
    id: int
    project_id: int
    title: str
    status: str
    workflow_step: str
    writing_mode: str | None
    brief: str | None
    draft: str | None
    word_count: int
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


def _to_response(article: Article) -> dict:
    """把 ORM 对象转成字典（isort 格式化时间字段）"""
    return {
        "id": article.id,
        "project_id": article.project_id,
        "title": article.title,
        "status": article.status,
        "workflow_step": article.workflow_step,
        "writing_mode": article.writing_mode,
        "brief": article.brief,
        "draft": article.draft,
        "word_count": article.word_count,
        "created_at": article.created_at.isoformat() if article.created_at else "",
        "updated_at": article.updated_at.isoformat() if article.updated_at else "",
    }


# ============ 接口 ============

@router.get("/projects/{project_id}/articles", response_model=list[ArticleResponse])
def list_articles(project_id: int, db: Session = Depends(get_db)):
    """获取某个项目下的所有文章"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    return [_to_response(a) for a in project.articles]


@router.post("/projects/{project_id}/articles", response_model=ArticleResponse, status_code=201)
def create_article(project_id: int, data: ArticleCreate, db: Session = Depends(get_db)):
    """在某个项目下创建新文章"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    article = Article(title=data.title, project_id=project_id)
    db.add(article)
    db.commit()
    db.refresh(article)
    return _to_response(article)


@router.get("/articles/{article_id}", response_model=ArticleResponse)
def get_article(article_id: int, db: Session = Depends(get_db)):
    """获取单篇文章详情"""
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="文章不存在")
    return _to_response(article)


@router.patch("/articles/{article_id}", response_model=ArticleResponse)
def update_article(article_id: int, data: ArticleUpdate, db: Session = Depends(get_db)):
    """更新文章 —— 传什么更新什么（部分更新）"""
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="文章不存在")

    # 只更新传了值的字段（dict(exclude_unset=True) 自动跳过 None）
    update_data = data.model_dump(exclude_unset=True)

    # 如果更新了 draft 但没有传 word_count，自动计算字数
    if "draft" in update_data and "word_count" not in update_data:
        raw = update_data["draft"] or ""
        # 统计非空白字符数（中文一个字=1，英文单词不算，简单处理）
        update_data["word_count"] = len(raw.replace("\n", "").replace(" ", ""))

    for field, value in update_data.items():
        setattr(article, field, value)

    db.commit()
    db.refresh(article)
    return _to_response(article)


@router.delete("/articles/{article_id}", status_code=204)
def delete_article(article_id: int, db: Session = Depends(get_db)):
    """删除文章（并级联删除其下所有消息）"""
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="文章不存在")
    db.delete(article)
    db.commit()
    return None
