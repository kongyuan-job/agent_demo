"""
Tool factory for creating tools from configuration
"""

from typing import Dict, Type
from langchain_core.tools import Tool as LangChainTool
from models import Tool as ToolConfig, ToolType
from .calculator import CalculatorTool
from .web_search import WebSearchTool
from .knowledge_base import KnowledgeBaseTool
from .api_call import APICallTool
from .base import BaseTool


class ToolFactory:
    """Factory for creating LangChain tools from configuration"""
    
    # Registry of tool types to implementation classes
    _tool_registry: Dict[ToolType, Type[BaseTool]] = {
        ToolType.CALCULATOR: CalculatorTool,
        ToolType.WEB_SEARCH: WebSearchTool,
        ToolType.KNOWLEDGE_BASE: KnowledgeBaseTool,
        ToolType.API_CALL: APICallTool,
    }
    
    @classmethod
    def create_tool(cls, tool_config: ToolConfig) -> LangChainTool:
        """
        Create a LangChain tool from configuration
        
        Args:
            tool_config: Tool configuration object
            
        Returns:
            LangChain Tool instance
            
        Raises:
            ValueError: If tool type is not supported
        """
        tool_class = cls._tool_registry.get(tool_config.type)
        
        if not tool_class:
            # Handle custom function or unknown types
            if tool_config.type == ToolType.CUSTOM_FUNCTION:
                return cls._create_custom_function_tool(tool_config)
            raise ValueError(f"Unsupported tool type: {tool_config.type}")
        
        return tool_class.from_config(tool_config)
    
    @classmethod
    def _create_custom_function_tool(cls, tool_config: ToolConfig) -> LangChainTool:
        """Create a custom function tool"""
        from pydantic import BaseModel, Field, create_model
        
        # Create input schema from parameters
        if tool_config.parameters:
            fields = {}
            for param in tool_config.parameters:
                field_type = str
                if param.type == "integer":
                    field_type = int
                elif param.type == "float":
                    field_type = float
                elif param.type == "boolean":
                    field_type = bool
                
                if param.required:
                    fields[param.name] = (field_type, Field(description=param.description))
                else:
                    fields[param.name] = (
                        field_type,
                        Field(default=param.default_value, description=param.description)
                    )
            
            CustomFunctionInput = create_model('CustomFunctionInput', **fields)
        else:
            class CustomFunctionInput(BaseModel):
                input_data: dict = Field(
                    default={},
                    description="自定义函数的输入参数"
                )
        
        async def custom_func(**kwargs) -> str:
            # TODO: Implement custom function execution in sandbox
            return f"自定义函数执行结果: {kwargs}"
        
        return LangChainTool(
            name=tool_config.name,
            description=tool_config.description or "执行自定义函数",
            func=custom_func,
            args_schema=CustomFunctionInput,
            coroutine=custom_func
        )
    
    @classmethod
    def register_tool(cls, tool_type: ToolType, tool_class: Type[BaseTool]) -> None:
        """
        Register a new tool type
        
        Args:
            tool_type: The tool type enum value
            tool_class: The tool implementation class
        """
        cls._tool_registry[tool_type] = tool_class
    
    @classmethod
    def get_supported_types(cls) -> list[ToolType]:
        """Get list of supported tool types"""
        return list(cls._tool_registry.keys())
