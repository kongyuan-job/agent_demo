"""Chat API routes"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from datetime import datetime
import json

from models import ChatRequest, ChatResponse
from agent_factory import agent_factory

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def chat_with_agent(request: ChatRequest):
    """Chat with Agent"""
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


@router.post("/stream")
async def chat_with_agent_stream(request: ChatRequest):
    """Stream chat (SSE) - Real LangGraph streaming output"""
    async def generate():
        try:
            async for event in agent_factory.chat_with_agent_stream(request):
                # Convert event to SSE format
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
        except Exception as e:
            error_event = {
                "type": "error",
                "message": str(e),
                "timestamp": datetime.now().isoformat()
            }
            yield f"data: {json.dumps(error_event, ensure_ascii=False)}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )
