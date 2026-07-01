"""应用配置 —— 从 .env 文件读取，没有则用默认值"""
import os
from dotenv import load_dotenv

load_dotenv()  # 加载 backend/.env 文件

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./ai_writer.db")
AI_API_KEY = os.getenv("AI_API_KEY", "")
AI_BASE_URL = os.getenv("AI_BASE_URL", "https://api.deepseek.com")
AI_MODEL = os.getenv("AI_MODEL", "deepseek-chat")

# JWT 认证配置
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-me-in-production")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "1440"))

# 注册开关：设为 "false" 可关闭公开注册（"true" / "false"）
REGISTRATION_ENABLED = os.getenv("REGISTRATION_ENABLED", "true").lower() in ("true", "1", "yes")
