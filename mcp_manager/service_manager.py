"""
MCP服务管理器 - 管理多个MCP服务的生命周期
"""
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from loguru import logger

from database import DatabaseManager


class MCPServiceManager:
    """MCP服务管理器"""

    def __init__(self, db_manager: DatabaseManager, config: Dict[str, Any]):
        """
        初始化MCP服务管理器

        Args:
            db_manager: 数据库管理器
            config: MCP服务配置
        """
        self.db = db_manager
        self.config = config.get("mcp_services", {})

        self.max_services = self.config.get("max_services", 50)
        self.health_check_interval = self.config.get("health_check_interval", 30)
        self.timeout = self.config.get("timeout", 10)

        # 熔断配置
        circuit_config = self.config.get("circuit_breaker", {})
        self.failure_threshold = circuit_config.get("failure_threshold", 5)
        self.timeout_duration = circuit_config.get("timeout_duration", 60)

        # 服务实例缓存 {service_name: service_instance}
        self.service_instances = {}

        # 后台任务
        self.health_check_task = None

        logger.info(f"MCP service manager initialized: max_services={self.max_services}")

    async def start(self):
        """启动服务管理器"""
        # 加载已注册的服务
        await self._load_registered_services()

        # 启动健康检查任务
        self.health_check_task = asyncio.create_task(self._health_check_loop())

        logger.info("MCP service manager started")

    async def stop(self):
        """停止服务管理器"""
        if self.health_check_task:
            self.health_check_task.cancel()
            try:
                await self.health_check_task
            except asyncio.CancelledError:
                pass

        logger.info("MCP service manager stopped")

    async def register_service(
        self,
        service_name: str,
        service_url: str,
        description: str,
        tools: List[Dict],
        layer: str = "L2",
        domain: Optional[str] = None
    ) -> bool:
        """
        注册MCP服务

        Args:
            service_name: 服务名称
            service_url: 服务URL
            description: 服务描述
            tools: 工具列表
            layer: 工具层级
            domain: 所属领域

        Returns:
            是否注册成功
        """
        try:
            # 检查服务数量限制
            active_services = await self.db.get_active_services()
            if len(active_services) >= self.max_services:
                logger.warning(f"Cannot register service: max limit {self.max_services} reached")
                return False

            # 注册到数据库
            await self.db.register_mcp_service(
                service_name=service_name,
                service_url=service_url,
                description=description,
                tools=tools,
                layer=layer,
                domain=domain
            )

            logger.info(f"Registered MCP service: {service_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to register service {service_name}: {e}")
            return False

    async def get_service_status(self, service_name: str) -> Optional[Dict[str, Any]]:
        """
        获取服务状态

        Args:
            service_name: 服务名称

        Returns:
            服务状态信息
        """
        service = await self.db.get_mcp_service(service_name)
        if not service:
            return None

        return {
            "service_name": service.service_name,
            "is_active": service.is_active,
            "health_status": service.health_status,
            "circuit_breaker_state": service.circuit_breaker_state,
            "layer": service.layer,
            "domain": service.domain,
            "tools": service.tools,
            "metrics": {
                "total_calls": service.total_calls,
                "success_calls": service.success_calls,
                "failed_calls": service.failed_calls,
                "success_rate": (
                    service.success_calls / service.total_calls * 100
                    if service.total_calls > 0 else 0
                ),
                "avg_latency_ms": service.avg_latency_ms
            },
            "last_health_check": service.last_health_check
        }

    async def list_services(
        self,
        layer: Optional[str] = None,
        active_only: bool = True
    ) -> List[Dict[str, Any]]:
        """
        列出所有服务

        Args:
            layer: 筛选层级
            active_only: 是否只返回活跃服务

        Returns:
            服务列表
        """
        if active_only:
            services = await self.db.get_active_services(layer=layer)
        else:
            # 这里需要数据库添加方法获取所有服务
            services = await self.db.get_active_services(layer=layer)

        result = []
        for service in services:
            result.append({
                "service_name": service.service_name,
                "description": service.description,
                "layer": service.layer,
                "domain": service.domain,
                "is_active": service.is_active,
                "health_status": service.health_status,
                "circuit_breaker_state": service.circuit_breaker_state,
                "tool_count": len(service.tools) if service.tools else 0,
                "tools": service.tools
            })

        return result

    async def get_tools_by_service(self, service_name: str) -> List[Dict[str, Any]]:
        """
        获取服务的所有工具

        Args:
            service_name: 服务名称

        Returns:
            工具列表
        """
        service = await self.db.get_mcp_service(service_name)
        if not service:
            return []

        return service.tools or []

    async def check_service_health(self, service_name: str) -> bool:
        """
        检查服务健康状态

        Args:
            service_name: 服务名称

        Returns:
            是否健康
        """
        try:
            # 这里应该实际调用MCP服务的健康检查接口
            # 简化实现，实际项目中需要HTTP请求
            service = await self.db.get_mcp_service(service_name)
            if not service:
                return False

            # 模拟健康检查
            # 实际实现: response = await http_client.get(f"{service.service_url}/health")
            is_healthy = True

            # 更新健康状态
            health_status = "healthy" if is_healthy else "down"
            await self.db.update_service_health(service_name, health_status)

            return is_healthy

        except Exception as e:
            logger.error(f"Health check failed for {service_name}: {e}")
            await self.db.update_service_health(service_name, "down")
            return False

    async def update_circuit_breaker(
        self,
        service_name: str,
        success: bool
    ):
        """
        更新熔断器状态

        Args:
            service_name: 服务名称
            success: 调用是否成功
        """
        service = await self.db.get_mcp_service(service_name)
        if not service:
            return

        current_state = service.circuit_breaker_state

        if current_state == "closed":
            if not success:
                # 检查失败次数
                recent_failures = service.failed_calls
                if recent_failures >= self.failure_threshold:
                    # 打开熔断器
                    await self.db.update_service_health(
                        service_name,
                        service.health_status,
                        circuit_breaker_state="open"
                    )
                    logger.warning(f"Circuit breaker opened for {service_name}")

        elif current_state == "open":
            # 检查是否可以进入半开状态
            if service.circuit_breaker_opened_at:
                elapsed = (datetime.utcnow() - service.circuit_breaker_opened_at).total_seconds()
                if elapsed >= self.timeout_duration:
                    await self.db.update_service_health(
                        service_name,
                        service.health_status,
                        circuit_breaker_state="half_open"
                    )
                    logger.info(f"Circuit breaker half-opened for {service_name}")

        elif current_state == "half_open":
            if success:
                # 恢复
                await self.db.update_service_health(
                    service_name,
                    "healthy",
                    circuit_breaker_state="closed"
                )
                logger.info(f"Circuit breaker closed for {service_name}")
            else:
                # 重新打开
                await self.db.update_service_health(
                    service_name,
                    "degraded",
                    circuit_breaker_state="open"
                )
                logger.warning(f"Circuit breaker re-opened for {service_name}")

    async def _health_check_loop(self):
        """后台健康检查循环"""
        logger.info("Health check loop started")

        while True:
            try:
                await asyncio.sleep(self.health_check_interval)

                # 获取所有活跃服务
                services = await self.db.get_active_services()

                # 并发检查所有服务
                tasks = [
                    self.check_service_health(service.service_name)
                    for service in services
                ]

                if tasks:
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    healthy_count = sum(1 for r in results if r is True)
                    logger.debug(
                        f"Health check completed: {healthy_count}/{len(services)} services healthy"
                    )

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in health check loop: {e}")

        logger.info("Health check loop stopped")

    async def _load_registered_services(self):
        """加载已注册的服务"""
        services = await self.db.get_active_services()
        logger.info(f"Loaded {len(services)} registered services")
