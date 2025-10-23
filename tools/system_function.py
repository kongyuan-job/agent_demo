"""
System function tool - wrapper for built-in system tools
"""

from typing import Dict, Any
from pydantic import BaseModel, Field
from langchain_core.tools import Tool as LangChainTool
from .base import BaseTool
from .calculator import CalculatorTool
from .web_search import WebSearchTool
from .knowledge_base import KnowledgeBaseTool


class SystemFunctionInput(BaseModel):
    """Input schema for system function tool"""
    query: str = Field(description="Input query for the system function")


class SystemFunctionTool(BaseTool):
    """Wrapper for built-in system tools (calculator, web_search, knowledge_base)"""
    
    # System tool registry
    SYSTEM_TOOLS = {
        'calculator': CalculatorTool,
        'web_search': WebSearchTool,
        'knowledge_base': KnowledgeBaseTool,
    }
    
    @classmethod
    def from_config(cls, tool_config: Dict[str, Any]) -> LangChainTool:
        """
        Create system function tool from configuration
        
        Args:
            tool_config: Dictionary containing tool configuration
                - name: Name of the system function (calculator, web_search, etc.)
                - description: Tool description
                
        Returns:
            LangChain Tool instance
        """
        func_name = tool_config.get('name', 'calculator')
        tool_class = cls.SYSTEM_TOOLS.get(func_name)
        
        if not tool_class:
            raise ValueError(f"Unknown system tool: {func_name}. Available: {list(cls.SYSTEM_TOOLS.keys())}")
        
        # Create mock config object for compatibility with existing tool classes
        class MockToolConfig:
            def __init__(self, name: str, description: str):
                self.name = name
                self.description = description
                self.type = name
                self.parameters = []
                self.config = {}
        
        mock_config = MockToolConfig(
            name=tool_config.get('name', func_name),
            description=tool_config.get('description', f'{func_name} tool')
        )
        
        # Delegate to the specific tool class
        return tool_class.from_config(mock_config)
    
    @staticmethod
    def get_input_schema() -> type[BaseModel]:
        """Get the input schema for system function tool"""
        return SystemFunctionInput
    
    @staticmethod
    async def execute(**kwargs) -> str:
        """
        Execute the system function tool
        
        Note: This method is not directly called for system functions,
        as each system tool has its own execute implementation.
        """
        return "System function executed (delegated to specific tool)"
    
    @classmethod
    def get_available_functions(cls) -> list[str]:
        """Get list of available system functions"""
        return list(cls.SYSTEM_TOOLS.keys())
