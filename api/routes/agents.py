"""Agent management API routes"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from datetime import datetime
import uuid

from models import AgentConfig, AgentResponse, ToolType
from agent_factory import agent_factory

router = APIRouter(prefix="/api/agents", tags=["agents"])


@router.post("", response_model=AgentResponse)
async def create_agent(config: AgentConfig):
    """Create a new AI Agent"""
    try:
        # Generate ID and timestamps
        if not config.id:
            config.id = str(uuid.uuid4())
        
        # Generate IDs for tools (if missing)
        for tool in config.tools:
            if not tool.id:
                tool.id = str(uuid.uuid4())
            # Ensure type is set correctly
            if isinstance(tool.type, str):
                tool.type = ToolType(tool.type)
        
        config.created_at = datetime.now().isoformat()
        config.updated_at = datetime.now().isoformat()
        
        # Create Agent
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


@router.get("", response_model=List[Dict[str, Any]])
async def get_agents():
    """Get all Agent list"""
    try:
        return agent_factory.get_agent_list()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取Agent列表失败: {str(e)}")


@router.get("/{agent_id}")
async def get_agent(agent_id: str):
    """Get specific Agent configuration"""
    try:
        config = agent_factory.get_agent_config(agent_id)
        if not config:
            raise HTTPException(status_code=404, detail="Agent不存在")
        return config.dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取Agent配置失败: {str(e)}")


@router.put("/{agent_id}", response_model=AgentResponse)
async def update_agent(agent_id: str, config: AgentConfig):
    """Update Agent configuration"""
    try:
        config.id = agent_id
        config.updated_at = datetime.now().isoformat()
        
        # Generate IDs for tools (if missing)
        for tool in config.tools:
            if not tool.id:
                tool.id = str(uuid.uuid4())
        
        # Recreate Agent
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


@router.delete("/{agent_id}", response_model=AgentResponse)
async def delete_agent(agent_id: str):
    """Delete Agent"""
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
