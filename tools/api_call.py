"""
API call tool implementation
"""

from typing import Dict, Any
from pydantic import BaseModel, Field, create_model
from langchain_core.tools import Tool as LangChainTool
from .base import BaseTool
import httpx


class APICallTool(BaseTool):
    """API call tool for external API integration"""
    
    @classmethod
    def from_config(cls, tool_config) -> LangChainTool:
        """Create API call tool from configuration"""
        # Create dynamic input schema based on parameters
        input_schema = cls._create_input_schema(tool_config)
        
        async def api_call_func(**kwargs) -> str:
            return await cls.execute(config=tool_config.config, **kwargs)
        
        # Build detailed description
        api_description = tool_config.description or "调用外部API接口"
        if tool_config.config.get("url"):
            api_description += f"\nAPI地址: {tool_config.config['url']}"
        if tool_config.config.get("method"):
            api_description += f"\n请求方法: {tool_config.config['method']}"
        
        return LangChainTool(
            name=tool_config.name,
            description=api_description,
            func=api_call_func,
            args_schema=input_schema,
            coroutine=api_call_func
        )
    
    @staticmethod
    def get_input_schema() -> type[BaseModel]:
        """Get default input schema"""
        class DefaultAPIInput(BaseModel):
            params: dict = Field(
                default={},
                description="API调用参数，以JSON对象形式传递"
            )
        return DefaultAPIInput
    
    @staticmethod
    def _create_input_schema(tool_config) -> type[BaseModel]:
        """从工具参数创建动态输入模式"""
        # 如果没有参数，返回默认schema
        if not hasattr(tool_config, 'parameters') or not tool_config.parameters:
            return APICallTool.get_input_schema()
        
        # 为动态模型构建字段字典
        fields = {}
        for param in tool_config.parameters:
            field_type = str
            # 简单处理，不依赖ParameterType enum
            param_type = getattr(param, 'type', 'string')
            if param_type in ('integer', 'Integer'):
                field_type = int
            elif param_type in ('float', 'Float'):
                field_type = float
            elif param_type in ('boolean', 'Boolean'):
                field_type = bool
            
            if getattr(param, 'required', False):
                fields[param.name] = (field_type, Field(description=getattr(param, 'description', '')))
            else:
                fields[param.name] = (
                    field_type,
                    Field(default=getattr(param, 'default_value', None), description=getattr(param, 'description', ''))
                )
        
        return create_model('APICallInput', **fields)
    
    @staticmethod
    async def execute(config: Dict[str, Any] | None = None, **kwargs) -> str:
        """Execute API call"""
        if not config:
            return "错误: 缺少API配置"
        
        url = config.get("url", "")
        method = config.get("method", "GET").upper()
        headers = config.get("headers", {})
        
        try:
            async with httpx.AsyncClient() as client:
                if method == "GET":
                    response = await client.get(url, headers=headers, params=kwargs)
                elif method == "POST":
                    response = await client.post(url, headers=headers, json=kwargs)
                else:
                    return f"不支持的HTTP方法: {method}"
                
                return f"API调用结果: {response.text}"
        except Exception as e:
            return f"API调用失败: {str(e)}"
