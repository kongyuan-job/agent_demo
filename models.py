from pydantic import BaseModel, Field, ConfigDict
from typing import List, Dict, Any, Optional, Union
from enum import Enum

class AgentStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"

class ToolType(str, Enum):
    KNOWLEDGE_BASE = "knowledge_base"
    CALCULATOR = "calculator"
    WEB_SEARCH = "web_search"
    API_CALL = "api_call"
    CUSTOM_FUNCTION = "custom_function"

class ParameterType(str, Enum):
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"

class Parameter(BaseModel):
    model_config = ConfigDict(use_enum_values=True)
    
    name: str
    type: ParameterType
    description: str
    required: bool = True
    default_value: Optional[Any] = None
    enum_values: Optional[List[Any]] = None

class Tool(BaseModel):
    model_config = ConfigDict(use_enum_values=True)
    
    id: Optional[str] = None
    name: str
    description: str
    type: ToolType
    parameters: List[Parameter] = []
    config: Dict[str, Any] = {}

class AgentConfig(BaseModel):
    model_config = ConfigDict(use_enum_values=True)
    
    id: Optional[str] = None
    name: str
    description: str
    system_prompt: str
    user_prompt_template: str
    input_format: List[Parameter] = []
    output_format: List[Parameter] = []
    tools: List[Tool] = []
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=1000, ge=1, le=4000)
    status: AgentStatus = AgentStatus.DRAFT
    created_at: str = ""
    updated_at: str = ""

class AgentResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    agent_id: str                  # 代理的 ID
    user_input: Any               # 用户的输入 - 支持字符串、对象等多种类型
    conversation_history: List[ChatMessage] = []  # 历史对话记录
    input_data: Optional[Dict[str, Any]] = None  # 结构化输入数据
    stream: bool = False          # 是否启用流式响应
    temperature: Optional[float] = None    # 可选：覆盖代理的温度设置
    max_tokens: Optional[int] = None       # 可选：覆盖代理的最大令牌设置

class ChatResponse(BaseModel):
    success: bool
    message: str
    response: Optional[Any] = None  # 支持字符串、对象等多种类型
    output_data: Optional[Dict[str, Any]] = None  # 结构化输出数据
    metadata: Optional[Dict[str, Any]] = None

