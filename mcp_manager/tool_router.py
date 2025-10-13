"""
工具路由器 - 智能选择需要加载的工具
"""
import re
from typing import List, Dict, Any, Optional
from loguru import logger

from database import DatabaseManager


class ToolRouter:
    """工具路由器"""

    def __init__(self, db_manager: DatabaseManager, config: Dict[str, Any]):
        """
        初始化工具路由器

        Args:
            db_manager: 数据库管理器
            config: 工具分层配置
        """
        self.db = db_manager
        self.config = config.get("tool_layers", {})

        # L1核心工具（始终加载）
        self.core_tools = self.config.get("L1_core_tools", [])

        # L2领域工具
        self.domain_tools = self.config.get("L2_domain_tools", {})

        # L3高风险工具
        self.high_risk_tools = self.config.get("L3_high_risk_tools", [])

        # 意图关键词映射
        self.intent_keywords = {
            "weather": ["天气", "weather", "温度", "temperature", "forecast"],
            "email": ["邮件", "email", "发送", "send", "mail"],
            "file": ["文件", "file", "目录", "directory", "folder"],
            "database": ["数据库", "database", "查询", "query", "sql"],
            "network": ["网络", "network", "请求", "request", "api", "http"],
            "calculation": ["计算", "calculate", "数学", "math"],
        }

        logger.info("Tool router initialized")

    async def route_tools(
        self,
        user_question: str,
        user_id: Optional[str] = None,
        explicit_tools: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        根据用户问题路由需要的工具

        Args:
            user_question: 用户问题
            user_id: 用户ID
            explicit_tools: 显式指定的工具

        Returns:
            路由结果，包含工具列表和元数据
        """
        logger.debug(f"Routing tools for question: {user_question[:50]}...")

        result = {
            "core_tools": [],
            "domain_tools": [],
            "high_risk_tools": [],
            "total_tools": [],
            "detected_intents": [],
            "active_domains": []
        }

        # 1. 始终加载L1核心工具
        result["core_tools"] = await self._get_core_tools()

        # 2. 如果显式指定了工具，直接使用
        if explicit_tools:
            result["domain_tools"] = await self._get_explicit_tools(explicit_tools)
        else:
            # 3. 否则，检测意图并加载相应领域工具
            intents = self._detect_intent(user_question)
            result["detected_intents"] = intents

            for intent in intents:
                domain_tools = await self._get_domain_tools(intent)
                result["domain_tools"].extend(domain_tools)
                if domain_tools:
                    result["active_domains"].append(intent)

        # 4. 检查用户偏好（如果有用户ID）
        if user_id:
            user_tools = await self._get_user_preferred_tools(user_id)
            result["domain_tools"].extend(user_tools)

        # 5. 合并所有工具
        all_tools = result["core_tools"] + result["domain_tools"]

        # 去重
        seen_names = set()
        unique_tools = []
        for tool in all_tools:
            tool_name = tool.get("name") or tool.get("function", {}).get("name")
            if tool_name and tool_name not in seen_names:
                seen_names.add(tool_name)
                unique_tools.append(tool)

        result["total_tools"] = unique_tools

        logger.info(
            f"Tool routing complete: {len(unique_tools)} tools, "
            f"intents={result['detected_intents']}"
        )

        return result

    def _detect_intent(self, user_question: str) -> List[str]:
        """
        检测用户意图

        Args:
            user_question: 用户问题

        Returns:
            检测到的意图列表
        """
        question_lower = user_question.lower()
        detected = []

        for intent, keywords in self.intent_keywords.items():
            for keyword in keywords:
                if keyword.lower() in question_lower:
                    detected.append(intent)
                    break

        # 如果没有检测到任何意图，返回通用意图
        if not detected:
            detected.append("general")

        logger.debug(f"Detected intents: {detected}")
        return detected

    async def _get_core_tools(self) -> List[Dict[str, Any]]:
        """获取L1核心工具"""
        tools = []

        # 获取L1层的服务
        services = await self.db.get_active_services(layer="L1")

        for service in services:
            if service.tools:
                tools.extend(service.tools)

        logger.debug(f"Loaded {len(tools)} core tools")
        return tools

    async def _get_domain_tools(self, domain: str) -> List[Dict[str, Any]]:
        """
        获取特定领域的工具

        Args:
            domain: 领域名称

        Returns:
            工具列表
        """
        tools = []

        # 从L2层获取特定领域的服务
        services = await self.db.get_active_services(layer="L2")

        for service in services:
            if service.domain == domain and service.tools:
                tools.extend(service.tools)

        logger.debug(f"Loaded {len(tools)} tools for domain '{domain}'")
        return tools

    async def _get_explicit_tools(self, tool_names: List[str]) -> List[Dict[str, Any]]:
        """
        根据工具名称显式获取工具

        Args:
            tool_names: 工具名称列表

        Returns:
            工具列表
        """
        tools = []

        # 获取所有活跃服务
        services = await self.db.get_active_services()

        for service in services:
            if not service.tools:
                continue

            for tool in service.tools:
                tool_name = tool.get("name") or tool.get("function", {}).get("name")
                if tool_name in tool_names:
                    tools.append(tool)

        logger.debug(f"Loaded {len(tools)} explicit tools")
        return tools

    async def _get_user_preferred_tools(self, user_id: str) -> List[Dict[str, Any]]:
        """
        获取用户偏好的工具

        Args:
            user_id: 用户ID

        Returns:
            工具列表
        """
        # 获取用户偏好
        preference = await self.db.get_user_preference(user_id)
        if not preference or not preference.preferred_tools:
            return []

        # 获取偏好的工具
        tools = await self._get_explicit_tools(preference.preferred_tools)

        logger.debug(f"Loaded {len(tools)} user preferred tools")
        return tools

    def simplify_tool_description(self, tool: Dict[str, Any]) -> Dict[str, Any]:
        """
        精简工具描述（减少prompt长度）

        Args:
            tool: 工具定义

        Returns:
            精简后的工具定义
        """
        simplified = tool.copy()

        # 简化函数描述
        if "function" in simplified:
            func = simplified["function"]

            # 截断过长的描述
            if "description" in func and len(func["description"]) > 200:
                func["description"] = func["description"][:200] + "..."

            # 简化参数描述
            if "parameters" in func and "properties" in func["parameters"]:
                for param_name, param_def in func["parameters"]["properties"].items():
                    if "description" in param_def and len(param_def["description"]) > 100:
                        param_def["description"] = param_def["description"][:100] + "..."

        return simplified
