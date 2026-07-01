"""文章表 —— 核心表，一篇文章的全部状态都在这里"""
from datetime import datetime, timezone
from sqlalchemy import String, Integer, Text, DateTime, ForeignKey, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


def _utcnow():
    """返回 naive UTC 时间（SQLite 不存时区，替代废弃的 datetime.utcnow）"""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Article(Base):
    __tablename__ = "articles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(Integer, ForeignKey("projects.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)

    # 状态
    status: Mapped[str] = mapped_column(String(20), default="draft")       # draft / writing / completed
    workflow_step: Mapped[str] = mapped_column(String(20), default="specify")  # 当前在哪一步
    writing_mode: Mapped[str | None] = mapped_column(String(20), nullable=True)  # coach / fast

    # 内容（大文本字段，存 Markdown）
    brief: Mapped[str | None] = mapped_column(Text, nullable=True)         # 需求说明
    draft: Mapped[str | None] = mapped_column(Text, nullable=True)         # 文章正文

    # 统计
    word_count: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)

    # 关系
    project = relationship("Project", back_populates="articles")
    messages = relationship("Message", back_populates="article", cascade="all, delete-orphan",
                            order_by="Message.created_at")
