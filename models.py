from pydantic import BaseModel, Field, ConfigDict
from typing import List, Dict, Any, Optional, Union
from enum import Enum

class AgentStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"

class ToolType(str, Enum):
    """工具类型"""
    SYSTEM_FUNCTION = "system_function"  # 系统工具（计算器等）
    CALL_FUNCTION = "call_function"      # 用户自定义工具（API等）
    QUERY_OBJECTS = "query_objects"      # 本体工具（图数据库）



class VariableMetaType(str, Enum):
    """变量元类型"""
    STRING = "String"
    INTEGER = "Integer"
    FLOAT = "Float"
    BOOLEAN = "Boolean"
    OBJECT = "Object"
    ARRAY = "Array"

class FunctionType(str, Enum):
    """函数类型"""
    API = "api"
    LAMBDA = "lambda"
    CUSTOM = "custom"

class ReferenceObjectType(str, Enum):
    """引用对象类型"""
    INPUT = "input_type"      # 引用输入参数
    TOOL_RESULT = "tool_result"  # 引用工具结果
    VARIABLE = "variable"     # 引用变量

# ==================== 新模型定义 ====================

class InputParameter(BaseModel):
    """输入参数定义"""
    model_config = ConfigDict(use_enum_values=True)
    
    type: VariableMetaType
    value: Optional[Any] = None  # 默认值
    description: Optional[str] = None
    required: bool = False

class OutputParameter(BaseModel):
    """输出参数定义"""
    model_config = ConfigDict(use_enum_values=True)
    
    variable_meta_type: VariableMetaType  # 元类型（String, Object等）
    variable_type: Optional[str] = None   # 具体类型（List, Dict等）
    variable_desc: str                     # 变量描述
    required: bool = True

class ObjectField(BaseModel):
    """对象字段定义（用于query_objects工具）"""
    field_name: str
    field_description: str
    field_type: Optional[str] = None

class QueryObject(BaseModel):
    """查询对象定义（用于query_objects工具）"""
    object_code: str
    object_description: str
    fields: List[ObjectField] = []

class ReferenceObject(BaseModel):
    """提示词中的引用对象"""
    model_config = ConfigDict(use_enum_values=True)
    
    id: int                          # 引用ID
    type: ReferenceObjectType        # 引用类型
    name: str                        # 引用名称
    value: Optional[Any] = None      # 引用值（可选）
    tag: Optional[str] = None        # 标签（用于模板替换）

class SystemPrompt(BaseModel):
    """系统提示词"""
    value: str                                    # 提示词内容
    ref_objects: List[ReferenceObject] = []      # 引用的对象列表

class TaskPrompt(BaseModel):
    """任务提示词"""
    value: str                                    # 提示词内容
    ref_objects: List[ReferenceObject] = []      # 引用的对象列表

class LLMConfig(BaseModel):
    """大模型配置"""
    id: str                          # LLM ID
    name: str                        # LLM名称（如 deepseek-chat, gpt-4等）
    temperature: float = 0.7         # 温度值
    max_tokens: int = 1000           # 最大token数
    api_base: Optional[str] = None   # API地址（可选）
    api_key: Optional[str] = None    # API密钥（可选）

class SystemFunctionTool(BaseModel):
    """系统函数工具"""
    type: str = "system_function"
    name: str                        # 系统函数名称（如calculator）
    description: Optional[str] = None

class CallFunctionTool(BaseModel):
    """调用函数工具"""
    type: str = "call_function"
    name: str                        # 函数名称
    function_type: FunctionType      # 函数类型（api, lambda, custom）
    description: Optional[str] = None
    config: Dict[str, Any] = {}      # 函数配置（如API地址、请求方法等）

class QueryObjectsTool(BaseModel):
    """查询对象工具（图数据库）"""
    type: str = "query_objects"
    objects: List[QueryObject] = []  # 查询的对象列表
    description: Optional[str] = None

# 工具联合类型
AgentTool = Union[SystemFunctionTool, CallFunctionTool, QueryObjectsTool]

class AgentConfig(BaseModel):
    """Agent配置模型（新版）"""
    model_config = ConfigDict(use_enum_values=True)
    
    # 基础信息
    id: Optional[str] = None
    name: str
    description: str
    
    # 输入参数（可选，支持多个）
    input: Dict[str, InputParameter] = {}  # key为参数名，value为参数定义
    
    # 工具列表（可选，支持多个）
    tools: List[Dict[str, Any]] = []  # 支持多种工具类型的混合列表
    
    # 系统提示词（必填）
    system_prompt: SystemPrompt
    
    # 任务提示词（必填）
    task_prompt: TaskPrompt
    
    # 输出参数（必填，支持多个）
    output: Dict[str, OutputParameter]  # key为参数名，value为参数定义
    
    # 大模型配置（必填）
    llm: LLMConfig
    
    # 状态和时间戳
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

