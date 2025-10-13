"""
PostgreSQL数据库连接和操作
"""
import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime
from contextlib import asynccontextmanager

from sqlalchemy import create_engine, select, update, delete
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker
from loguru import logger

from database.models import Base, ToolCallHistory, MCPService, ToolCallMetrics, UserPreference


class PostgreSQLManager:
    """PostgreSQL数据库管理器"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化PostgreSQL连接

        Args:
            config: 数据库配置字典
        """
        self.config = config
        pg_config = config.get("postgresql", {})

        # 构建连接URL
        self.db_url = (
            f"postgresql+asyncpg://{pg_config['user']}:{pg_config['password']}"
            f"@{pg_config['host']}:{pg_config['port']}/{pg_config['database']}"
        )

        # 创建异步引擎
        self.engine = create_async_engine(
            self.db_url,
            pool_size=pg_config.get("pool_size", 10),
            max_overflow=pg_config.get("max_overflow", 20),
            echo=False
        )

        # 创建会话工厂
        self.async_session_maker = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )

        logger.info(f"PostgreSQL manager initialized: {pg_config['host']}:{pg_config['port']}/{pg_config['database']}")

    async def init_database(self):
        """初始化数据库表"""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created successfully")

    @asynccontextmanager
    async def get_session(self):
        """获取数据库会话的上下文管理器"""
        async with self.async_session_maker() as session:
            try:
                yield session
                await session.commit()
            except Exception as e:
                await session.rollback()
                logger.error(f"Database session error: {e}")
                raise

    # ==================== ToolCallHistory操作 ====================

    async def create_tool_call_history(
        self,
        request_id: str,
        user_id: str,
        user_question: str,
        tool_name: str,
        tool_parameters: Dict,
        risk_score: float,
        requires_confirmation: bool,
        **kwargs
    ) -> ToolCallHistory:
        """创建工具调用历史记录"""
        async with self.get_session() as session:
            history = ToolCallHistory(
                request_id=request_id,
                user_id=user_id,
                user_question=user_question,
                tool_name=tool_name,
                tool_parameters=tool_parameters,
                risk_score=risk_score,
                requires_confirmation=requires_confirmation,
                **kwargs
            )
            session.add(history)
            await session.flush()
            await session.refresh(history)
            logger.info(f"Created tool call history: {request_id}")
            return history

    async def update_tool_call_confirmation(
        self,
        request_id: str,
        user_confirmed: bool,
        user_feedback: Optional[str] = None
    ) -> bool:
        """更新工具调用确认状态"""
        async with self.get_session() as session:
            stmt = (
                update(ToolCallHistory)
                .where(ToolCallHistory.request_id == request_id)
                .values(
                    user_confirmed=user_confirmed,
                    user_feedback=user_feedback,
                    confirmed_at=datetime.utcnow()
                )
            )
            result = await session.execute(stmt)
            logger.info(f"Updated confirmation for {request_id}: {user_confirmed}")
            return result.rowcount > 0

    async def update_tool_call_execution(
        self,
        request_id: str,
        execution_success: bool,
        execution_result: Optional[Dict] = None
    ) -> bool:
        """更新工具调用执行结果"""
        async with self.get_session() as session:
            stmt = (
                update(ToolCallHistory)
                .where(ToolCallHistory.request_id == request_id)
                .values(
                    execution_success=execution_success,
                    execution_result=execution_result,
                    executed_at=datetime.utcnow()
                )
            )
            result = await session.execute(stmt)
            logger.info(f"Updated execution for {request_id}: {execution_success}")
            return result.rowcount > 0

    async def get_tool_call_history(self, request_id: str) -> Optional[ToolCallHistory]:
        """根据request_id获取工具调用历史"""
        async with self.get_session() as session:
            stmt = select(ToolCallHistory).where(ToolCallHistory.request_id == request_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def get_user_tool_history(
        self,
        user_id: str,
        limit: int = 100,
        tool_name: Optional[str] = None
    ) -> List[ToolCallHistory]:
        """获取用户的工具调用历史"""
        async with self.get_session() as session:
            stmt = select(ToolCallHistory).where(ToolCallHistory.user_id == user_id)
            if tool_name:
                stmt = stmt.where(ToolCallHistory.tool_name == tool_name)
            stmt = stmt.order_by(ToolCallHistory.created_at.desc()).limit(limit)
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def get_history_by_ids(self, history_ids: List[int]) -> List[ToolCallHistory]:
        """根据ID列表批量获取历史记录"""
        async with self.get_session() as session:
            stmt = select(ToolCallHistory).where(ToolCallHistory.id.in_(history_ids))
            result = await session.execute(stmt)
            return list(result.scalars().all())

    # ==================== MCPService操作 ====================

    async def register_mcp_service(
        self,
        service_name: str,
        service_url: str,
        description: str,
        tools: List[Dict],
        layer: str,
        domain: Optional[str] = None
    ) -> MCPService:
        """注册MCP服务"""
        async with self.get_session() as session:
            service = MCPService(
                service_name=service_name,
                service_url=service_url,
                description=description,
                tools=tools,
                layer=layer,
                domain=domain
            )
            session.add(service)
            await session.flush()
            await session.refresh(service)
            logger.info(f"Registered MCP service: {service_name}")
            return service

    async def get_mcp_service(self, service_name: str) -> Optional[MCPService]:
        """获取MCP服务"""
        async with self.get_session() as session:
            stmt = select(MCPService).where(MCPService.service_name == service_name)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def get_active_services(self, layer: Optional[str] = None) -> List[MCPService]:
        """获取活跃的MCP服务"""
        async with self.get_session() as session:
            stmt = select(MCPService).where(MCPService.is_active == True)
            if layer:
                stmt = stmt.where(MCPService.layer == layer)
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def update_service_health(
        self,
        service_name: str,
        health_status: str,
        circuit_breaker_state: Optional[str] = None
    ) -> bool:
        """更新服务健康状态"""
        async with self.get_session() as session:
            values = {
                "health_status": health_status,
                "last_health_check": datetime.utcnow()
            }
            if circuit_breaker_state:
                values["circuit_breaker_state"] = circuit_breaker_state
                if circuit_breaker_state == "open":
                    values["circuit_breaker_opened_at"] = datetime.utcnow()

            stmt = (
                update(MCPService)
                .where(MCPService.service_name == service_name)
                .values(**values)
            )
            result = await session.execute(stmt)
            return result.rowcount > 0

    async def update_service_metrics(
        self,
        service_name: str,
        success: bool,
        latency_ms: float
    ) -> bool:
        """更新服务调用指标"""
        async with self.get_session() as session:
            # 先获取当前服务
            service = await self.get_mcp_service(service_name)
            if not service:
                return False

            # 更新统计
            total_calls = service.total_calls + 1
            success_calls = service.success_calls + (1 if success else 0)
            failed_calls = service.failed_calls + (0 if success else 1)

            # 计算平均延迟
            avg_latency = (service.avg_latency_ms * service.total_calls + latency_ms) / total_calls

            stmt = (
                update(MCPService)
                .where(MCPService.service_name == service_name)
                .values(
                    total_calls=total_calls,
                    success_calls=success_calls,
                    failed_calls=failed_calls,
                    avg_latency_ms=avg_latency
                )
            )
            result = await session.execute(stmt)
            return result.rowcount > 0

    # ==================== UserPreference操作 ====================

    async def get_user_preference(self, user_id: str) -> Optional[UserPreference]:
        """获取用户偏好"""
        async with self.get_session() as session:
            stmt = select(UserPreference).where(UserPreference.user_id == user_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def create_or_update_user_preference(
        self,
        user_id: str,
        **kwargs
    ) -> UserPreference:
        """创建或更新用户偏好"""
        async with self.get_session() as session:
            pref = await self.get_user_preference(user_id)
            if pref:
                # 更新
                for key, value in kwargs.items():
                    if hasattr(pref, key):
                        setattr(pref, key, value)
                pref.updated_at = datetime.utcnow()
            else:
                # 创建
                pref = UserPreference(user_id=user_id, **kwargs)
                session.add(pref)

            await session.flush()
            await session.refresh(pref)
            logger.info(f"Updated user preference: {user_id}")
            return pref

    # ==================== ToolCallMetrics操作 ====================

    async def record_tool_call_metric(
        self,
        tool_name: str,
        request_id: str,
        user_id: str,
        latency_ms: float,
        success: bool,
        error_message: Optional[str] = None,
        service_id: Optional[int] = None
    ):
        """记录工具调用指标"""
        async with self.get_session() as session:
            metric = ToolCallMetrics(
                tool_name=tool_name,
                service_id=service_id,
                request_id=request_id,
                user_id=user_id,
                latency_ms=latency_ms,
                success=success,
                error_message=error_message
            )
            session.add(metric)
            logger.debug(f"Recorded metric for {tool_name}: {latency_ms}ms, success={success}")

    async def close(self):
        """关闭数据库连接"""
        await self.engine.dispose()
        logger.info("PostgreSQL connection closed")
