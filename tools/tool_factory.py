"""
Tool factory for creating tools from configuration
"""

from typing import Dict
from langchain_core.tools import Tool as LangChainTool
from .calculator import CalculatorTool
from .web_search import WebSearchTool
from .knowledge_base import KnowledgeBaseTool
from .api_call import APICallTool


class ToolFactory:
    """工具工厂 - 从配置创建 LangChain 工具"""
    
    # 系统工具映射
    _system_tools = {
        'calculator': CalculatorTool,
        'web_search': WebSearchTool,
        'knowledge_base': KnowledgeBaseTool,
    }
    
    @classmethod
    def create_tool(cls, tool_config: Dict) -> LangChainTool:
        """
        从配置字典创建 LangChain 工具
        
        Args:
            tool_config: 工具配置字典
            
        Returns:
            LangChain Tool 实例
            
        Raises:
            ValueError: 如果工具类型不支持
        """
        tool_type = tool_config.get('type')
        
        if tool_type == 'system_function':
            return cls._create_system_function_tool(tool_config)
        elif tool_type == 'call_function':
            return cls._create_call_function_tool(tool_config)
        elif tool_type == 'query_objects':
            return cls._create_query_objects_tool(tool_config)
        else:
            raise ValueError(f"不支持的工具类型: {tool_type}")
    
    @classmethod
    def _create_system_function_tool(cls, tool_config: Dict) -> LangChainTool:
        """创建系统函数工具"""
        func_name = tool_config.get('name', 'calculator')
        tool_class = cls._system_tools.get(func_name)
        
        if not tool_class:
            raise ValueError(f"未知的系统工具: {func_name}")
        
        # 创建一个简单的模拟配置对象
        class MockToolConfig:
            def __init__(self, name, description):
                self.name = name
                self.description = description
                self.type = name
                self.parameters = []
                self.config = {}
        
        mock_config = MockToolConfig(
            name=tool_config.get('name', func_name),
            description=tool_config.get('description', f'{func_name} tool')
        )
        
        try:
            return tool_class.from_config(mock_config)
        except Exception as e:
            # Fallback: create a basic tool
            print(f"Warning: Failed to create {func_name} tool: {e}")
            return cls._create_basic_tool(tool_config)
    @classmethod
    def _create_call_function_tool(cls, tool_config: Dict) -> LangChainTool:
        """创建自定义函数调用工具"""
        from pydantic import BaseModel, Field
        
        class CallFunctionInput(BaseModel):
            input_data: dict = Field(
                default={},
                description="函数输入参数"
            )
        
        async def call_func(**kwargs) -> str:
            # TODO: Implement actual function execution
            func_name = tool_config.get('name', 'unknown')
            func_type = tool_config.get('function_type', 'api')
            config = tool_config.get('config', {})
            return f"函数 {func_name} (类型: {func_type}) 执行结果 (placeholder)\n配置: {config}\n参数: {kwargs}"
        
        return LangChainTool(
            name=tool_config.get('name', 'custom_function'),
            description=tool_config.get('description', '执行自定义函数'),
            func=call_func,
            args_schema=CallFunctionInput,
            coroutine=call_func
        )
    
    @classmethod
    def _create_basic_tool(cls, tool_config: Dict) -> LangChainTool:
        """创建基础工具（fallback）"""
        from pydantic import BaseModel, Field
        
        class BasicInput(BaseModel):
            query: str = Field(description="工具输入")
        
        async def basic_func(query: str) -> str:
            return f"Tool {tool_config.get('name', 'unknown')} executed with: {query}"
        
        return LangChainTool(
            name=tool_config.get('name', 'tool'),
            description=tool_config.get('description', 'A basic tool'),
            func=basic_func,
            args_schema=BasicInput,
            coroutine=basic_func
        )
    
    @classmethod
    def _create_query_objects_tool(cls, tool_config: Dict) -> LangChainTool:
        """Create a query objects tool for graph database queries"""
        from pydantic import BaseModel, Field
        
        class QueryObjectsInput(BaseModel):
            query: str = Field(description="Query string for graph database")
        
        async def query_objects_func(query: str) -> str:
            # TODO: Implement actual graph database query
            objects = tool_config.get('objects', [])
            object_descriptions = []
            for obj in objects:
                obj_desc = f"Object: {obj.get('object_code')} - {obj.get('object_description')}"
                fields = obj.get('fields', [])
                if fields:
                    field_list = ", ".join([f"{f.get('field_name')}: {f.get('field_description')}" for f in fields])
                    obj_desc += f" (Fields: {field_list})"
                object_descriptions.append(obj_desc)
            
            return f"Graph database query result (placeholder):\n" + "\n".join(object_descriptions)
        
        return LangChainTool(
            name="query_objects",
            description=tool_config.get('description', "Query graph database for objects and their fields"),
            func=query_objects_func,
            args_schema=QueryObjectsInput,
            coroutine=query_objects_func
        )
    
    @classmethod
    def get_supported_tool_types(cls) -> list[str]:
        """获取支持的工具类型列表"""
        return ['system_function', 'call_function', 'query_objects']
