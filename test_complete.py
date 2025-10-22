#!/usr/bin/env python3
"""
完整测试脚本 - 验证AI Agent系统所有功能
"""

import asyncio
import json
from datetime import datetime

from models import AgentConfig, Tool, Parameter, ParameterType, ToolType, ChatRequest, ChatMessage
from agent_factory import agent_factory

async def test_agent_creation():
    """测试Agent创建功能"""
    print("测试Agent创建功能...")
    
    # 创建一个客服助手Agent
    agent_config = AgentConfig(
        id="test-customer-service",
        name="客服助手",
        description="专业的在线客服助手",
        system_prompt="你是一个专业的在线客服助手，请礼貌、耐心地回答用户问题。",
        user_prompt_template="用户问题：{user_input}\n请提供专业、有帮助的回答。",
        input_format=[
            Parameter(
                name="user_input",
                type=ParameterType.STRING,
                description="用户输入的问题",
                required=True
            )
        ],
        output_format=[
            Parameter(
                name="response",
                type=ParameterType.STRING,
                description="客服回复",
                required=True
            )
        ],
        tools=[
            Tool(
                id="knowledge-search",
                name="知识库搜索",
                description="搜索产品知识库",
                type=ToolType.KNOWLEDGE_BASE,
                parameters=[
                    Parameter(
                        name="query",
                        type=ParameterType.STRING,
                        description="搜索关键词",
                        required=True
                    )
                ]
            )
        ],
        temperature=0.7,
        max_tokens=1000,
        status="active",
        created_at=datetime.now().isoformat(),
        updated_at=datetime.now().isoformat()
    )
    
    # 创建Agent
    agent_id = await agent_factory.create_agent(agent_config)
    print(f"Agent创建成功，ID: {agent_id}")
    
    return agent_id

async def test_string_input():
    """测试字符串输入"""
    print("\n测试字符串输入...")
    
    agent_config = AgentConfig(
        id="test-string-agent",
        name="字符串处理Agent",
        description="处理字符串输入的Agent",
        system_prompt="你是一个字符串处理助手，请对输入进行适当处理。",
        user_prompt_template="用户输入：{user_input}\n请处理这个字符串。",
        input_format=[
            Parameter(
                name="user_input",
                type=ParameterType.STRING,
                description="用户输入的字符串",
                required=True
            )
        ],
        output_format=[
            Parameter(
                name="processed_text",
                type=ParameterType.STRING,
                description="处理后的文本",
                required=True
            )
        ],
        temperature=0.7,
        max_tokens=500,
        status="active",
        created_at=datetime.now().isoformat(),
        updated_at=datetime.now().isoformat()
    )
    
    agent_id = await agent_factory.create_agent(agent_config)
    
    # 测试字符串输入
    chat_request = ChatRequest(
        agent_id=agent_id,
        user_input="Hello, world! 请帮我翻译成中文。"
    )
    
    result = await agent_factory.chat_with_agent(chat_request)
    
    print(f"字符串输入测试:")
    print(f"   输入: {chat_request.user_input}")
    print(f"   输出: {result['response']}")
    
    return result

async def test_object_input():
    """测试对象输入"""
    print("\n测试对象输入...")
    
    agent_config = AgentConfig(
        id="test-object-agent",
        name="对象处理Agent",
        description="处理结构化对象输入的Agent",
        system_prompt="你是一个数据处理助手，请分析输入的结构化数据。",
        user_prompt_template="用户输入的数据：{user_input}\n数据详情：{name}, {age}岁, {city}人\n请分析这些数据。",
        input_format=[
            Parameter(
                name="name",
                type=ParameterType.STRING,
                description="姓名",
                required=True
            ),
            Parameter(
                name="age",
                type=ParameterType.INTEGER,
                description="年龄",
                required=True
            ),
            Parameter(
                name="city",
                type=ParameterType.STRING,
                description="城市",
                required=True
            )
        ],
        output_format=[
            Parameter(
                name="analysis",
                type=ParameterType.OBJECT,
                description="分析结果",
                required=True
            )
        ],
        temperature=0.7,
        max_tokens=500,
        status="active",
        created_at=datetime.now().isoformat(),
        updated_at=datetime.now().isoformat()
    )
    
    agent_id = await agent_factory.create_agent(agent_config)
    
    # 测试对象输入
    user_data = {
        "name": "张三",
        "age": 25,
        "city": "北京"
    }
    
    chat_request = ChatRequest(
        agent_id=agent_id,
        user_input=user_data,
        input_data=user_data
    )
    
    result = await agent_factory.chat_with_agent(chat_request)
    
    print(f"对象输入测试:")
    print(f"   输入: {chat_request.user_input}")
    print(f"   输出: {result['response']}")
    
    return result

async def test_mixed_input():
    """测试混合输入"""
    print("\n测试混合输入...")
    
    agent_config = AgentConfig(
        id="test-mixed-agent",
        name="混合输入Agent",
        description="处理混合类型输入的Agent",
        system_prompt="你是一个通用助手，可以处理各种类型的输入。",
        user_prompt_template="用户输入：{user_input}\n请根据输入类型进行处理。",
        input_format=[
            Parameter(
                name="user_input",
                type=ParameterType.STRING,
                description="用户输入",
                required=True
            ),
            Parameter(
                name="input_type",
                type=ParameterType.STRING,
                description="输入类型",
                required=False
            )
        ],
        output_format=[
            Parameter(
                name="result",
                type=ParameterType.OBJECT,
                description="处理结果",
                required=True
            )
        ],
        temperature=0.7,
        max_tokens=500,
        status="active",
        created_at=datetime.now().isoformat(),
        updated_at=datetime.now().isoformat()
    )
    
    agent_id = await agent_factory.create_agent(agent_config)
    
    # 测试不同类型的输入
    test_cases = [
        "简单的字符串输入",
        {"type": "json", "data": {"key": "value"}},
        123,
        ["列表", "输入", "测试"]
    ]
    
    for i, test_input in enumerate(test_cases):
        chat_request = ChatRequest(
            agent_id=agent_id,
            user_input=test_input,
            input_data={"input_type": type(test_input).__name__}
        )
        
        result = await agent_factory.chat_with_agent(chat_request)
        
        print(f"混合输入测试 {i+1}:")
        print(f"   输入类型: {type(test_input).__name__}")
        print(f"   输入内容: {test_input}")
        print(f"   输出: {result['response']}")
        print()
    
    return True

async def test_agent_list():
    """测试Agent列表功能"""
    print("测试Agent列表功能...")
    
    agent_list = agent_factory.get_agent_list()
    print(f"获取到 {len(agent_list)} 个Agent:")
    
    for agent in agent_list:
        print(f"   - {agent['name']} ({agent['id']}) - {agent['status']}")

async def main():
    """主测试函数"""
    print("AI Agent系统完整功能测试")
    print("=" * 50)
    
    try:
        # 测试Agent创建
        agent_id = await test_agent_creation()
        
        # 测试Agent列表
        await test_agent_list()
        
        # 测试字符串输入
        await test_string_input()
        
        # 测试对象输入
        await test_object_input()
        
        # 测试混合输入
        await test_mixed_input()
        
        print("=" * 50)
        print("所有测试完成!")
        
    except Exception as e:
        print(f"\n测试过程中出现错误: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
