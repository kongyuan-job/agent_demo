# Developer Guide - Palantir AI Agent System

## Quick Start

### Project Structure
```
palantir_agent/
├── main.py              # Application entry point (49 lines)
├── agent_factory.py     # Agent execution engine
├── models.py            # Pydantic data models
├── config.py            # Configuration
├── observability.py     # Metrics and logging
│
├── api/                 # API layer
│   └── routes/
│       ├── agents.py         # Agent CRUD endpoints
│       ├── chat.py           # Chat endpoints
│       ├── observability.py  # Metrics endpoints
│       └── utils.py          # Utility endpoints
│
├── core/                # Business logic layer
│   └── agent_manager.py      # Agent lifecycle management
│
├── tools/               # Tool system
│   ├── base.py              # Abstract base class
│   ├── calculator.py        # Calculator tool
│   ├── web_search.py        # Web search tool
│   ├── knowledge_base.py    # Knowledge base tool
│   ├── api_call.py          # API call tool
│   └── tool_factory.py      # Tool factory
│
├── utils/               # Utilities
│   └── formatters.py        # Prompt formatting
│
├── storage/             # Storage layer
│   └── agent_storage.py     # JSON persistence
│
└── static/              # Frontend files
    ├── index.html
    ├── stream_test.html
    └── observability.html
```

## Common Development Tasks

### 1. Adding a New Tool

**Step 1**: Create tool implementation in `tools/my_tool.py`

```python
"""My custom tool implementation"""

from pydantic import BaseModel, Field
from .base import BaseTool
from models import ToolConfig


class MyToolInput(BaseModel):
    """Input schema for my tool"""
    parameter1: str = Field(description="Description of parameter1")
    parameter2: int = Field(default=0, description="Description of parameter2")


class MyTool(BaseTool):
    """My custom tool implementation"""
    
    def get_input_schema(self):
        """Return the input schema for this tool"""
        return MyToolInput
    
    def execute(self, parameter1: str, parameter2: int = 0, **kwargs):
        """Execute the tool logic
        
        Args:
            parameter1: First parameter
            parameter2: Second parameter
            
        Returns:
            Tool execution result
        """
        try:
            # Your tool logic here
            result = f"Processed {parameter1} with {parameter2}"
            return result
        except Exception as e:
            return f"Error: {str(e)}"
```

**Step 2**: Register tool in `tools/tool_factory.py`

```python
from models import ToolType
from .my_tool import MyTool

class ToolFactory:
    _tool_registry: Dict[ToolType, Type[BaseTool]] = {
        ToolType.MY_TOOL: MyTool,  # Add this line
        ToolType.CALCULATOR: CalculatorTool,
        # ... other tools
    }
```

**Step 3**: Add tool type to `models.py` (if new type)

```python
class ToolType(str, Enum):
    MY_TOOL = "my_tool"  # Add this line
    CALCULATOR = "calculator"
    # ... other types
```

**Step 4**: Test your tool

```python
# In Python REPL or test file
from tools.tool_factory import ToolFactory
from models import ToolConfig, ToolType

config = ToolConfig(
    id="test-tool",
    name="Test My Tool",
    type=ToolType.MY_TOOL,
    description="Testing my new tool",
    parameters=[],
    config={}
)

tool = ToolFactory.create_tool(config)
result = tool.invoke({"parameter1": "hello", "parameter2": 42})
print(result)
```

### 2. Adding a New API Endpoint

**Step 1**: Choose appropriate router file in `api/routes/`

- Agent operations → `agents.py`
- Chat operations → `chat.py`
- Metrics/logs → `observability.py`
- Utility endpoints → `utils.py`
- New feature → Create new file `my_feature.py`

**Step 2**: Add endpoint to router

```python
# api/routes/my_feature.py
from fastapi import APIRouter, HTTPException
from models import MyRequest, MyResponse

router = APIRouter(prefix="/api/my-feature", tags=["my-feature"])


@router.post("/", response_model=MyResponse)
async def my_endpoint(request: MyRequest):
    """My new endpoint"""
    try:
        # Your logic here
        return MyResponse(success=True, data={"result": "success"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

**Step 3**: Register router in `main.py`

```python
from api.routes import agents, chat, observability, utils, my_feature

app.include_router(my_feature.router)
```

**Step 4**: Test endpoint

```bash
curl -X POST http://localhost:8000/api/my-feature/ \
  -H "Content-Type: application/json" \
  -d '{"param": "value"}'
