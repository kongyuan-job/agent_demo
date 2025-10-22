from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from datetime import datetime
from pathlib import Path

from config import Config
from api.routes import agents, chat, observability, utils

# 创建FastAPI应用
app = FastAPI(
    title="Palantir AI Agent System",
    description="动态AI Agent创建和管理平台",
    version="1.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境中应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files directory
static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Register API routers
app.include_router(agents.router)
app.include_router(chat.router)
app.include_router(observability.router)
app.include_router(utils.router)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Palantir AI Agent System",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=Config.HOST,
        port=Config.PORT,
        reload=Config.DEBUG
    )

