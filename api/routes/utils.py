"""Utility API routes (tool types, parameter types, presets)"""

from fastapi import APIRouter
import uuid

from models import ToolType, ParameterType

router = APIRouter(prefix="/api", tags=["utils"])


@router.get("/tool-types")
async def get_tool_types():
    """Get available tool types"""
    return [
        {"value": tool_type.value, "label": tool_type.value}
        for tool_type in ToolType
    ]


@router.get("/parameter-types")
async def get_parameter_types():
    """Get available parameter types"""
    return [
        {"value": param_type.value, "label": param_type.value}
        for param_type in ParameterType
    ]


@router.get("/presets")
async def get_preset_configs():
    """Get preset Agent configuration templates"""
    presets = {
        "customer_service": {
            "name": "客服助手",
            "description": "专业的在线客服助手",
            "system_prompt": "你是一个专业的在线客服助手，请礼貌、耐心地回答用户问题。",
            "user_prompt_template": "用户问题：{user_input}\n请提供专业、有帮助的回答。",
            "input_format": [],
            "output_format": [],
            "tools": [
                {
                    "id": str(uuid.uuid4()),
                    "name": "knowledge_search",
                    "description": "搜索知识库",
                    "type": "knowledge_base",
                    "parameters": [],
                    "config": {}
                }
            ]
        },
        "content_writer": {
            "name": "内容创作助手",
            "description": "专业的文案创作助手",
            "system_prompt": "你是一个专业的内容创作助手，擅长各种文案写作。",
            "user_prompt_template": "请根据以下要求创作内容：{user_input}",
            "input_format": [],
            "output_format": [],
            "tools": [
                {
                    "id": str(uuid.uuid4()),
                    "name": "web_search",
                    "description": "网络搜索",
                    "type": "web_search",
                    "parameters": [],
                    "config": {}
                }
            ]
        },
        "data_analyst": {
            "name": "数据分析师",
            "description": "专业的数据分析助手",
            "system_prompt": "你是一个专业的数据分析师，能够处理和分析各种数据。",
            "user_prompt_template": "请分析以下数据：{user_input}",
            "input_format": [],
            "output_format": [],
            "tools": [
                {
                    "id": str(uuid.uuid4()),
                    "name": "calculator",
                    "description": "计算器",
                    "type": "calculator",
                    "parameters": [],
                    "config": {}
                }
            ]
        }
    }
    return presets
