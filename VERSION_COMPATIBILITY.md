# 版本兼容性说明

## 🔄 版本更新记录

### 当前版本 (v2.4)
- **LangChain**: 0.3.3
- **LangChain-Core**: 0.3.15  
- **LangChain-OpenAI**: 0.2.0
- **LangGraph**: 0.2.45
- **OpenAI**: 1.40.0
- **Pydantic**: 2.7.4

### 主要变更

#### 1. LangGraph API 变更
- 状态定义从字典改为 `TypedDict`
- 消息处理使用 `operator.add` 注解
- 移除了 `add_messages` 导入，改用列表操作

#### 2. 状态管理优化
```python
# 旧版本
workflow = StateGraph({
    "messages": add_messages,
    "user_input": str,
    "response": str
})

# 新版本
class AgentState(TypedDict):
    messages: Annotated[list, operator.add]
    user_input: str
    response: str

workflow = StateGraph(AgentState)
```

#### 3. 消息处理简化
```python
# 旧版本
initial_state["messages"] = add_messages(
    initial_state["messages"], 
    [HumanMessage(content=msg.content)]
)

# 新版本
initial_state["messages"].append(HumanMessage(content=msg.content))
```

## 🛠️ 故障排除

### 常见问题

#### 1. 依赖冲突
```
ERROR: Cannot install -r requirements.txt because these package versions have conflicting dependencies.
```

**解决方案**:
```bash
# 使用安装脚本
python install.py

# 或者创建新的虚拟环境
python -m venv fresh_env
fresh_env\Scripts\activate  # Windows
source fresh_env/bin/activate  # Linux/Mac
pip install -r requirements.txt
```

#### 2. 导入错误
```
ImportError: cannot import name 'add_messages' from 'langgraph.graph.message'
```

**解决方案**: 代码已更新为使用新API，确保使用最新版本的代码。

#### 3. 状态类型错误
```
TypeError: 'dict' object is not callable
```

**解决方案**: 确保使用 `TypedDict` 定义状态类型。

### 版本回退

如果需要使用旧版本，可以修改 `requirements.txt`:

```txt
# 旧版本配置（不推荐）
langchain==0.1.0
langchain-core==0.1.0
langchain-openai==0.0.5
langgraph==0.0.20
```

**注意**: 使用旧版本需要相应调整代码中的API调用。

## 🔍 测试兼容性

运行测试脚本验证版本兼容性:

```bash
python test_agent.py
```

如果测试通过，说明版本配置正确。

## 📚 相关资源

- [LangChain官方文档](https://python.langchain.com/)
- [LangGraph官方文档](https://langchain-ai.github.io/langgraph/)
- [版本更新日志](https://github.com/langchain-ai/langchain/releases)
