import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # OpenAI配置
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    
    # 服务器配置
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", 8000))
    DEBUG = os.getenv("DEBUG", "true").lower() == "true"
    
    # 可观测性配置
    OBSERVABILITY_DB_PATH = os.getenv("OBSERVABILITY_DB_PATH", "agent_observability.db")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

