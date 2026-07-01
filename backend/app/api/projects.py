"""项目相关接口 —— GET/POST/DELETE"""
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from app.core.database import get_db
from app.models import Project

router = APIRouter(tags=["项目"])

WORKSPACE_TYPES = Literal["wechat", "video", "general"]

# ============ 请求/响应模型（Pydantic）============

class ProjectCreate(BaseModel):
    """创建项目时前端传过来的数据"""
    name: str = Field(..., min_length=1, max_length=100)
    workspace_type: WORKSPACE_TYPES = "wechat"  # wechat / video / general


class ProjectResponse(BaseModel):
    """返回给前端的数据格式"""
    id: int
    name: str
    workspace_type: str
    article_count: int  # 这个项目下有多少篇文章

    model_config = {"from_attributes": True}  # ← 告诉 Pydantic 可以从 ORM 对象转


# ============ 接口 ============

@router.get("/projects", response_model=list[ProjectResponse])
def list_projects(db: Session = Depends(get_db)):
    """获取所有项目列表"""
    projects = db.query(Project).all()
    result = []
    for p in projects:
        result.append({
            "id": p.id,
            "name": p.name,
            "workspace_type": p.workspace_type,
            "article_count": len(p.articles),
        })
    return result


@router.post("/projects", response_model=ProjectResponse, status_code=201)
def create_project(data: ProjectCreate, db: Session = Depends(get_db)):
    """创建新项目"""
    project = Project(name=data.name, workspace_type=data.workspace_type)
    db.add(project)
    db.commit()
    db.refresh(project)  # 刷新以获取自增 id
    return {
        "id": project.id,
        "name": project.name,
        "workspace_type": project.workspace_type,
        "article_count": 0,
    }


@router.get("/projects/{project_id}", response_model=ProjectResponse)
def get_project(project_id: int, db: Session = Depends(get_db)):
    """获取单个项目详情"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    return {
        "id": project.id,
        "name": project.name,
        "workspace_type": project.workspace_type,
        "article_count": len(project.articles),
    }


@router.delete("/projects/{project_id}", status_code=204)
def delete_project(project_id: int, db: Session = Depends(get_db)):
    """删除项目（会级联删除下面所有文章和消息）"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    db.delete(project)
    db.commit()
    return None  # 204 No Content
