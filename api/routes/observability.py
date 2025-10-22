"""Observability API routes"""

from fastapi import APIRouter, HTTPException
from typing import Optional
from datetime import datetime

from observability import observability_manager

router = APIRouter(prefix="/api/observability", tags=["observability"])


@router.get("/metrics")
async def get_agent_metrics(agent_id: Optional[str] = None):
    """Get Agent performance metrics"""
    try:
        if agent_id:
            metrics = observability_manager.get_agent_metrics(agent_id)
            return {"success": True, "data": metrics.__dict__ if metrics else None}
        else:
            metrics = observability_manager.get_all_metrics()
            return {"success": True, "data": [m.__dict__ for m in metrics]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取指标失败: {str(e)}")


@router.get("/history")
async def get_execution_history(agent_id: str, limit: int = 100):
    """Get Agent execution history"""
    try:
        executions = observability_manager.get_execution_history(agent_id, limit)
        return {"success": True, "data": [e.__dict__ for e in executions]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取执行历史失败: {str(e)}")


@router.get("/tool-calls")
async def get_tool_calls(execution_id: str):
    """Get tool calls during execution"""
    try:
        tool_calls = observability_manager.get_tool_calls(execution_id)
        return {"success": True, "data": [t.__dict__ for t in tool_calls]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取工具调用失败: {str(e)}")


@router.get("/llm-calls")
async def get_llm_calls(execution_id: str):
    """Get LLM calls during execution"""
    try:
        llm_calls = observability_manager.get_llm_calls(execution_id)
        return {"success": True, "data": [l.__dict__ for l in llm_calls]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取LLM调用失败: {str(e)}")


@router.get("/execution-timeline")
async def get_execution_timeline(execution_id: str):
    """Get complete execution timeline (including tool calls and LLM calls)"""
    try:
        # Get tool calls and LLM calls
        tool_calls = observability_manager.get_tool_calls(execution_id)
        llm_calls = observability_manager.get_llm_calls(execution_id)
        
        # Merge and sort by time
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
        
        # Sort by timestamp
        timeline.sort(key=lambda x: x["timestamp"])
        
        return {"success": True, "data": timeline}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取执行时间线失败: {str(e)}")


@router.get("/export")
async def export_observability_data(agent_id: Optional[str] = None, format: str = "json"):
    """Export observability data"""
    try:
        data = observability_manager.export_data(agent_id, format)
        return {"success": True, "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出数据失败: {str(e)}")


@router.get("/dashboard")
async def get_observability_dashboard():
    """Get observability dashboard data"""
    try:
        # Get all Agent metrics
        all_metrics = observability_manager.get_all_metrics()
        
        # Calculate overall statistics
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
