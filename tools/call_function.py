"""
Call function tool - for custom API/Lambda function invocations
"""

from typing import Dict, Any
from pydantic import BaseModel, Field, create_model
from langchain_core.tools import Tool as LangChainTool
from .base import BaseTool
import httpx
import json


class CallFunctionInput(BaseModel):
    """Default input schema for call function tool"""
    input_data: dict = Field(
        default_factory=dict,
        description="Input parameters for the function call"
    )


class CallFunctionTool(BaseTool):
    """Tool for calling custom functions (API, Lambda, etc.)"""
    
    @classmethod
    def from_config(cls, tool_config: Dict[str, Any]) -> LangChainTool:
        """
        Create call function tool from configuration
        
        Args:
            tool_config: Dictionary containing tool configuration
                - name: Function name
                - description: Function description
                - function_type: Type of function (api, lambda, etc.)
                - config: Function-specific configuration
                    - url: API endpoint URL (for api type)
                    - method: HTTP method (for api type)
                    - headers: HTTP headers (for api type)
                    - lambda_arn: Lambda ARN (for lambda type)
                - parameters: Optional list of input parameters
                
        Returns:
            LangChain Tool instance
        """
        # Create dynamic input schema if parameters are defined
        input_schema = cls._create_input_schema(tool_config)
        
        # Capture config for closure
        config = tool_config.get('config', {})
        func_type = tool_config.get('function_type', 'api')
        
        async def call_func(**kwargs) -> str:
            return await cls.execute(
                function_type=func_type,
                config=config,
                **kwargs
            )
        
        # Build detailed description
        description = tool_config.get('description', 'Execute custom function')
        if func_type:
            description += f"\nFunction Type: {func_type}"
        if config.get('url'):
            description += f"\nEndpoint: {config['url']}"
        
        return LangChainTool(
            name=tool_config.get('name', 'custom_function'),
            description=description,
            func=call_func,
            args_schema=input_schema,
            coroutine=call_func
        )
    
    @staticmethod
    def get_input_schema() -> type[BaseModel]:
        """Get default input schema"""
        return CallFunctionInput
    
    @staticmethod
    def _create_input_schema(tool_config: Dict[str, Any]) -> type[BaseModel]:
        """Create dynamic input schema from parameters"""
        parameters = tool_config.get('parameters', [])
        
        if not parameters:
            return CallFunctionTool.get_input_schema()
        
        # Build fields for dynamic model
        fields = {}
        for param in parameters:
            param_name = param.get('name', 'param')
            param_type = param.get('type', 'string')
            param_desc = param.get('description', '')
            param_required = param.get('required', False)
            param_default = param.get('default_value')
            
            # Map parameter types to Python types
            type_mapping = {
                'string': str,
                'String': str,
                'integer': int,
                'Integer': int,
                'float': float,
                'Float': float,
                'boolean': bool,
                'Boolean': bool,
                'array': list,
                'Array': list,
                'object': dict,
                'Object': dict,
            }
            
            field_type = type_mapping.get(param_type, str)
            
            if param_required:
                fields[param_name] = (field_type, Field(description=param_desc))
            else:
                fields[param_name] = (
                    field_type,
                    Field(default=param_default, description=param_desc)
                )
        
        return create_model('CallFunctionInput', **fields)
    
    @staticmethod
    async def execute(function_type: str = 'api', config: Dict[str, Any] = None, **kwargs) -> str:
        """
        Execute the custom function call
        
        Args:
            function_type: Type of function (api, lambda, etc.)
            config: Function configuration
            **kwargs: Function input parameters
            
        Returns:
            Execution result as string
        """
        if not config:
            config = {}
        
        if function_type == 'api':
            return await CallFunctionTool._execute_api_call(config, kwargs)
        elif function_type == 'lambda':
            return await CallFunctionTool._execute_lambda_call(config, kwargs)
        else:
            return f"Unsupported function type: {function_type}"
    
    @staticmethod
    async def _execute_api_call(config: Dict[str, Any], params: Dict[str, Any]) -> str:
        """Execute API call"""
        url = config.get('url', '')
        method = config.get('method', 'POST').upper()
        headers = config.get('headers', {})
        
        if not url:
            return "Error: API URL not configured"
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                if method == 'GET':
                    response = await client.get(url, headers=headers, params=params)
                elif method == 'POST':
                    response = await client.post(url, headers=headers, json=params)
                elif method == 'PUT':
                    response = await client.put(url, headers=headers, json=params)
                elif method == 'DELETE':
                    response = await client.delete(url, headers=headers, params=params)
                else:
                    return f"Unsupported HTTP method: {method}"
                
                response.raise_for_status()
                
                # Try to parse JSON response
                try:
                    result = response.json()
                    return json.dumps(result, ensure_ascii=False, indent=2)
                except:
                    return response.text
                    
        except httpx.TimeoutException:
            return f"API call timeout: {url}"
        except httpx.HTTPError as e:
            return f"API call failed: {str(e)}"
        except Exception as e:
            return f"Unexpected error: {str(e)}"
    
    @staticmethod
    async def _execute_lambda_call(config: Dict[str, Any], params: Dict[str, Any]) -> str:
        """Execute AWS Lambda function call"""
        # TODO: Implement Lambda invocation using boto3
        lambda_arn = config.get('lambda_arn', '')
        
        if not lambda_arn:
            return "Error: Lambda ARN not configured"
        
        # Placeholder implementation
        return f"Lambda function {lambda_arn} invoked with params: {json.dumps(params)}\n(Implementation pending: requires boto3 integration)"
