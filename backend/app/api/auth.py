"""认证接口 —— 注册、登录、获取当前用户"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.core.database import get_db
from app.core.auth import hash_password, verify_password, create_access_token, get_current_user
from app.core.config import REGISTRATION_ENABLED
from app.models import User

router = APIRouter(tags=["认证"])


# ============ 请求/响应模型 ============

class AuthRequest(BaseModel):
    """注册或登录请求"""
    username: str
    password: str


class AuthResponse(BaseModel):
    """返回 token 和用户信息"""
    access_token: str
    token_type: str = "bearer"
    username: str


class UserResponse(BaseModel):
    """当前用户信息"""
    id: int
    username: str


# ============ 接口 ============

@router.post("/auth/register", response_model=AuthResponse, status_code=201)
def register(data: AuthRequest, db: Session = Depends(get_db)):
    """注册新用户，成功后直接返回 JWT token（自动登录）"""
    # 检查是否开放注册
    if not REGISTRATION_ENABLED:
        raise HTTPException(status_code=403, detail="当前不开放公开注册")

    # 检查用户名是否已存在
    existing = db.query(User).filter(User.username == data.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="用户名已被注册")

    # 校验密码长度
    if len(data.password) < 6:
        raise HTTPException(status_code=400, detail="密码至少需要 6 位")

    # 创建用户
    user = User(
        username=data.username,
        hashed_password=hash_password(data.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # 生成 token（sub 存用户 ID）
    token = create_access_token({"sub": user.id})
    return {"access_token": token, "token_type": "bearer", "username": user.username}


@router.post("/auth/login", response_model=AuthResponse)
def login(data: AuthRequest, db: Session = Depends(get_db)):
    """用户名 + 密码登录，返回 JWT token"""
    # 查找用户
    user = db.query(User).filter(User.username == data.username).first()
    if not user:
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    # 验证密码
    if not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    token = create_access_token({"sub": user.id})
    return {"access_token": token, "token_type": "bearer", "username": user.username}


@router.get("/auth/me", response_model=UserResponse)
def get_me(user: User = Depends(get_current_user)):
    """获取当前登录用户信息（用于前端验证 token 是否有效）"""
    return {"id": user.id, "username": user.username}
