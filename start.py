#!/usr/bin/env python3
"""
Palantir AI Agent System 启动脚本
"""

import os
import sys
import uvicorn
from pathlib import Path

def main():
    """启动应用"""
    # 检查环境变量
    if not os.getenv("OPENAI_API_KEY"):
        print("警告: 未设置 OPENAI_API_KEY 环境变量")
        print("请在 .env 文件中设置您的 OpenAI API Key")
    
    # 创建必要的目录
    Path("static").mkdir(exist_ok=True)
    Path("logs").mkdir(exist_ok=True)
    
    print("🚀 启动 Palantir AI Agent System...")
    print("📝 前端界面: http://localhost:8000/static/index.html")
    print("🔧 API文档: http://localhost:8000/docs")
    print("📊 健康检查: http://localhost:8000/health")
    print("\n按 Ctrl+C 停止服务")
    
    # 启动服务
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    main()
