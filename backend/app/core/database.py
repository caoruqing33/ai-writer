"""数据库连接 —— SQLAlchemy 引擎、会话、模型基类"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from .config import DATABASE_URL

# 引擎 —— 负责跟数据库文件通信
# check_same_thread=False 是 SQLite 特有的，允许多个请求用同一个连接
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# 会话工厂 —— 每次请求创建一个 Session，用完关掉
SessionLocal = sessionmaker(bind=engine, autoflush=False)

# 基类 —— 所有模型继承它，SQLAlchemy 就能识别
class Base(DeclarativeBase):
    pass


def get_db():
    """FastAPI 依赖注入用：每次请求给一个数据库会话，用完自动关"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
