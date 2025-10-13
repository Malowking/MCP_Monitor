"""
FastAPI路由 - API接口定义
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from loguru import logger

from models.base_model import Message


router = APIRouter(prefix="/api/v1", tags=["MCP Monitor"])


# ==================== 请求/响应模型 ====================

class QueryRequest(BaseModel):
    """查询请求"""
    user_id: str = Field(..., description="用户ID")
    question: str = Field(..., description="用户问题")
    context: Optional[List[Dict[str, str]]] = Field(None, description="对话上下文")


class QueryResponse(BaseModel):
    """查询响应"""
    request_id: str
    requires_confirmation: bool
    risk_score: Optional[float] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    content: Optional[str] = None
    routing_info: Optional[Dict[str, Any]] = None


class ConfirmRequest(BaseModel):
    """确认请求"""
    request_id: str = Field(..., description="请求ID")
    user_id: str = Field(..., description="用户ID")
    confirmed: bool = Field(..., description="是否确认")
    feedback: Optional[str] = Field(None, description="用户反馈")


class RegisterServiceRequest(BaseModel):
    """注册服务请求"""
    service_name: str
    service_url: str
    description: str
    tools: List[Dict[str, Any]]
    layer: str = "L2"
    domain: Optional[str] = None


class ExecutionResultRequest(BaseModel):
    """执行结果请求"""
    request_id: str
    execution_success: bool
    execution_result: Optional[Dict[str, Any]] = None


# ==================== 依赖注入 ====================

def get_orchestrator():
    """获取编排器实例（将在main.py中设置）"""
    from main import orchestrator
    return orchestrator


# ==================== API端点 ====================

@router.post("/query", response_model=QueryResponse)
async def process_query(
    request: QueryRequest,
    orchestrator = Depends(get_orchestrator)
):
    """
    处理用户查询

    这是主要的API端点，处理用户问题并返回是否需要确认。

    流程：
    1. 工具路由
    2. 模型生成
    3. RAG检索
    4. 规则检查
    5. 风险评估
    6. 返回结果
    """
    try:
        # 转换上下文
        context = None
        if request.context:
            context = [Message(**msg) for msg in request.context]

        # 处理查询
        result = await orchestrator.process_query(
            user_id=request.user_id,
            user_question=request.question,
            conversation_context=context
        )

        return QueryResponse(**result)

    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/confirm")
async def confirm_tool_call(
    request: ConfirmRequest,
    orchestrator = Depends(get_orchestrator)
):
    """
    用户确认或拒绝工具调用

    Args:
        request: 确认请求

    Returns:
        确认结果
    """
    try:
        result = await orchestrator.confirm_tool_call(
            request_id=request.request_id,
            user_id=request.user_id,
            confirmed=request.confirmed,
            feedback=request.feedback
        )

        return result

    except Exception as e:
        logger.error(f"Error confirming tool call: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/execution")
async def record_execution(
    request: ExecutionResultRequest,
    orchestrator = Depends(get_orchestrator)
):
    """
    记录工具执行结果

    Args:
        request: 执行结果请求

    Returns:
        成功消息
    """
    try:
        await orchestrator.record_execution_result(
            request_id=request.request_id,
            execution_success=request.execution_success,
            execution_result=request.execution_result
        )

        return {"success": True, "message": "Execution result recorded"}

    except Exception as e:
        logger.error(f"Error recording execution: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== MCP服务管理 ====================

@router.post("/services/register")
async def register_service(
    request: RegisterServiceRequest,
    orchestrator = Depends(get_orchestrator)
):
    """
    注册新的MCP服务

    Args:
        request: 注册请求

    Returns:
        注册结果
    """
    try:
        success = await orchestrator.service_manager.register_service(
            service_name=request.service_name,
            service_url=request.service_url,
            description=request.description,
            tools=request.tools,
            layer=request.layer,
            domain=request.domain
        )

        if success:
            return {"success": True, "message": f"Service {request.service_name} registered"}
        else:
            raise HTTPException(status_code=400, detail="Failed to register service")

    except Exception as e:
        logger.error(f"Error registering service: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/services/list")
async def list_services(
    layer: Optional[str] = None,
    active_only: bool = True,
    orchestrator = Depends(get_orchestrator)
):
    """
    列出所有MCP服务

    Args:
        layer: 筛选层级（L1/L2/L3）
        active_only: 是否只返回活跃服务

    Returns:
        服务列表
    """
    try:
        services = await orchestrator.service_manager.list_services(
            layer=layer,
            active_only=active_only
        )

        return {
            "total": len(services),
            "services": services
        }

    except Exception as e:
        logger.error(f"Error listing services: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/services/{service_name}/status")
async def get_service_status(
    service_name: str,
    orchestrator = Depends(get_orchestrator)
):
    """
    获取服务状态

    Args:
        service_name: 服务名称

    Returns:
        服务状态信息
    """
    try:
        status = await orchestrator.service_manager.get_service_status(service_name)

        if status is None:
            raise HTTPException(status_code=404, detail="Service not found")

        return status

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting service status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/services/{service_name}/tools")
async def get_service_tools(
    service_name: str,
    orchestrator = Depends(get_orchestrator)
):
    """
    获取服务的所有工具

    Args:
        service_name: 服务名称

    Returns:
        工具列表
    """
    try:
        tools = await orchestrator.service_manager.get_tools_by_service(service_name)

        return {
            "service_name": service_name,
            "tool_count": len(tools),
            "tools": tools
        }

    except Exception as e:
        logger.error(f"Error getting service tools: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 历史记录 ====================

@router.get("/history/{user_id}")
async def get_user_history(
    user_id: str,
    limit: int = 50,
    tool_name: Optional[str] = None,
    orchestrator = Depends(get_orchestrator)
):
    """
    获取用户的工具调用历史

    Args:
        user_id: 用户ID
        limit: 返回记录数量
        tool_name: 筛选工具名称

    Returns:
        历史记录列表
    """
    try:
        histories = await orchestrator.db.get_user_tool_history(
            user_id=user_id,
            limit=limit,
            tool_name=tool_name
        )

        return {
            "total": len(histories),
            "histories": [
                {
                    "request_id": h.request_id,
                    "user_question": h.user_question,
                    "tool_name": h.tool_name,
                    "risk_score": h.risk_score,
                    "user_confirmed": h.user_confirmed,
                    "execution_success": h.execution_success,
                    "created_at": h.created_at.isoformat()
                }
                for h in histories
            ]
        }

    except Exception as e:
        logger.error(f"Error getting user history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 健康检查 ====================

@router.get("/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "service": "MCP Monitor"
    }
