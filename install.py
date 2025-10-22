#!/usr/bin/env python3
"""
依赖安装脚本 - 解决版本冲突问题
"""

import subprocess
import sys
import os

def run_command(command, description):
    """运行命令并处理错误"""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} 成功")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} 失败:")
        print(f"   错误: {e.stderr}")
        return False

def main():
    """主安装流程"""
    print("🚀 Palantir AI Agent System 依赖安装脚本")
    print("=" * 50)
    
    # 检查Python版本
    python_version = sys.version_info
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 8):
        print("❌ 错误: 需要Python 3.8或更高版本")
        sys.exit(1)
    
    print(f"✅ Python版本检查通过: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    # 建议创建虚拟环境
    print("\n💡 建议创建虚拟环境以避免依赖冲突:")
    print("   python -m venv palantir_env")
    print("   # Windows:")
    print("   palantir_env\\Scripts\\activate")
    print("   # Linux/Mac:")
    print("   source palantir_env/bin/activate")
    
    # 升级pip
    if not run_command(f"{sys.executable} -m pip install --upgrade pip", "升级pip"):
        print("⚠️ pip升级失败，继续安装依赖...")
    
    # 安装核心依赖
    print("\n📦 安装核心依赖包...")
    packages = [
        "fastapi==0.104.1",
        "uvicorn==0.24.0", 
        "pydantic==2.7.4",
        "python-dotenv==1.0.0",
        "httpx==0.25.2",
        "python-multipart==0.0.6",
        "jinja2==3.1.2",
        "aiofiles==23.2.1"
    ]
    
    for package in packages:
        if not run_command(f"{sys.executable} -m pip install {package}", f"安装 {package}"):
            print(f"⚠️ {package} 安装失败")
    
    # 安装LangChain相关包
    print("\n🤖 安装LangChain相关包...")
    langchain_packages = [
        "langchain-core==0.3.15",
        "langchain-openai==0.2.0", 
        "langchain==0.3.3",
        "langgraph==0.2.45",
        "openai==1.40.0"
    ]
    
    for package in langchain_packages:
        if not run_command(f"{sys.executable} -m pip install {package}", f"安装 {package}"):
            print(f"⚠️ {package} 安装失败")
    
    print("\n" + "=" * 50)
    print("🎉 依赖安装完成!")
    print("\n📝 下一步:")
    print("1. 复制 env_example.txt 为 .env 并填入您的OpenAI API Key")
    print("2. 运行 python start.py 启动服务")
    print("3. 访问 http://localhost:8000/static/index.html 使用系统")

if __name__ == "__main__":
    main()
