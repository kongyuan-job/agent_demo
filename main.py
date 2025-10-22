from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from typing import List, Dict, Any, Optional
import json
import asyncio
from datetime import datetime
from pathlib import Path

from models import (
    AgentConfig, AgentResponse, ChatRequest, ChatResponse,
    AgentStatus, Tool, Parameter, ParameterType, ToolType
)
from agent_factory import agent_factory
from config import Config
from observability import observability_manager

# 创建FastAPI应用
app = FastAPI(
    title="Palantir AI Agent System",
    description="动态AI Agent创建和管理平台",
    version="1.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境中应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件目录
static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "Palantir AI Agent System",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# Agent管理API
@app.post("/api/agents", response_model=AgentResponse)
async def create_agent(config: AgentConfig):
    """创建新的AI Agent"""
    try:
        # 生成ID和时间戳
        if not config.id:
            import uuid
            config.id = str(uuid.uuid4())
        
        # 为工具生成ID(如果缺失)
        for tool in config.tools:
            if not tool.id:
                import uuid
                tool.id = str(uuid.uuid4())
            # Ensure type is set correctly
            if isinstance(tool.type, str):
                # Convert string to ToolType enum if needed
                from models import ToolType
                tool.type = ToolType(tool.type)
        
        config.created_at = datetime.now().isoformat()
        config.updated_at = datetime.now().isoformat()
        
        # 创建Agent
        agent_id = await agent_factory.create_agent(config)
        
        return AgentResponse(
            success=True,
            message="Agent创建成功",
            data={
                "agent_id": agent_id,
                "config": config.dict()
            }
        )
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error creating agent: {error_details}")
        raise HTTPException(status_code=500, detail=f"创建Agent失败: {str(e)}")

@app.get("/api/agents", response_model=List[Dict[str, Any]])
async def get_agents():
    """获取所有Agent列表"""
    try:
        return agent_factory.get_agent_list()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取Agent列表失败: {str(e)}")

@app.get("/api/agents/{agent_id}")
async def get_agent(agent_id: str):
    """获取特定Agent的配置"""
    try:
        config = agent_factory.get_agent_config(agent_id)
        if not config:
            raise HTTPException(status_code=404, detail="Agent不存在")
        return config.dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取Agent配置失败: {str(e)}")

@app.put("/api/agents/{agent_id}", response_model=AgentResponse)
async def update_agent(agent_id: str, config: AgentConfig):
    """更新Agent配置"""
    try:
        config.id = agent_id
        config.updated_at = datetime.now().isoformat()
        
        # 为工具生成ID（如果缺失）
        for tool in config.tools:
            if not tool.id:
                import uuid
                tool.id = str(uuid.uuid4())
        
        # 重新创建Agent
        new_agent_id = await agent_factory.create_agent(config)
        
        return AgentResponse(
            success=True,
            message="Agent更新成功",
            data={
                "agent_id": new_agent_id,
                "config": config.dict()
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新Agent失败: {str(e)}")

@app.delete("/api/agents/{agent_id}", response_model=AgentResponse)
async def delete_agent(agent_id: str):
    """删除Agent"""
    try:
        success = agent_factory.delete_agent(agent_id)
        if not success:
            raise HTTPException(status_code=404, detail="Agent不存在")
        
        return AgentResponse(
            success=True,
            message="Agent删除成功"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除Agent失败: {str(e)}")

# 对话API
@app.post("/api/chat", response_model=ChatResponse)
async def chat_with_agent(request: ChatRequest):
    """与Agent对话"""
    try:
        result = await agent_factory.chat_with_agent(request)
        
        return ChatResponse(
            success=result["success"],
            message=result["message"],
            response=result.get("response"),
            output_data=result.get("output_data"),
            metadata=result.get("metadata")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"对话失败: {str(e)}")

@app.post("/api/chat/stream")
async def chat_with_agent_stream(request: ChatRequest):
    """流式对话（SSE）"""
    async def generate():
        try:
            # 这里可以实现流式响应
            result = await agent_factory.chat_with_agent(request)
            
            # 模拟流式输出
            response_text = result.get("response", "")
            words = response_text.split()
            
            for i, word in enumerate(words):
                chunk = {
                    "type": "chunk",
                    "content": word + " ",
                    "index": i,
                    "total": len(words)
                }
                yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
                await asyncio.sleep(0.1)  # 模拟延迟
            
            # 发送结束信号
            final_chunk = {
                "type": "done",
                "metadata": result.get("metadata", {})
            }
            yield f"data: {json.dumps(final_chunk, ensure_ascii=False)}\n\n"
            
        except Exception as e:
            error_chunk = {
                "type": "error",
                "message": str(e)
            }
            yield f"data: {json.dumps(error_chunk, ensure_ascii=False)}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream"
        }
    )

# 工具和参数类型API
@app.get("/api/tool-types")
async def get_tool_types():
    """获取可用的工具类型"""
    return [
        {"value": tool_type.value, "label": tool_type.value}
        for tool_type in ToolType
    ]

@app.get("/api/parameter-types")
async def get_parameter_types():
    """获取可用的参数类型"""
    return [
        {"value": param_type.value, "label": param_type.value}
        for param_type in ParameterType
    ]

# 预设配置API
@app.get("/api/presets")
async def get_preset_configs():
    """获取预设的Agent配置模板"""
    import uuid
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

# 可观测性API端点
@app.get("/api/observability/metrics")
async def get_agent_metrics(agent_id: Optional[str] = None):
    """获取Agent性能指标"""
    try:
        if agent_id:
            metrics = observability_manager.get_agent_metrics(agent_id)
            return {"success": True, "data": metrics.__dict__ if metrics else None}
        else:
            metrics = observability_manager.get_all_metrics()
            return {"success": True, "data": [m.__dict__ for m in metrics]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取指标失败: {str(e)}")

@app.get("/api/observability/history")
async def get_execution_history(agent_id: str, limit: int = 100):
    """获取Agent执行历史"""
    try:
        executions = observability_manager.get_execution_history(agent_id, limit)
        return {"success": True, "data": [e.__dict__ for e in executions]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取执行历史失败: {str(e)}")

@app.get("/api/observability/tool-calls")
async def get_tool_calls(execution_id: str):
    """获取执行过程中的工具调用"""
    try:
        tool_calls = observability_manager.get_tool_calls(execution_id)
        return {"success": True, "data": [t.__dict__ for t in tool_calls]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取工具调用失败: {str(e)}")

@app.get("/api/observability/llm-calls")
async def get_llm_calls(execution_id: str):
    """获取执行过程中的LLM调用"""
    try:
        llm_calls = observability_manager.get_llm_calls(execution_id)
        return {"success": True, "data": [l.__dict__ for l in llm_calls]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取LLM调用失败: {str(e)}")

@app.get("/api/observability/execution-timeline")
async def get_execution_timeline(execution_id: str):
    """获取执行过程的完整时间线（包括工具调用和LLM调用）"""
    try:
        # 获取工具调用和LLM调用
        tool_calls = observability_manager.get_tool_calls(execution_id)
        llm_calls = observability_manager.get_llm_calls(execution_id)
        
        # 合并并按时间排序
        timeline = []
        
        for tool_call in tool_calls:
            timeline.append({
                "type": "tool_call",
                "timestamp": tool_call.timestamp,
                "data": tool_call.__dict__
            })
        
        for llm_call in llm_calls:
            timeline.append({
                "type": "llm_call",
                "timestamp": llm_call.timestamp,
                "data": llm_call.__dict__
            })
        
        # 按时间排序
        timeline.sort(key=lambda x: x["timestamp"])
        
        return {"success": True, "data": timeline}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取执行时间线失败: {str(e)}")

@app.get("/api/observability/export")
async def export_observability_data(agent_id: Optional[str] = None, format: str = "json"):
    """导出可观测性数据"""
    try:
        data = observability_manager.export_data(agent_id, format)
        return {"success": True, "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出数据失败: {str(e)}")

@app.get("/api/observability/dashboard")
async def get_observability_dashboard():
    """获取可观测性仪表板数据"""
    try:
        # 获取所有Agent指标
        all_metrics = observability_manager.get_all_metrics()
        
        # 计算总体统计
        total_agents = len(all_metrics)
        total_executions = sum(m.total_executions for m in all_metrics)
        total_successful = sum(m.successful_executions for m in all_metrics)
        total_failed = sum(m.failed_executions for m in all_metrics)
        avg_error_rate = sum(m.error_rate for m in all_metrics) / total_agents if total_agents > 0 else 0
        
        dashboard_data = {
            "overview": {
                "total_agents": total_agents,
                "total_executions": total_executions,
                "total_successful": total_successful,
                "total_failed": total_failed,
                "avg_error_rate": avg_error_rate,
                "success_rate": (total_successful / total_executions * 100) if total_executions > 0 else 0
            },
            "agent_metrics": [m.__dict__ for m in all_metrics],
            "timestamp": datetime.now().isoformat()
        }
        
        return {"success": True, "data": dashboard_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取仪表板数据失败: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=Config.HOST,
        port=Config.PORT,
        reload=Config.DEBUG
    )

