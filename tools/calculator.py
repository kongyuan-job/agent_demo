"""
Calculator tool implementation
"""

from pydantic import BaseModel, Field
from langchain_core.tools import Tool as LangChainTool
from models import Tool as ToolConfig
from .base import BaseTool


class CalculatorInput(BaseModel):
    """Input schema for calculator tool"""
    expression: str = Field(
        description="需要计算的数学表达式，例如: '1+1', '2*3', '(1+1)*3'"
    )


class CalculatorTool(BaseTool):
    """Calculator tool for mathematical expressions"""
    
    @classmethod
    def from_config(cls, tool_config: ToolConfig) -> LangChainTool:
        """Create calculator tool from configuration"""
        return LangChainTool(
            name=tool_config.name,
            description=tool_config.description or "用于计算数学表达式",
            func=lambda expression: cls._calculate(expression),
            args_schema=CalculatorInput
        )
    
    @staticmethod
    def get_input_schema() -> type[BaseModel]:
        """Get the input schema"""
        return CalculatorInput
    
    @staticmethod
    def _calculate(expression: str) -> str:
        """Execute calculation"""
        try:
            # Security: only allow safe characters
            allowed_chars = set('0123456789+-*/.() ')
            if not all(c in allowed_chars for c in expression):
                return "错误: 包含不安全的字符"
            
            result = eval(expression)
            return f"计算结果: {result}"
        except Exception as e:
            return f"计算错误: {str(e)}"
    
    @staticmethod
    async def execute(**kwargs) -> str:
        """Execute the calculator tool"""
        expression = kwargs.get('expression', '')
        return CalculatorTool._calculate(expression)
