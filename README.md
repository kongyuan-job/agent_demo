# Palantir AI Agent System

一个基于LangGraph的动态AI Agent创建和管理平台，支持通过可视化界面配置Agent的核心定义、能力配置、测试验证和部署集成。

## 🎉 Recent Updates

**v2.0 - Code Architecture Optimization** (2025-10-22)
- ✅ Refactored monolithic code into modular architecture
- ✅ main.py reduced from 401 → 49 lines (-88%)
- ✅ agent_factory.py reduced from 853 → 578 lines (-32%)
- ✅ Created 19 focused modules with clear responsibilities
- ✅ Improved testability, maintainability, and scalability
- ✅ 100% backward compatible - no breaking changes!

📚 **See [REFACTORING_COMPLETE.md](docs/REFACTORING_COMPLETE.md) for details**

## 🌟 功能特性

- **可视化Agent配置**: 通过直观的界面配置Agent的基础信息、提示词、输入输出格式
- **动态输入输出**: 支持字符串、对象、数组等多种输入输出类型，灵活处理结构化数据
- **动态工具集成**: 支持知识库搜索、计算器、网络搜索、API调用等多种工具
- **流式输出**: 实时观察Agent执行过程，包括LLM思考和工具调用
- **实时测试**: 内置聊天界面，可以实时测试Agent的响应效果，支持多种输入类型
- **工作流设计**: 基于LangGraph的工作流引擎，支持复杂的对话流程
- **RESTful API**: 完整的API接口，支持Agent的CRUD操作和在线调用
- **可观测性监控**: 完整的Agent执行监控系统，替代LangSmith，提供实时性能分析

## 🚀 快速开始

### 环境要求

- Python 3.8+
- OpenAI API Key

### 安装依赖

**推荐使用虚拟环境**:
```bash
python -m venv palantir_env
# Windows:
palantir_env\Scripts\activate
# Linux/Mac:
source palantir_env/bin/activate
```

**安装依赖**:
```bash
# 方法1: 使用安装脚本（推荐，解决版本冲突）
python install.py

# 方法2: 手动安装
pip install -r requirements.txt
```

**注意**: LangChain和LangGraph的版本依赖比较复杂，如果遇到冲突，请使用 `python install.py` 脚本自动安装兼容版本。

### 配置环境变量

创建 `.env` 文件：

```bash
OPENAI_API_KEY=your_openai_api_key_here
LANGCHAIN_API_KEY=your_langchain_api_key_here
LANGCHAIN_TRACING_V2=true
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
LANGCHAIN_PROJECT=palantir-agent
```

### 启动服务

```bash
python start.py
```

服务启动后访问：
- 前端界面: http://localhost:8000/static/index.html
- 流式测试: http://localhost:8000/static/stream_test.html
- 可观测性: http://localhost:8000/static/observability.html
- API文档: http://localhost:8000/docs

## 📖 使用指南

### 1. 创建Agent

1. 点击"创建Agent"按钮
2. 填写基础信息：
   - Agent名称和描述
   - 系统提示词（定义Agent的角色和行为）
   - 用户提示词模板（支持变量替换）

### 2. 配置输入输出格式

- 定义输入参数的类型、描述和是否必填
- 定义输出参数的格式和结构

### 3. 添加工具

系统支持多种工具类型：
- **知识库搜索**: 从预设知识库中检索信息
- **计算器**: 执行数学计算
- **网络搜索**: 搜索网络信息
- **API调用**: 调用外部API服务
- **自定义函数**: 执行自定义逻辑

### 4. 测试Agent

在测试界面中与Agent进行对话，验证其响应效果。

### 5. 部署使用

Agent创建完成后，可以通过API接口进行调用：

```python
import requests

response = requests.post('http://localhost:8000/api/chat', json={
    'agent_id': 'your_agent_id',
    'user_input': '你好，请介绍一下你自己'
})

print(response.json())
```

## 🔧 API接口

### Agent管理

- `POST /api/agents` - 创建Agent
- `GET /api/agents` - 获取Agent列表
- `GET /api/agents/{agent_id}` - 获取Agent详情
- `PUT /api/agents/{agent_id}` - 更新Agent
- `DELETE /api/agents/{agent_id}` - 删除Agent

### 对话接口

- `POST /api/chat` - 与Agent对话
- `POST /api/chat/stream` - 流式对话（Server-Sent Events）

详细的流式输出文档请查看 [STREAMING.md](STREAMING.md)

