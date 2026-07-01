"""项目表 —— 一个项目对应一个写作主题/工作区"""
from datetime import datetime, timezone
from sqlalchemy import String, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


def _utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    workspace_type: Mapped[str] = mapped_column(String(20), default="wechat")  # wechat / video / general
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    # 关系：一个项目下有多篇文章
    articles = relationship("Article", back_populates="project", cascade="all, delete-orphan")
