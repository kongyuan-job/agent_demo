import time
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from typing_extensions import TypedDict
from typing import Annotated
import operator

from models import AgentConfig, ChatRequest, ChatMessage
from config import Config
from observability import log_tool_call, log_llm_call, observability_manager, AgentExecution
from core import AgentManager
from tools import ToolFactory
from utils.formatters import PromptFormatter

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
    """动态Agent创建工厂类 - 重构版本"""
    
    def __init__(self):
        # 使用新的AgentManager处理CRUD操作
        self.agent_manager = AgentManager()
        # Agent graph缓存（graph不能序列化，需要运行时重建）
        self._graph_cache: Dict[str, Any] = {}
        self._rebuild_graphs()
    
    def _rebuild_graphs(self):
        """重建所有Agent的graph实例"""
        for agent_data in self.agent_manager.get_agent_list():
            agent_id = agent_data["id"]
            config = self.agent_manager.get_agent_config(agent_id)
            if config:
                self._graph_cache[agent_id] = self._create_agent_graph(config)
        print(f"Loaded {len(self._graph_cache)} agents from disk")
    
    # Tool creation now delegated to ToolFactory - no need for these methods
    
    def _create_agent_graph(self, config: AgentConfig):
        """根据配置动态创建LangGraph Agent"""
        llm = ChatOpenAI(
            model="deepseek-chat",
            temperature=0.1
        )
        # 使用ToolFactory创建工具列表
        tools = [ToolFactory.create_tool(tool_config) for tool_config in config.tools]
        
        tool_node = ToolNode(tools) if tools else None
        if tools:
            llm = llm.bind_tools(tools)
        
        def agent_node(state: AgentState) -> AgentState:
            """Agent节点处理逻辑 - 支持动态输入输出类型"""
            messages = state.get("messages", [])
            execution_id = state.get("execution_id", "")
            agent_id = state.get("agent_id", "")
            
            # 使用PromptFormatter添加工具指导
            system_prompt_text = config.system_prompt.value if hasattr(config.system_prompt, 'value') else str(config.system_prompt)
            system_prompt = PromptFormatter.add_tool_guidance(system_prompt_text, bool(tools))
            
            system_message: SystemMessage = SystemMessage(content=system_prompt)
            
            # 处理动态输入类型
            user_input = state.get("user_input", "")
            input_data = state.get("input_data", {}) or {}  # Ensure it's never None
            
            # 使用PromptFormatter格式化用户输入
            task_prompt_text = config.task_prompt.value if hasattr(config.task_prompt, 'value') else str(config.task_prompt)
            formatted_input = PromptFormatter.format_user_input(
                task_prompt_text,
                user_input,
                input_data
            )
            
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
                    system_prompt_text = config.system_prompt.value if hasattr(config.system_prompt, 'value') else str(config.system_prompt)
                    log_llm_call(
                        execution_id=execution_id,
                        agent_id=agent_id,
                        model="deepseek-chat",
                        messages=[
                            {"role": "system", "content": system_prompt_text},
                            *[{"role": m.type, "content": m.content} for m in messages],
                            {"role": "user", "content": formatted_input}
                        ],
                        response=str(response.content),
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
            import json as json_module
            output_data = {}
            if config.output:
                # 如果有输出格式定义，尝试解析为结构化数据
                try:
                    # 简单的JSON解析尝试
                    content_str = str(response.content) if response.content else ""
                    output_data = json_module.loads(content_str)
                except (json_module.JSONDecodeError, ValueError):
                    # 如果不是JSON，保持为字符串
                    output_data = {"content": str(response.content)}
            else:
                # 没有输出格式定义，直接使用内容
                output_data = {"content": str(response.content)}
            
            return {
                "messages": [response],
                "response": str(response.content),
                "output_data": output_data,
                "user_input": state.get("user_input"),
                "input_data": state.get("input_data"),
                "execution_id": state.get("execution_id"),
                "agent_id": state.get("agent_id")
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
            if tool_node is None:
                return state
            
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
        
        # 不使用checkpointer - 对话历史由前端通过conversation_history管理
        return workflow.compile()
    
    async def create_agent(self, config: AgentConfig) -> str:
        """创建Agent并返回ID"""
        # 使用AgentManager创建Agent（处理持久化）
        agent_id = await self.agent_manager.create_agent(config)
        
        # 创建并缓存graph实例
        self._graph_cache[agent_id] = self._create_agent_graph(config)
        
        return agent_id
    
    async def chat_with_agent_stream(self, request: ChatRequest):
        """与Agent对话 - 流式输出版本"""
        agent_id = request.agent_id
        start_time = time.time()
        execution_id = str(uuid.uuid4())  # Initialize early to avoid unbound variable error
        streaming_tokens = False  # Initialize to avoid unbound variable error
        
        # 使用AgentManager获取配置
        config = self.agent_manager.get_agent_config(agent_id)
        if not config:
            error_msg = f"Agent {agent_id} 不存在"
            yield {
                "type": "error",
                "message": error_msg,
                "timestamp": datetime.now().isoformat()
            }
            return
        
        # 从缓存获取graph
        agent_graph = self._graph_cache.get(agent_id)
        if not agent_graph:
            # 如果缓存中没有，重建
            agent_graph = self._create_agent_graph(config)
            self._graph_cache[agent_id] = agent_graph
        
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
            
            # 流式执行Agent - 不需要thread_id,因为不使用checkpointer
            from langchain_core.runnables import RunnableConfig
            runnable_config = RunnableConfig(recursion_limit=50)  # Increase limit to prevent premature termination
            
            # Track if we're in a token streaming phase
            final_result = None
            
            async for event in agent_graph.astream(initial_state, runnable_config):
                # event 是一个字典，key是节点名，value是该节点的输出
                for node_name, node_output in event.items():
                    if node_name == "agent":
                        # Agent节点输出
                        messages = node_output.get("messages", [])
                        if messages:
                            last_message = messages[-1]
                            
                            # LLM响应 - token level streaming
                            if hasattr(last_message, 'content'):
                                content = last_message.content
                                # If we have content, stream it token by token
                                if content:
                                    # Send token_start event when we begin streaming
                                    if not streaming_tokens:
                                        yield {
                                            "type": "token_stream_start",
                                            "timestamp": datetime.now().isoformat()
                                        }
                                        streaming_tokens = True
                                    
                                    # Stream each character/token as it arrives
                                    content_str = str(content)
                                    for char in content_str:
                                        yield {
                                            "type": "token",
                                            "content": char,
                                            "timestamp": datetime.now().isoformat()
                                        }
                            
                            # 工具调用
                            if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
                                # End any ongoing token streaming
                                if streaming_tokens:
                                    yield {
                                        "type": "token_stream_end",
                                        "timestamp": datetime.now().isoformat()
                                    }
                                    streaming_tokens = False
                                    
                                for tool_call in last_message.tool_calls:
                                    yield {
                                        "type": "tool_call_start",
                                        "tool_name": tool_call.get('name', 'unknown'),
                                        "tool_args": tool_call.get('args', {}),
                                        "timestamp": datetime.now().isoformat()
                                    }
                    
                    elif node_name == "tools":
                        # End any ongoing token streaming when entering tools
                        if streaming_tokens:
                            yield {
                                "type": "token_stream_end",
                                "timestamp": datetime.now().isoformat()
                            }
                            streaming_tokens = False
                            
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
            
            # End any remaining token streaming
            if streaming_tokens:
                yield {
                    "type": "token_stream_end",
                    "timestamp": datetime.now().isoformat()
                }
            
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
            # End any remaining token streaming on error
            if streaming_tokens:
                yield {
                    "type": "token_stream_end",
                    "timestamp": datetime.now().isoformat()
                }
                
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
        execution_id = str(uuid.uuid4())  # Initialize early to avoid unbound variable error
        
        # 使用AgentManager获取配置
        config = self.agent_manager.get_agent_config(agent_id)
        if not config:
            error_msg = f"Agent {agent_id} 不存在"
            final_execution = AgentExecution(
                execution_id=execution_id,
                agent_id=agent_id,
                user_input=request.user_input,
                response=None,
                input_type=type(request.user_input).__name__,
                output_type="None",
                execution_time=time.time() - start_time,
                timestamp=datetime.now().isoformat(),
                metadata={"error_type": "agent_not_found"},
                success=False,
                error_message=error_msg
            )
            observability_manager.log_execution(final_execution)
            return {
                "success": False,
                "message": error_msg,
                "response": None
            }
        
        # 从缓存获取graph
        agent_graph = self._graph_cache.get(agent_id)
        if not agent_graph:
            # 如果缓存中没有，重建
            agent_graph = self._create_agent_graph(config)
            self._graph_cache[agent_id] = agent_graph
        
        try:
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
            
            # 执行Agent - 不需要thread_id,因为不使用checkpointer
            from langchain_core.runnables import RunnableConfig
            runnable_config = RunnableConfig(recursion_limit=50)  # Increase limit to prevent premature termination
            result = await agent_graph.ainvoke(initial_state, runnable_config)
            
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
            
            return {
                "success": False,
                "message": error_msg,
                "response": None,
                "output_data": {}
            }
    
    def get_agent_list(self) -> List[Dict[str, Any]]:
        """获取Agent列表 - 委托给AgentManager"""
        return self.agent_manager.get_agent_list()
    
    def get_agent_config(self, agent_id: str) -> Optional[AgentConfig]:
        """获取Agent配置 - 委托给AgentManager"""
        return self.agent_manager.get_agent_config(agent_id)
    
    def delete_agent(self, agent_id: str) -> bool:
        """删除Agent - 委托给AgentManager"""
        # 从graph缓存中删除
        if agent_id in self._graph_cache:
            del self._graph_cache[agent_id]
        # 委托给AgentManager删除
        return self.agent_manager.delete_agent(agent_id)

# 全局Agent工厂实例
agent_factory = AgentFactory()