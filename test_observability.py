#!/usr/bin/env python3
"""
可观测性功能测试脚本
"""

import asyncio
import time
from datetime import datetime

from models import AgentConfig, ChatRequest
from agent_factory import agent_factory
from observability import observability_manager, log_agent_execution

async def test_observability():
    """测试可观测性功能"""
    print("测试可观测性功能...")
    
    # 创建测试Agent
    agent_config = AgentConfig(
        id="test-observability-agent",
        name="可观测性测试Agent",
        description="用于测试可观测性功能的Agent",
        system_prompt="你是一个测试助手，请简单回复用户的问题。",
        user_prompt_template="用户问题：{user_input}\n请回答。",
        input_format=[],
        output_format=[],
        tools=[],
        temperature=0.7,
        max_tokens=500,
        status="active",
        created_at=datetime.now().isoformat(),
        updated_at=datetime.now().isoformat()
    )
    
    agent_id = await agent_factory.create_agent(agent_config)
    print(f"创建测试Agent: {agent_id}")
    
    # 模拟多次对话
    test_inputs = [
        "你好，请介绍一下你自己",
        {"type": "greeting", "message": "Hello"},
        ["测试", "数组", "输入"],
        123
    ]
    
    for i, user_input in enumerate(test_inputs):
        print(f"\n测试对话 {i+1}: {user_input}")
        
        chat_request = ChatRequest(
            agent_id=agent_id,
            user_input=user_input,
            input_data={"test_id": i+1}
        )
        
        result = await agent_factory.chat_with_agent(chat_request)
        
        if result["success"]:
            print(f"✓ 对话成功: {result['response'][:50]}...")
        else:
            print(f"✗ 对话失败: {result['message']}")
        
        # 等待一秒
        await asyncio.sleep(1)
    
    # 测试直接记录执行
    print("\n测试直接记录执行...")
    execution_id = log_agent_execution(
        agent_id=agent_id,
        user_input="直接记录测试",
        response="测试响应",
        execution_time=0.5,
        success=True,
        metadata={"test_type": "direct_logging"}
    )
    print(f"✓ 直接记录执行ID: {execution_id}")
    
    # 测试获取指标
    print("\n测试获取Agent指标...")
    metrics = observability_manager.get_agent_metrics(agent_id)
    if metrics:
        print(f"✓ Agent指标:")
        print(f"  总执行次数: {metrics.total_executions}")
        print(f"  成功次数: {metrics.successful_executions}")
        print(f"  失败次数: {metrics.failed_executions}")
        print(f"  平均执行时间: {metrics.avg_execution_time:.3f}s")
        print(f"  错误率: {metrics.error_rate:.2%}")
    else:
        print("✗ 未找到Agent指标")
    
    # 测试获取执行历史
    print("\n测试获取执行历史...")
    history = observability_manager.get_execution_history(agent_id, limit=10)
    print(f"✓ 获取到 {len(history)} 条执行历史")
    
    # 测试获取所有指标
    print("\n测试获取所有指标...")
    all_metrics = observability_manager.get_all_metrics()
    print(f"✓ 获取到 {len(all_metrics)} 个Agent的指标")
    
    # 测试数据导出
    print("\n测试数据导出...")
    export_data = observability_manager.export_data(agent_id, "json")
    print(f"✓ 导出数据长度: {len(export_data)} 字符")
    
    print("\n可观测性功能测试完成!")

async def main():
    """主测试函数"""
    print("可观测性功能测试")
    print("=" * 50)
    
    try:
        await test_observability()
        print("\n" + "=" * 50)
        print("✓ 所有测试通过!")
    except Exception as e:
        print(f"\n✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