```

### 3. Modifying Agent Execution Logic

**Current Location**: `agent_factory.py` (will be refactored to `core/agent_executor.py`)

**Key Methods**:
- `create_agent()` - Create agent instance
- `chat_with_agent()` - Regular chat
- `chat_with_agent_stream()` - Streaming chat

**Example: Add custom processing**

```python
# In agent_factory.py or future core/agent_executor.py

async def chat_with_agent(self, request: ChatRequest) -> Dict:
    """Chat with agent"""
    
    # Get agent config
    config = self.agent_manager.get_agent_config(request.agent_id)
    
    # Add your custom preprocessing here
    processed_input = self._preprocess_input(request.user_input)
    
    # Execute with LangGraph
    result = await self._execute_workflow(config, processed_input)
    
    # Add your custom postprocessing here
    final_result = self._postprocess_output(result)
    
    return final_result

def _preprocess_input(self, user_input: str) -> str:
    """Custom preprocessing logic"""
    # Your logic here
    return user_input

def _postprocess_output(self, output: str) -> str:
    """Custom postprocessing logic"""
    # Your logic here
    return output
```

### 4. Customizing Storage Backend

**Current**: JSON file storage in `storage/agent_storage.py`

**To switch to database**:

**Step 1**: Create new storage implementation

```python
# storage/database_storage.py
from typing import Dict, List, Optional
from models import AgentConfig
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

class DatabaseStorage:
    """Database storage implementation"""
    
    def __init__(self, connection_string: str):
        self.engine = create_engine(connection_string)
        self.Session = sessionmaker(bind=self.engine)
    
    def save_agent(self, agent_id: str, config: AgentConfig) -> None:
        """Save agent to database"""
        session = self.Session()
        try:
            # Your database logic
            pass
        finally:
            session.close()
    
    # Implement other methods: load_agent, delete_agent, etc.
```

**Step 2**: Update `core/agent_manager.py` to use new storage

```python
from storage import DatabaseStorage

class AgentManager:
    def __init__(self, storage: Optional[AgentStorage] = None):
        # Use database storage instead
        self.storage = storage or DatabaseStorage("postgresql://...")
```

### 5. Adding Prompt Templates

**Location**: `utils/formatters.py`

**Add custom formatter**:

```python
class PromptFormatter:
    
    @staticmethod
    def format_with_context(template: str, context: Dict) -> str:
        """Format prompt with additional context"""
        try:
            return template.format(**context)
        except KeyError as e:
            # Handle missing keys
            return template
    
    @staticmethod
    def add_custom_guidance(system_prompt: str, custom_rules: List[str]) -> str:
        """Add custom guidance rules to system prompt"""
        if not custom_rules:
            return system_prompt
        
        guidance = "\n\n自定义规则："
        for i, rule in enumerate(custom_rules, 1):
            guidance += f"\n{i}. {rule}"
        
        return system_prompt + guidance
```

**Use in agent execution**:

```python
from utils.formatters import PromptFormatter

system_prompt = PromptFormatter.add_custom_guidance(
    config.system_prompt,
    custom_rules=["Rule 1", "Rule 2"]
)
```

## Design Patterns Reference

### Factory Pattern (Tool Creation)

```python
# Instead of:
if tool_type == "calculator":
    tool = CalculatorTool(config)
elif tool_type == "web_search":
    tool = WebSearchTool(config)
# ...

# Use:
tool = ToolFactory.create_tool(config)
```

### Template Method Pattern (Tool Base Class)

```python
# Base class defines structure
class BaseTool:
    def from_config(cls, config):
        # Template method
        schema = cls.get_input_schema()  # Abstract
        tool = create_tool(cls.execute)  # Abstract
        return tool

# Subclasses implement specifics
class CalculatorTool(BaseTool):
    def get_input_schema(self):
        return CalculatorInput
    
    def execute(self, expression: str):
        return eval(expression)
```

### Repository Pattern (Storage)

```python
# Storage interface
class AgentStorage:
    def save_agent(self, agent_id, config): pass
    def load_agent(self, agent_id): pass
    def delete_agent(self, agent_id): pass

# Concrete implementations
class JSONStorage(AgentStorage):
    # Implement for JSON files
    pass

class DatabaseStorage(AgentStorage):
    # Implement for database
    pass

# Usage (dependency injection)
manager = AgentManager(storage=JSONStorage())
# Or
manager = AgentManager(storage=DatabaseStorage())
```

## Testing Guidelines

### Unit Test Example

```python
# tests/unit/test_calculator_tool.py
import pytest
from tools.calculator import CalculatorTool
from models import ToolConfig, ToolType

