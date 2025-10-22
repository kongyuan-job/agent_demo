# 🚀 快速启动指南

## 1. 环境准备

### 推荐：使用虚拟环境
```bash
# 创建虚拟环境
python -m venv palantir_env

# 激活虚拟环境
# Windows:
palantir_env\Scripts\activate
# Linux/Mac:
source palantir_env/bin/activate
```

### 安装Python依赖
```bash
# 方法1: 使用安装脚本（推荐）
python install.py

# 方法2: 手动安装
pip install -r requirements.txt
```

**注意**: 如果遇到依赖冲突，请使用安装脚本 `python install.py`，它会按正确顺序安装兼容的版本。

### 验证安装
安装完成后，可以运行验证脚本：
```bash
python verify_installation.py
```

### 配置环境变量
复制 `env_example.txt` 为 `.env` 并填入您的OpenAI API Key：
```bash
cp env_example.txt .env
```

编辑 `.env` 文件：
```
OPENAI_API_KEY=your_actual_openai_api_key_here
```

## 2. 启动服务

```bash
python start.py
```

## 3. 访问系统

- **前端界面**: http://localhost:8000/static/index.html
- **API文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/health

## 4. 创建您的第一个Agent

1. 打开前端界面
2. 点击"创建Agent"按钮
3. 填写基础信息：
   - 名称：客服助手
   - 描述：专业的在线客服助手
   - 系统提示词：你是一个专业的在线客服助手，请礼貌、耐心地回答用户问题。
4. 点击"创建"按钮
5. 在Agent列表中点击"测试"按钮开始对话

## 5. API调用示例

```python
import requests

# 创建Agent
response = requests.post('http://localhost:8000/api/agents', json={
    "name": "我的助手",
    "description": "一个有用的助手",
    "system_prompt": "你是一个有用的助手。",
    "user_prompt_template": "{user_input}",
    "input_format": [],
    "output_format": [],
    "tools": []
})

agent_id = response.json()["data"]["agent_id"]

# 与Agent对话
response = requests.post('http://localhost:8000/api/chat', json={
    "agent_id": agent_id,
    "user_input": "你好！"
})

print(response.json()["response"])
```

## 6. 测试系统

运行测试脚本验证系统功能：
```bash
# 完整功能测试
python test_complete.py

# 可观测性功能测试
python test_observability.py
```

## 常见问题

### Q: 启动时提示缺少OpenAI API Key
A: 请确保在 `.env` 文件中正确设置了 `OPENAI_API_KEY`

### Q: 前端页面无法访问
A: 确保服务已启动，端口8000未被占用

### Q: Agent对话没有响应
A: 检查OpenAI API Key是否有效，网络连接是否正常

## 下一步

- 查看 [README.md](README.md) 了解详细功能
- 探索API文档了解所有可用接口
- 根据需要扩展工具和功能
