import json
import asyncio
from langchain_core.messages.system import SystemMessage
import time
import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
import uuid

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.tools import Tool as LangChainTool
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
from typing_extensions import TypedDict
from typing import Annotated
import operator

from models import AgentConfig, Tool as ToolConfig, ParameterType, ToolType, ChatRequest, ChatMessage
from config import Config
from observability import log_agent_execution, log_tool_call, log_llm_call, observability_manager, AgentExecution

# 定义状态类型 - 支持动态输入输出类型
class AgentState(TypedDict):
    messages: Annotated[list, operator.add]
    user_input: Any  # 支持字符串、对象等多种类型
    response: Any    # 支持字符串、对象等多种类型
    input_data: Optional[Dict[str, Any]]  # 结构化输入数据
    output_data: Optional[Dict[str, Any]]  # 结构化输出数据
    execution_id: Optional[str]  # 执行ID，用于追踪
    agent_id: Optional[str]  # Agent ID

class AgentFactory:
    """动态Agent创建工厂类"""
    
    def __init__(self):
        self.agents: Dict[str, Any] = {}
        self.storage_path = Path("agents_storage.json")
        self._load_agents_from_disk()
    
    def _load_agents_from_disk(self):
        """从磁盘加载Agent配置"""
        try:
            if self.storage_path.exists():
                with open(self.storage_path, 'r', encoding='utf-8') as f:
                    saved_data = json.load(f)
                    
                # 重新创建Agent实例
                for agent_id, agent_data in saved_data.items():
                    config_dict = agent_data.get("config")
                    if config_dict:
                        # 从dict重建AgentConfig对象
                        config = AgentConfig(**config_dict)
                        # 重新创建Agent graph
                        agent_graph = self.create_agent_from_config(config)
                        
                        self.agents[agent_id] = {
                            "id": agent_id,
                            "config": config,
                            "graph": agent_graph,
                            "created_at": agent_data.get("created_at", datetime.now().isoformat())
                        }
                print(f"Loaded {len(self.agents)} agents from disk")
        except Exception as e:
            print(f"Error loading agents from disk: {e}")
            # 如果加载失败，从空开始
            self.agents = {}
    
    def _save_agents_to_disk(self):
        """保存Agent配置到磁盘"""
        try:
            # 只保存配置和元数据，不保存graph实例
            save_data = {}
            for agent_id, agent_info in self.agents.items():
                save_data[agent_id] = {
                    "id": agent_id,
                    "config": agent_info["config"].dict(),
                    "created_at": agent_info.get("created_at", datetime.now().isoformat())
                }
            
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, ensure_ascii=False, indent=2)
            print(f"Saved {len(save_data)} agents to disk")
        except Exception as e:
            print(f"Error saving agents to disk: {e}")
    
    def create_tool_from_config(self, tool_config: ToolConfig) -> LangChainTool:
        """根据配置创建LangChain工具"""
        from pydantic import BaseModel, Field as PydanticField
        
        # 根据工具类型创建输入模型
        if tool_config.type == ToolType.CALCULATOR:
            class CalculatorInput(BaseModel):
                expression: str = PydanticField(
                    description="需要计算的数学表达式，例如: '1+1', '2*3', '(1+1)*3'"
                )
            
            def calculator_func(expression: str) -> str:
                try:
                    allowed_chars = set('0123456789+-*/.() ')
                    if not all(c in allowed_chars for c in expression):
                        return "错误: 包含不安全的字符"
                    result = eval(expression)
                    return f"计算结果: {result}"
                except Exception as e:
                    return f"计算错误: {str(e)}"
            
            return LangChainTool(
                name=tool_config.name,
                description=tool_config.description or "用于计算数学表达式",
                func=calculator_func,
                args_schema=CalculatorInput
            )
        
        elif tool_config.type == ToolType.WEB_SEARCH:
            class WebSearchInput(BaseModel):
                query: str = PydanticField(
                    description="搜索查询关键词"
                )
            
            async def web_search_func(query: str) -> str:
                return await self._web_search(query)
            
            return LangChainTool(
                name=tool_config.name,
                description=tool_config.description or "网络搜索工具",
                func=web_search_func,
                args_schema=WebSearchInput,
                coroutine=web_search_func
            )
        
        elif tool_config.type == ToolType.KNOWLEDGE_BASE:
            class KnowledgeSearchInput(BaseModel):
                query: str = PydanticField(
                    description="知识库搜索关键词"
                )
            
            async def knowledge_search_func(query: str) -> str:
                return await self._knowledge_base_search(query)
            
            return LangChainTool(
                name=tool_config.name,
                description=tool_config.description or "搜索知识库",
                func=knowledge_search_func,
                args_schema=KnowledgeSearchInput,
                coroutine=knowledge_search_func
            )
        
        elif tool_config.type == ToolType.API_CALL:
            # 根据配置的参数动态创建Schema
            if tool_config.parameters:
                # 使用配置的参数创建动态Schema
                from typing import Dict as TypingDict
                
                # 动态创建字段字典
                fields = {}
                for param in tool_config.parameters:
                    field_type = str  # 默认字符串类型
                    if param.type == ParameterType.INTEGER:
                        field_type = int
                    elif param.type == ParameterType.FLOAT:
                        field_type = float
                    elif param.type == ParameterType.BOOLEAN:
                        field_type = bool
                    
                    if param.required:
                        fields[param.name] = (field_type, PydanticField(description=param.description))
                    else:
                        fields[param.name] = (field_type, PydanticField(default=param.default_value, description=param.description))
                
                # 动态创建Pydantic模型
                from pydantic import create_model
                APICallInput = create_model('APICallInput', **fields)
            else:
                # 默认通用参数Schema
                class APICallInput(BaseModel):
                    params: dict = PydanticField(
                        default={},
                        description="API调用参数，以JSON对象形式传递"
                    )
            
            async def api_call_func(**kwargs) -> str:
                return await self._api_call(tool_config.config, kwargs)
            
            # 构建详细的描述
            api_description = tool_config.description or "调用外部API接口"
            if tool_config.config.get("url"):
                api_description += f"\nAPI地址: {tool_config.config['url']}"
            if tool_config.config.get("method"):
                api_description += f"\n请求方法: {tool_config.config['method']}"
            
            return LangChainTool(
                name=tool_config.name,
                description=api_description,
                func=api_call_func,
                args_schema=APICallInput,
                coroutine=api_call_func
            )
        
        elif tool_config.type == ToolType.CUSTOM_FUNCTION:
            # 自定义函数工具
            if tool_config.parameters:
                # 使用配置的参数创建动态Schema
                fields = {}
                for param in tool_config.parameters:
                    field_type = str
                    if param.type == ParameterType.INTEGER:
                        field_type = int
                    elif param.type == ParameterType.FLOAT:
                        field_type = float
                    elif param.type == ParameterType.BOOLEAN:
                        field_type = bool
                    
                    if param.required:
                        fields[param.name] = (field_type, PydanticField(description=param.description))
                    else:
                        fields[param.name] = (field_type, PydanticField(default=param.default_value, description=param.description))
                
                from pydantic import create_model
                CustomFunctionInput = create_model('CustomFunctionInput', **fields)
            else:
                class CustomFunctionInput(BaseModel):
                    input_data: dict = PydanticField(
                        default={},
                        description="自定义函数的输入参数"
                    )
            
            async def custom_func(**kwargs) -> str:
                return await self._custom_function(tool_config.config, kwargs)
            
            return LangChainTool(
                name=tool_config.name,
                description=tool_config.description or "执行自定义函数",
                func=custom_func,
                args_schema=CustomFunctionInput,
                coroutine=custom_func
            )
        
        else:
            # 默认通用工具处理
            class GenericToolInput(BaseModel):
                input: str = PydanticField(
                    default="",
                    description="工具输入参数"
                )
            
            async def generic_func(**kwargs) -> str:
                return f"工具 {tool_config.name} 执行成功，参数: {kwargs}"
            
            return LangChainTool(
                name=tool_config.name,
                description=tool_config.description or "通用工具",
                func=generic_func,
                args_schema=GenericToolInput,
                coroutine=generic_func
            )
    
    async def _knowledge_base_search(self, query: str) -> str:
        """知识库搜索工具"""
        # 这里可以集成实际的向量数据库或知识库
        return f"知识库搜索结果: {query}"
    
    async def _calculator(self, expression: str) -> str:
        """计算器工具"""
        try:
            # 安全的数学表达式计算
            allowed_chars = set('0123456789+-*/.() ')
            if not all(c in allowed_chars for c in expression):
                return "错误: 包含不安全的字符"
            
            result = eval(expression)
            return f"计算结果: {result}"
        except Exception as e:
            return f"计算错误: {str(e)}"
    
    async def _web_search(self, query: str) -> str:
        """网络搜索工具"""
        # 这里可以集成实际的搜索API
        return f"网络搜索结果: {query}"
    
    async def _api_call(self, config: Dict[str, Any], kwargs: Dict[str, Any]) -> str:
        """API调用工具"""
        import httpx
        
        url = config.get("url", "")
        method = config.get("method", "GET").upper()
        headers = config.get("headers", {})
        
        async with httpx.AsyncClient() as client:
            if method == "GET":
                response = await client.get(url, headers=headers, params=kwargs)
            elif method == "POST":
                response = await client.post(url, headers=headers, json=kwargs)
            else:
                return f"不支持的HTTP方法: {method}"
            
            return f"API调用结果: {response.text}"
    
    async def _custom_function(self, config: Dict[str, Any], kwargs: Dict[str, Any]) -> str:
        """自定义函数工具"""
        # 这里可以执行用户自定义的Python代码（需要沙箱环境）
        return f"自定义函数执行结果: {kwargs}"
    
    def create_agent_from_config(self, config: AgentConfig) -> StateGraph:
        """根据配置动态创建LangGraph Agent"""
        llm = ChatOpenAI(
            model="deepseek-chat",
            temperature=0.1,
            openai_api_key=Config.OPENAI_API_KEY
        )
        # 创建工具列表
        tools = []
        for tool_config in config.tools:
            langchain_tool = self.create_tool_from_config(tool_config)
            tools.append(langchain_tool)
        
        tool_node = ToolNode(tools) if tools else None
        if tools:
            llm = llm.bind_tools(tools)
        
        def agent_node(state: AgentState) -> AgentState:
            """Agent节点处理逻辑 - 支持动态输入输出类型"""
            messages = state.get("messages", [])
            execution_id = state.get("execution_id", "")
            agent_id = state.get("agent_id", "")
            
            # 构建系统消息 - 添加工具使用指导
            system_prompt = config.system_prompt
            if tools:
                # 如果有工具，添加明确的指导原则
                tool_guidance = (
                    "\n\n重要指导原则："
                    "\n1. 当需要使用工具时，调用相应的工具获取信息。"
                    "\n2. 工具返回结果后，基于结果给出最终答案，不要重复调用同一工具。"
                    "\n3. 如果工具已经提供了答案，直接使用该答案回复用户，不要再次调用工具。"
                    "\n4. 一旦得到所需信息，立即给出完整的最终回复，结束对话。"
                )
                system_prompt = system_prompt + tool_guidance
            
            system_message: SystemMessage = SystemMessage(content=system_prompt)
            
            # 处理动态输入类型
            user_input = state.get("user_input", "")
            input_data = state.get("input_data", {}) or {}  # Ensure it's never None
            
            # 根据输入类型构建用户消息
            try:
                if isinstance(user_input, str):
                    # 字符串输入 - 使用模板格式化
                    formatted_input = config.user_prompt_template.format(
                        user_input=user_input,
                        **input_data  # 支持额外的结构化数据
                    )
                elif isinstance(user_input, dict):
                    # 对象输入 - 直接使用对象数据
                    formatted_input = config.user_prompt_template.format(
                        user_input=str(user_input),
                        **user_input,  # 展开对象属性
                        **input_data
                    )
                else:
                    # 其他类型输入 - 转换为字符串
                    formatted_input = config.user_prompt_template.format(
                        user_input=str(user_input),
                        **input_data
                    )
            except (KeyError, TypeError) as e:
                # 如果模板中缺少占位符或参数错误，使用默认格式
                formatted_input = f"用户输入：{user_input}\n{config.user_prompt_template}"
            
            user_message = HumanMessage(content=formatted_input)
            
            # 调用LLM - 添加观测
            llm_start_time = time.time()
            try:
                # 只在第一次调用时添加用户消息，后续调用只使用messages（包含工具调用历史）
                if not messages:
                    # 第一次调用：添加用户消息
                    conversation = [system_message, user_message]
                else:
                    # 后续调用：使用已有的消息历史（包含工具调用和结果）
                    conversation = [system_message] + messages
                print(conversation)
                response = llm.invoke(conversation)
                llm_call_time = time.time() - llm_start_time
                
                # 记录LLM调用
                if execution_id and agent_id:
                    log_llm_call(
                        execution_id=execution_id,
                        agent_id=agent_id,
                        model="deepseek-chat",
                        messages=[
                            {"role": "system", "content": config.system_prompt},
                            *[{"role": m.type, "content": m.content} for m in messages],
                            {"role": "user", "content": formatted_input}
                        ],
                        response=response.content,
                        call_time=llm_call_time,
                        tokens_used=None,  # Can extract from response if available
                        success=True
                    )
            except Exception as e:
                llm_call_time = time.time() - llm_start_time
                if execution_id and agent_id:
                    log_llm_call(
                        execution_id=execution_id,
                        agent_id=agent_id,
                        model="deepseek-chat",
                        messages=[],
                        response="",
                        call_time=llm_call_time,
                        success=False,
                        error_message=str(e)
                    )
                raise
            
            # 处理输出格式
            output_data = {}
            if config.output_format:
                # 如果有输出格式定义，尝试解析为结构化数据
                try:
                    # 简单的JSON解析尝试
                    import json
                    output_data = json.loads(response.content)
                except (json.JSONDecodeError, ValueError):
                    # 如果不是JSON，保持为字符串
                    output_data = {"content": response.content}
            else:
                # 没有输出格式定义，直接使用内容
                output_data = {"content": response.content}
            
            return {
                "messages": [response],
                "response": response.content,
                "output_data": output_data
            }
        
        def should_continue(state: AgentState) -> str:
            """判断是否继续执行"""
            messages = state.get("messages", [])
            last_message = messages[-1] if messages else None
            
            if last_message and hasattr(last_message, 'tool_calls') and last_message.tool_calls:
                return "tools"
            return "end"
        
        def call_tools(state: AgentState) -> AgentState:
            """调用工具 - 添加观测"""
            execution_id = state.get("execution_id", "")
            agent_id = state.get("agent_id", "")
            
            # 调用工具节点
            tool_start_time = time.time()
            try:
                result = tool_node.invoke(state)
                
                # 尝试记录工具调用（从messages中提取）
                if execution_id and agent_id:
                    last_message = state.get("messages", [])[-1] if state.get("messages") else None
                    if last_message and hasattr(last_message, 'tool_calls'):
                        for tool_call in last_message.tool_calls:
                            tool_call_time = time.time() - tool_start_time
                            log_tool_call(
                                execution_id=execution_id,
                                agent_id=agent_id,
                                tool_name=tool_call.get('name', 'unknown'),
                                tool_type=tool_call.get('type', 'unknown'),
                                input_params=tool_call.get('args', {}),
                                output=str(result.get("messages", [])[-1].content if result.get("messages") else ""),
                                call_time=tool_call_time,
                                success=True
                            )
                
                return result
            except Exception as e:
                tool_call_time = time.time() - tool_start_time
                if execution_id and agent_id:
                    log_tool_call(
                        execution_id=execution_id,
                        agent_id=agent_id,
                        tool_name="unknown",
                        tool_type="unknown",
                        input_params={},
                        output="",
                        call_time=tool_call_time,
                        success=False,
                        error_message=str(e)
                    )
                raise

        # 创建状态图
        workflow = StateGraph(AgentState)
        
        # 添加节点
        workflow.add_node("agent", agent_node)
        
        if tool_node:
            workflow.add_node("tools", call_tools)
            workflow.add_conditional_edges(
                "agent",
                should_continue,
                {
                    "tools": "tools",
                    "end": END
                }
            )
            workflow.add_edge("tools", "agent")
        else:
            workflow.add_edge("agent", END)
        
        # 设置入口点
        workflow.set_entry_point("agent")
        
        return workflow.compile(checkpointer=MemorySaver())
    
    async def create_agent(self, config: AgentConfig) -> str:
        """创建Agent并返回ID"""
        agent_id = str(uuid.uuid4())
        
        # 创建Agent实例
        agent_graph = self.create_agent_from_config(config)
        
        # 存储Agent
        self.agents[agent_id] = {
            "id": agent_id,
            "config": config,
            "graph": agent_graph,
            "created_at": datetime.now().isoformat()
        }
        
        # 保存到磁盘
        self._save_agents_to_disk()
        
        return agent_id
    
    async def chat_with_agent_stream(self, request: ChatRequest):
        """与Agent对话 - 流式输出版本"""
        agent_id = request.agent_id
        start_time = time.time()
        
        if agent_id not in self.agents:
            error_msg = f"Agent {agent_id} 不存在"
            yield {
                "type": "error",
                "message": error_msg,
                "timestamp": datetime.now().isoformat()
            }
            return
        
        agent_info = self.agents[agent_id]
        agent_graph = agent_info["graph"]
        execution_id = str(uuid.uuid4())
        
        try:
            # 发送开始事件
            yield {
                "type": "start",
                "execution_id": execution_id,
                "agent_id": agent_id,
                "timestamp": datetime.now().isoformat()
            }
            
            # 构建初始状态
            initial_state = {
                "messages": [],
                "user_input": request.user_input,
                "response": "",
                "input_data": getattr(request, 'input_data', None) or {},  # Ensure never None
                "output_data": {},
                "execution_id": execution_id,
                "agent_id": agent_id
            }
            
            # 添加历史对话
            for msg in request.conversation_history:
                if msg.role == "user":
                    initial_state["messages"].append(HumanMessage(content=msg.content))
                elif msg.role == "assistant":
                    initial_state["messages"].append(AIMessage(content=msg.content))
            
            # 流式执行Agent
            config = {
                "configurable": {"thread_id": f"thread_{agent_id}"},
                "recursion_limit": 50  # Increase limit to prevent premature termination
            }
            final_result = None
            
            async for event in agent_graph.astream(initial_state, config):
                # event 是一个字典，key是节点名，value是该节点的输出
                for node_name, node_output in event.items():
                    if node_name == "agent":
                        # Agent节点输出
                        messages = node_output.get("messages", [])
                        if messages:
                            last_message = messages[-1]
                            
                            # LLM响应
                            if hasattr(last_message, 'content'):
                                yield {
                                    "type": "agent_message",
                                    "content": last_message.content,
                                    "timestamp": datetime.now().isoformat()
                                }
                            
                            # 工具调用
                            if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
                                for tool_call in last_message.tool_calls:
                                    yield {
                                        "type": "tool_call_start",
                                        "tool_name": tool_call.get('name', 'unknown'),
                                        "tool_args": tool_call.get('args', {}),
                                        "timestamp": datetime.now().isoformat()
                                    }
                    
                    elif node_name == "tools":
                        # 工具节点输出
                        messages = node_output.get("messages", [])
                        if messages:
                            last_message = messages[-1]
                            if hasattr(last_message, 'content'):
                                yield {
                                    "type": "tool_result",
                                    "content": last_message.content,
                                    "timestamp": datetime.now().isoformat()
                                }
                    
                    # 保存最终结果
                    final_result = node_output
            
            # 执行完成
            execution_time = time.time() - start_time
            response_data = final_result.get("response", "") if final_result else ""
            
            # 记录执行
            final_execution = AgentExecution(
                execution_id=execution_id,
                agent_id=agent_id,
                user_input=request.user_input,
                response=response_data,
                input_type=type(request.user_input).__name__,
                output_type=type(response_data).__name__,
                execution_time=execution_time,
                timestamp=datetime.now().isoformat(),
                metadata={
                    "conversation_length": len(request.conversation_history),
                    "output_data": final_result.get("output_data", {}) if final_result else {}
                },
                success=True
            )
            observability_manager.log_execution(final_execution)
            
            # 发送完成事件
            yield {
                "type": "done",
                "response": response_data,
                "output_data": final_result.get("output_data", {}) if final_result else {},
                "execution_id": execution_id,
                "execution_time": execution_time,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"对话失败: {str(e)}"
            
            # 记录失败的执行
            if execution_id:
                final_execution = AgentExecution(
                    execution_id=execution_id,
                    agent_id=agent_id,
                    user_input=request.user_input,
                    response=None,
                    input_type=type(request.user_input).__name__,
                    output_type="None",
                    execution_time=execution_time,
                    timestamp=datetime.now().isoformat(),
                    metadata={"error_type": "execution_error", "error_details": str(e)},
                    success=False,
                    error_message=error_msg
                )
                observability_manager.log_execution(final_execution)
            
            yield {
                "type": "error",
                "message": error_msg,
                "timestamp": datetime.now().isoformat()
            }

    async def chat_with_agent(self, request: ChatRequest) -> Dict[str, Any]:
        """与Agent对话 - 支持动态输入输出类型"""
        agent_id = request.agent_id
        start_time = time.time()
        
        if agent_id not in self.agents:
            error_msg = f"Agent {agent_id} 不存在"
            log_agent_execution(
                agent_id=agent_id,
                user_input=request.user_input,
                response=None,
                execution_time=time.time() - start_time,
                success=False,
                error_message=error_msg,
                metadata={"error_type": "agent_not_found"}
            )
            return {
                "success": False,
                "message": error_msg,
                "response": None
            }
        
        agent_info = self.agents[agent_id]
        agent_graph = agent_info["graph"]
        
        try:
            # 生成执行ID
            execution_id = str(uuid.uuid4())
            
            # 构建初始状态 - 支持动态输入类型
            initial_state = {
                "messages": [],
                "user_input": request.user_input,
                "response": "",
                "input_data": getattr(request, 'input_data', None) or {},  # Ensure never None
                "output_data": {},
                "execution_id": execution_id,  # 添加执行ID
                "agent_id": agent_id  # 添加Agent ID
            }
            
            # 添加历史对话
            for msg in request.conversation_history:
                if msg.role == "user":
                    initial_state["messages"].append(HumanMessage(content=msg.content))
                elif msg.role == "assistant":
                    initial_state["messages"].append(AIMessage(content=msg.content))
            
            # 执行Agent
            config = {
                "configurable": {"thread_id": f"thread_{agent_id}"},
                "recursion_limit": 50  # Increase limit to prevent premature termination
            }
            result = await agent_graph.ainvoke(initial_state, config)
            
            execution_time = time.time() - start_time
            response_data = result.get("response", "")
            
            # 记录成功的执行 - 使用同一个execution_id
            final_execution = AgentExecution(
                execution_id=execution_id,  # 使用已生成的execution_id
                agent_id=agent_id,
                user_input=request.user_input,
                response=response_data,
                input_type=type(request.user_input).__name__,
                output_type=type(response_data).__name__,
                execution_time=execution_time,
                timestamp=datetime.now().isoformat(),
                metadata={
                    "conversation_length": len(request.conversation_history),
                    "output_data": result.get("output_data", {})
                },
                success=True
            )
            observability_manager.log_execution(final_execution)
            
            return {
                "success": True,
                "message": "对话成功",
                "response": response_data,
                "output_data": result.get("output_data", {}),
                "metadata": {
                    "agent_id": agent_id,
                    "execution_id": execution_id,
                    "timestamp": datetime.now().isoformat(),
                    "input_type": type(request.user_input).__name__,
                    "output_type": type(response_data).__name__,
                    "execution_time": execution_time
                }
            }
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"对话失败: {str(e)}"
            
            # 记录失败的执行 - 使用同一个execution_id
            if 'execution_id' in locals():
                final_execution = AgentExecution(
                    execution_id=execution_id,
                    agent_id=agent_id,
                    user_input=request.user_input,
                    response=None,
                    input_type=type(request.user_input).__name__,
                    output_type="None",
                    execution_time=execution_time,
                    timestamp=datetime.now().isoformat(),
                    metadata={"error_type": "execution_error", "error_details": str(e)},
                    success=False,
                    error_message=error_msg
                )
                observability_manager.log_execution(final_execution)
            else:
                # 如果还没有生成execution_id，使用旧方法
                log_agent_execution(
                    agent_id=agent_id,
                    user_input=request.user_input,
                    response=None,
                    execution_time=execution_time,
                    success=False,
                    error_message=error_msg,
                    metadata={"error_type": "execution_error", "error_details": str(e)}
                )
            
            return {
                "success": False,
                "message": error_msg,
                "response": None,
                "output_data": {}
            }
    
    def get_agent_list(self) -> List[Dict[str, Any]]:
        """获取Agent列表"""
        return [
            {
                "id": agent_id,
                "name": info["config"].name,
                "description": info["config"].description,
                "status": info["config"].status,
                "created_at": info["created_at"]
            }
            for agent_id, info in self.agents.items()
        ]
    
    def get_agent_config(self, agent_id: str) -> Optional[AgentConfig]:
        """获取Agent配置"""
        if agent_id in self.agents:
            return self.agents[agent_id]["config"]
        return None
    
    def delete_agent(self, agent_id: str) -> bool:
        """删除Agent"""
        if agent_id in self.agents:
            del self.agents[agent_id]
            # 保存到磁盘
            self._save_agents_to_disk()
            return True
        return False

# 全局Agent工厂实例
agent_factory = AgentFactory()