### 配置接口

- `GET /api/tool-types` - 获取工具类型
- `GET /api/parameter-types` - 获取参数类型
- `GET /api/presets` - 获取预设配置

## 🌟 新功能：Token级流式输出

系统现在支持真正的Token级流式输出，可以逐个字符地显示Agent的响应，提供更加实时的用户体验。

**特性**：
- 逐字符实时显示LLM响应
- 工具调用过程中的暂停和恢复
- 完整的事件类型支持（开始、Token流、工具调用、完成等）
- 前端实时更新界面

**技术实现**：
- 基于Server-Sent Events (SSE)协议
- 使用LangGraph的astream方法
- 支持工具调用过程中的流式暂停

**文档**：
- 实现详情请查看 [docs/TOKEN_STREAMING.md](docs/TOKEN_STREAMING.md)
- 架构设计请查看 [docs/streaming_architecture.md](docs/streaming_architecture.md)

## 🏗️ System Architecture

### High-Level Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   FastAPI       │    │  LangGraph      │
│   (Vue.js)      │◄──►│   (Python)      │◄──►│   (Workflow)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   Tool Plugins  │
                       │  (KB/API/etc)   │
                       └─────────────────┘
```

### Modular Architecture (v2.0)

The system follows a clean, modular architecture with clear separation of concerns:

```
┌──────────────────────────────────────────────────────────────┐
│                         API Layer                             │
│  ┌─────────┐ ┌────────┐ ┌──────────────┐ ┌──────────────┐  │
│  │ Agents  │ │  Chat  │ │Observability │ │    Utils     │  │
│  │ Router  │ │ Router │ │   Router     │ │   Router     │  │
│  └─────────┘ └────────┘ └──────────────┘ └──────────────┘  │
└──────────────────────────────────────────────────────────────┘
                              ▼
┌──────────────────────────────────────────────────────────────┐
│                      Core Business Layer                      │
│  ┌──────────────────┐           ┌─────────────────────────┐ │
│  │  Agent Manager   │           │   Agent Executor        │ │
│  │  (Lifecycle)     │           │   (LangGraph Workflow)  │ │
│  └──────────────────┘           └─────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
                              ▼
┌──────────────────────────────────────────────────────────────┐
│                        Tool Layer                             │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐  │
│  │Calculator│ │WebSearch │ │Knowledge │ │   API Call   │  │
│  │   Tool   │ │   Tool   │ │Base Tool │ │     Tool     │  │
│  └──────────┘ └──────────┘ └──────────┘ └──────────────┘  │
│                    Tool Factory (Registry)                    │
└──────────────────────────────────────────────────────────────┘
                              ▼
┌──────────────────────────────────────────────────────────────┐
│                      Storage Layer                            │
│          ┌────────────────┐      ┌──────────────┐           │
│          │  Agent Storage │      │Observability │           │
│          │  (JSON/DB)     │      │     DB       │           │
│          └────────────────┘      └──────────────┘           │
└──────────────────────────────────────────────────────────────┘
```

**Key Features**:
- **Modular Design**: Each layer has clear responsibilities
- **Factory Pattern**: Extensible tool system
- **Repository Pattern**: Swappable storage backends
- **Router Pattern**: Organized API endpoints
- **Dependency Injection**: Loose coupling between components

📚 **For detailed architecture documentation, see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)**

## 🛠️ 开发说明

### Project Structure

```
palantir_agent/
├── main.py                    # Application entry point (49 lines)
├── agent_factory.py           # Agent execution engine
├── models.py                  # Pydantic data models
├── config.py                  # Configuration management
├── observability.py           # Observability system
│
├── api/                       # API Layer
│   └── routes/
│       ├── agents.py          # Agent CRUD endpoints
│       ├── chat.py            # Chat endpoints  
│       ├── observability.py   # Metrics & monitoring
│       └── utils.py           # Utility endpoints
│
├── core/                      # Business Logic Layer
│   └── agent_manager.py       # Agent lifecycle management
│
├── tools/                     # Tool System
│   ├── base.py                # Abstract base class
│   ├── calculator.py          # Calculator tool
│   ├── web_search.py          # Web search tool
│   ├── knowledge_base.py      # Knowledge base tool
│   ├── api_call.py            # API call tool
│   └── tool_factory.py        # Tool factory
│
├── utils/                     # Utilities
│   └── formatters.py          # Prompt formatting
│
├── storage/                   # Storage Layer
│   └── agent_storage.py       # Persistence (JSON/DB)
│
├── static/                    # Frontend
│   ├── index.html             # Main UI
│   ├── stream_test.html       # Streaming test
│   └── observability.html     # Monitoring UI
│
├── docs/                      # Documentation
│   ├── ARCHITECTURE.md        # Architecture details
│   ├── DEVELOPER_GUIDE.md     # Development guide
│   ├── OPTIMIZATION_SUMMARY.md # Refactoring summary
│   └── MIGRATION_CHECKLIST.md # Migration tracking
│
└── tests/                     # Test suite
    ├── test_complete.py
    ├── test_observability.py
    └── test_streaming.py
