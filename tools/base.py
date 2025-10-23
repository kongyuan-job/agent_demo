"""
Base tool class for all tool implementations
"""

from abc import ABC, abstractmethod
from typing import Any, Dict
from pydantic import BaseModel
from langchain_core.tools import Tool as LangChainTool


class BaseTool(ABC):
    """Base class for all tool implementations"""
    
    @classmethod
    @abstractmethod
    def from_config(cls, tool_config) -> LangChainTool:
        """Create a LangChain tool from configuration"""
        pass
    
    @staticmethod
    @abstractmethod
    def get_input_schema() -> type[BaseModel]:
        """Get the Pydantic input schema for this tool"""
        pass
    
    @staticmethod
    @abstractmethod
    async def execute(**kwargs) -> str:
        """Execute the tool with given parameters"""
        pass