def test_calculator_basic():
    config = ToolConfig(
        id="test",
        name="Calculator",
        type=ToolType.CALCULATOR,
        description="Test calculator",
        parameters=[],
        config={}
    )
    
    tool = CalculatorTool.from_config(config)
    result = tool.invoke({"expression": "2 + 2"})
    
    assert "4" in result

def test_calculator_invalid_expression():
    config = ToolConfig(id="test", name="Calculator", ...)
    tool = CalculatorTool.from_config(config)
    result = tool.invoke({"expression": "import os"})
    
    assert "Error" in result or "Invalid" in result
```

### Integration Test Example

```python
# tests/integration/test_agent_routes.py
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_create_agent():
    response = client.post("/api/agents", json={
        "name": "Test Agent",
        "description": "Test",
        "system_prompt": "You are helpful",
        "user_prompt_template": "{user_input}",
        "tools": []
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True
    assert "agent_id" in data["data"]

def test_list_agents():
    response = client.get("/api/agents")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
```

## Configuration Best Practices

### Environment Variables

```python
# .env file
OPENAI_API_KEY=sk-...
OPENAI_BASE_URL=https://api.openai.com/v1
DATABASE_URL=postgresql://user:pass@localhost/db
DEBUG=true
HOST=0.0.0.0
PORT=8000
```

### Using in Code

```python
from config import Config

# Access configuration
api_key = Config.OPENAI_API_KEY
debug = Config.DEBUG
```

## Debugging Tips

### Enable Verbose Logging

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

logger.debug("Debug message")
logger.info("Info message")
logger.error("Error message")
```

### Check Observability Dashboard

```bash
# Get execution timeline
curl http://localhost:8000/api/observability/execution-timeline?execution_id=xxx

# Get agent metrics
curl http://localhost:8000/api/observability/metrics?agent_id=xxx

# Get dashboard
curl http://localhost:8000/api/observability/dashboard
```

### Test Streaming Locally

```bash
curl -N -X POST http://localhost:8000/api/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"agent_id": "xxx", "user_input": "Hello"}'
```

## Performance Optimization Tips

### 1. Cache Agent Configs
Already implemented in `AgentManager` with in-memory cache

### 2. Use Connection Pooling
For database operations, use connection pooling:

```python
from sqlalchemy import create_engine

engine = create_engine(
    "postgresql://...",
    pool_size=10,
    max_overflow=20
)
```

### 3. Async Operations
Use async/await for I/O operations:

```python
async def chat_with_agent(self, request):
    # Use async for LLM calls
    async for event in self.graph.astream(...):
        yield event
```

### 4. Limit Tool Execution Time

```python
import asyncio

async def execute_with_timeout(tool, input_data, timeout=30):
    try:
        return await asyncio.wait_for(
            tool.ainvoke(input_data),
            timeout=timeout
        )
    except asyncio.TimeoutError:
        return "Tool execution timed out"
```

## Common Pitfalls

### 1. ❌ Don't modify agent_factory singleton directly
```python
# Bad
agent_factory.agents["new_id"] = config

# Good
await agent_factory.agent_manager.create_agent(config)
```

### 2. ❌ Don't create tools without factory
```python
# Bad
tool = CalculatorTool(config)

# Good
tool = ToolFactory.create_tool(config)
```

### 3. ❌ Don't hardcode configuration
```python
# Bad
api_key = "sk-..."

# Good
from config import Config
api_key = Config.OPENAI_API_KEY
```

### 4. ❌ Don't ignore error handling
```python
# Bad
result = some_operation()

# Good
try:
    result = some_operation()
except SpecificError as e:
    logger.error(f"Operation failed: {e}")
    raise HTTPException(status_code=500, detail=str(e))
```

## Resources

- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **LangGraph Docs**: https://langchain-ai.github.io/langgraph/
- **Pydantic Docs**: https://docs.pydantic.dev/
- **OpenAI API Docs**: https://platform.openai.com/docs

## Getting Help

1. Check `docs/ARCHITECTURE.md` for system design
2. Check `docs/OPTIMIZATION_SUMMARY.md` for recent changes
3. Check existing code for examples
4. Review test files for usage patterns
5. Check observability dashboard for runtime issues

---

**Last Updated**: 2025-10-22  
**Maintainer**: Development Team  
**Status**: Active Development