```

### Core Components

1. **API Layer** (`api/routes/`): HTTP request/response handling
   - `agents.py`: Agent CRUD operations
   - `chat.py`: Regular and streaming chat
   - `observability.py`: Metrics and monitoring
   - `utils.py`: Tool types and presets

2. **Business Logic** (`core/`): Agent management
   - `agent_manager.py`: Agent lifecycle (create, update, delete)

3. **Tool System** (`tools/`): Extensible tool framework
   - `base.py`: Abstract base class for all tools
   - Individual tool implementations (calculator, web search, etc.)
   - `tool_factory.py`: Factory pattern for tool creation

4. **Storage Layer** (`storage/`): Data persistence
   - `agent_storage.py`: JSON/Database storage abstraction

5. **Execution Engine** (`agent_factory.py`): LangGraph workflow orchestration

6. **Frontend** (`static/`): Vue.js UI for configuration and testing

7. **Observability** (`observability.py`): Metrics, logging, and monitoring

📚 **For detailed developer documentation, see [docs/DEVELOPER_GUIDE.md](docs/DEVELOPER_GUIDE.md)**

## 🧪 测试系统

### 运行测试
```bash
# 完整功能测试
python test_complete.py

# 可观测性功能测试  
python test_observability.py

# 流式输出功能测试
python test_streaming.py

# 时间线功能测试
python test_timeline.py
```

### 测试内容
- Agent创建和管理
- 动态输入输出处理
- 可观测性监控
- API接口功能

## 🔍 示例场景

### 客服助手Agent

```python
agent_config = {
    "name": "客服助手",
    "description": "专业的在线客服助手",
    "system_prompt": "你是一个专业的在线客服助手，请礼貌、耐心地回答用户问题。",
    "user_prompt_template": "用户问题：{user_input}\n请提供专业、有帮助的回答。",
    "tools": [
        {
            "name": "knowledge_search",
            "description": "搜索知识库",
            "type": "knowledge_base"
        }
    ]
}
```

### 数据处理器Agent (支持动态输入输出)

```python
agent_config = {
    "name": "数据处理器",
    "description": "处理各种结构化数据的Agent",
    "system_prompt": "你是一个数据处理专家，能够分析和处理各种类型的数据。",
    "user_prompt_template": "请处理以下数据：{user_input}\n数据详情：{name}, {age}岁, {city}人",
    "input_format": [
        {"name": "name", "type": "string", "description": "姓名", "required": True},
        {"name": "age", "type": "integer", "description": "年龄", "required": True},
        {"name": "city", "type": "string", "description": "城市", "required": True}
    ],
    "output_format": [
        {"name": "analysis", "type": "object", "description": "分析结果", "required": True}
    ]
}

# 使用示例
chat_request = {
    "agent_id": "data-processor-agent",
    "user_input": {"name": "张三", "age": 25, "city": "北京"},
    "input_data": {"name": "张三", "age": 25, "city": "北京"}
}
```

### 内容创作Agent

```python
agent_config = {
    "name": "内容创作助手",
    "description": "专业的文案创作助手",
    "system_prompt": "你是一个专业的内容创作助手，擅长各种文案写作。",
    "user_prompt_template": "请根据以下要求创作内容：{user_input}",
    "tools": [
        {
            "name": "web_search",
            "description": "网络搜索",
            "type": "web_search"
        }
    ]
}
```

## 🤝 贡献指南

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- [LangChain](https://langchain.com/) - LLM应用开发框架
- [LangGraph](https://github.com/langchain-ai/langgraph) - 工作流引擎
- [FastAPI](https://fastapi.tiangolo.com/) - 现代Python Web框架
- [Vue.js](https://vuejs.org/) - 渐进式JavaScript框架
- [Element Plus](https://element-plus.org/) - Vue 3组件库
