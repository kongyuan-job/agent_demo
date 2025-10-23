"""
Tool factory for creating tools from configuration
"""

from typing import Dict
from langchain_core.tools import Tool as LangChainTool
from .system_function import SystemFunctionTool
from .call_function import CallFunctionTool
from .query_objects import QueryObjectsTool


class ToolFactory:
    """工具工厂 - 从配置创建 LangChain 工具"""
    
    # 工具类型映射 - 所有工具都继承自 BaseTool
    _tool_classes = {
        'system_function': SystemFunctionTool,
        'call_function': CallFunctionTool,
        'query_objects': QueryObjectsTool,
    }
    
    @classmethod
    def create_tool(cls, tool_config: Dict) -> LangChainTool:
        """
        从配置字典创建 LangChain 工具
        
        Args:
            tool_config: 工具配置字典，必须包含 'type' 字段
                - type: 工具类型 (system_function, call_function, query_objects)
                - name: 工具名称
                - description: 工具描述
                - 其他字段根据工具类型而定
            
        Returns:
            LangChain Tool 实例
            
        Raises:
            ValueError: 如果工具类型不支持
        """
        tool_type = tool_config.get('type')
        
        if not tool_type:
            raise ValueError("工具配置缺少 'type' 字段")
        
        tool_class = cls._tool_classes.get(tool_type)
        
        if not tool_class:
            supported_types = ', '.join(cls._tool_classes.keys())
            raise ValueError(
                f"不支持的工具类型: {tool_type}. "
                f"支持的类型: {supported_types}"
            )
        
        # 使用 BaseTool 的 from_config 方法创建工具
        return tool_class.from_config(tool_config)

    @classmethod
    def get_supported_tool_types(cls) -> list[str]:
        """获取支持的工具类型列表"""
        return list(cls._tool_classes.keys())
    
    @classmethod
    def get_available_system_functions(cls) -> list[str]:
        """获取可用的系统函数列表"""
        return SystemFunctionTool.get_available_functions()
