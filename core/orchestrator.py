"""
主流程编排器 - 整合所有组件处理用户请求
"""
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime
from loguru import logger

from database import DatabaseManager
from models.base_model import BaseModel, Message, ToolDefinition
from core import RAGRetriever, RiskAssessor, RuleEngine
from mcp_manager.service_manager import MCPServiceManager
from mcp_manager.tool_router import ToolRouter


class MCPOrchestrator:
    """MCP主流程编排器"""

    def __init__(
        self,
        db_manager: DatabaseManager,
        model: BaseModel,
        config: Dict[str, Any]
    ):
        """
        初始化编排器

        Args:
            db_manager: 数据库管理器
            model: 模型实例
            config: 完整配置
        """
        self.db = db_manager
        self.model = model
        self.config = config

        # 初始化各组件
        self.rag_retriever = RAGRetriever(db_manager, model, config)
        self.risk_assessor = RiskAssessor(config)
        self.rule_engine = RuleEngine(config)
        self.service_manager = MCPServiceManager(db_manager, config)
        self.tool_router = ToolRouter(db_manager, config)

        logger.info("MCP orchestrator initialized")

    async def start(self):
        """启动编排器"""
        await self.service_manager.start()
        logger.info("MCP orchestrator started")

    async def stop(self):
        """停止编排器"""
        await self.service_manager.stop()
        logger.info("MCP orchestrator stopped")

    async def process_query(
        self,
        user_id: str,
        user_question: str,
        conversation_context: Optional[List[Message]] = None
    ) -> Dict[str, Any]:
        """
        处理用户查询的主流程

        流程：
        1. 工具路由 - 选择相关工具
        2. 模型生成 - 生成工具调用草案
        3. RAG检索 - 检索历史反馈
        4. 规则检查 - 检查黑名单和规则
        5. 风险评估 - 综合评估风险
        6. 决策 - 是否需要用户确认
        7. 生成响应 - 包含确认提示和历史建议

        Args:
            user_id: 用户ID
            user_question: 用户问题
            conversation_context: 对话上下文

        Returns:
            处理结果字典
        """
        request_id = str(uuid.uuid4())
        logger.info(f"Processing query {request_id}: {user_question[:50]}...")

        try:
            # 1. 工具路由 - 选择相关工具
            logger.debug("Step 1: Tool routing")
            routing_result = await self.tool_router.route_tools(
                user_question=user_question,
                user_id=user_id
            )

            available_tools = routing_result["total_tools"]
            logger.info(f"Routed {len(available_tools)} tools")

            # 2. 模型生成 - 生成工具调用草案
            logger.debug("Step 2: Model generation")
            messages = conversation_context or []
            messages.append(Message(role="user", content=user_question))

            # 转换工具格式
            tool_definitions = [
                ToolDefinition(
                    type="function",
                    function=tool.get("function") or tool
                )
                for tool in available_tools
            ]

            model_response = await self.model.generate(
                messages=messages,
                tools=tool_definitions if tool_definitions else None
            )

            # 检查是否有工具调用
            if not model_response.tool_calls:
                logger.info("No tool calls in response")
                return {
                    "request_id": request_id,
                    "requires_confirmation": False,
                    "content": model_response.content,
                    "tool_calls": None
                }

            # 处理每个工具调用
            results = []
            for tool_call in model_response.tool_calls:
                result = await self._process_tool_call(
                    request_id=request_id,
                    user_id=user_id,
                    user_question=user_question,
                    tool_call=tool_call,
                    conversation_context=conversation_context
                )
                results.append(result)

            # 如果有任何一个需要确认，整体需要确认
            requires_confirmation = any(r["requires_confirmation"] for r in results)
            max_risk_score = max(r["risk_score"] for r in results)

            return {
                "request_id": request_id,
                "requires_confirmation": requires_confirmation,
                "risk_score": max_risk_score,
                "tool_calls": results,
                "content": model_response.content,
                "routing_info": {
                    "detected_intents": routing_result["detected_intents"],
                    "active_domains": routing_result["active_domains"],
                    "tool_count": len(available_tools)
                }
            }

        except Exception as e:
            logger.error(f"Error processing query {request_id}: {e}")
            raise

    async def _process_tool_call(
        self,
        request_id: str,
        user_id: str,
        user_question: str,
        tool_call: Dict[str, Any],
        conversation_context: Optional[List[Message]] = None
    ) -> Dict[str, Any]:
        """
        处理单个工具调用

        Args:
            request_id: 请求ID
            user_id: 用户ID
            user_question: 用户问题
            tool_call: 工具调用信息
            conversation_context: 对话上下文

        Returns:
            处理结果
        """
        tool_name = tool_call["function"]["name"]
        tool_parameters = eval(tool_call["function"]["arguments"])  # 解析JSON

        logger.debug(f"Processing tool call: {tool_name}")

        # 3. RAG检索 - 检索历史反馈
        logger.debug("Step 3: RAG retrieval")
        similar_cases = await self.rag_retriever.retrieve_similar_cases(
            user_question=user_question,
            user_id=user_id
        )

        historical_analysis = self.rag_retriever.analyze_historical_feedback(similar_cases)

        # 4. 规则检查 - 检查黑名单和规则
        logger.debug("Step 4: Rule checking")
        rule_result = self.rule_engine.check_tool_call(
            tool_name=tool_name,
            tool_parameters=tool_parameters
        )

        # 如果被阻止，直接返回
        if rule_result.get("blocked"):
            logger.warning(f"Tool call blocked: {tool_name}")
            return {
                "tool_call_id": tool_call["id"],
                "tool_name": tool_name,
                "tool_parameters": tool_parameters,
                "requires_confirmation": False,
                "blocked": True,
                "risk_score": 1.0,
                "messages": rule_result.get("messages", [])
            }

        # 5. 风险评估 - 综合评估风险
        logger.debug("Step 5: Risk assessment")
        risk_result = self.risk_assessor.assess_tool_risk(
            tool_name=tool_name,
            tool_parameters=tool_parameters,
            historical_analysis=historical_analysis,
            rule_result=rule_result
        )

        # 6. 决策 - 是否需要用户确认
        requires_confirmation = (
            risk_result["requires_confirmation"] or
            rule_result.get("force_confirm", False)
        )

        # 7. 生成确认消息（动态prompt注入）
        confirmation_message = self._generate_confirmation_message(
            tool_name=tool_name,
            tool_parameters=tool_parameters,
            risk_result=risk_result,
            historical_analysis=historical_analysis,
            rule_result=rule_result
        )

        # 8. 存储到数据库
        history = await self.db.create_tool_call_history(
            request_id=request_id,
            user_id=user_id,
            user_question=user_question,
            tool_name=tool_name,
            tool_parameters=tool_parameters,
            risk_score=risk_result["risk_score"],
            requires_confirmation=requires_confirmation,
            matched_rules=[r.get("rule_id") for r in rule_result.get("matched_rules", [])],
            blacklist_hit=rule_result.get("blacklist_hit", False),
            confirmation_reason=confirmation_message,
            conversation_context=[m.model_dump() for m in conversation_context] if conversation_context else None,
            similar_history_ids=[c["history"].id for c in similar_cases]
        )

        # 9. 存储问题embedding
        vector_id = await self.rag_retriever.store_question_embedding(
            user_question=user_question,
            database_id=history.id
        )

        return {
            "tool_call_id": tool_call["id"],
            "tool_name": tool_name,
            "tool_parameters": tool_parameters,
            "requires_confirmation": requires_confirmation,
            "blocked": False,
            "risk_score": risk_result["risk_score"],
            "risk_level": risk_result["risk_level"],
            "confirmation_message": confirmation_message,
            "risk_reasons": risk_result["reasons"],
            "historical_insights": historical_analysis.get("common_patterns", []),
            "similar_case_count": len(similar_cases)
        }

    def _generate_confirmation_message(
        self,
        tool_name: str,
        tool_parameters: Dict[str, Any],
        risk_result: Dict[str, Any],
        historical_analysis: Dict[str, Any],
        rule_result: Dict[str, Any]
    ) -> str:
        """
        生成确认消息（动态prompt注入）

        Args:
            tool_name: 工具名称
            tool_parameters: 工具参数
            risk_result: 风险评估结果
            historical_analysis: 历史分析
            rule_result: 规则检查结果

        Returns:
            确认消息
        """
        message_parts = []

        # 基础信息
        message_parts.append(f"准备调用工具: {tool_name}")

        # 参数信息
        param_str = ", ".join(f"{k}={v}" for k, v in tool_parameters.items())
        message_parts.append(f"参数: {param_str}")

        # 风险等级
        risk_level = risk_result["risk_level"]
        risk_emoji = {"low": "🟢", "medium": "🟡", "high": "🔴"}.get(risk_level, "⚪")
        message_parts.append(f"风险等级: {risk_emoji} {risk_level.upper()}")

        # 风险原因
        if risk_result.get("reasons"):
            message_parts.append("风险分析:")
            for reason in risk_result["reasons"]:
                message_parts.append(f"  - {reason}")

        # 历史反馈（动态prompt注入）
        if historical_analysis.get("has_history"):
            message_parts.append(f"\n根据您过去的使用记录:")

            if historical_analysis.get("common_patterns"):
                for pattern in historical_analysis["common_patterns"]:
                    message_parts.append(f"  - {pattern}")

            if historical_analysis.get("user_preferences"):
                for pref in historical_analysis["user_preferences"]:
                    message_parts.append(f"  - {pref}")

        # 规则提示
        if rule_result.get("matched_rules"):
            message_parts.append("\n触发的安全规则:")
            for rule in rule_result["matched_rules"][:2]:
                message_parts.append(f"  - {rule.get('name', 'Unknown')}")

        message_parts.append("\n是否确认执行此操作？")

        return "\n".join(message_parts)

    async def confirm_tool_call(
        self,
        request_id: str,
        user_id: str,
        confirmed: bool,
        feedback: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        用户确认工具调用

        Args:
            request_id: 请求ID
            user_id: 用户ID
            confirmed: 是否确认
            feedback: 用户反馈

        Returns:
            确认结果
        """
        logger.info(f"Tool call {request_id} confirmed: {confirmed}")

        # 更新数据库
        success = await self.db.update_tool_call_confirmation(
            request_id=request_id,
            user_confirmed=confirmed,
            user_feedback=feedback
        )

        if not success:
            logger.error(f"Failed to update confirmation for {request_id}")
            return {"success": False, "message": "Request not found"}

        if confirmed:
            return {
                "success": True,
                "message": "工具调用已确认，可以执行",
                "action": "execute"
            }
        else:
            return {
                "success": True,
                "message": "工具调用已取消",
                "action": "cancel"
            }

    async def record_execution_result(
        self,
        request_id: str,
        execution_success: bool,
        execution_result: Optional[Dict] = None
    ):
        """
        记录工具执行结果

        Args:
            request_id: 请求ID
            execution_success: 执行是否成功
            execution_result: 执行结果
        """
        await self.db.update_tool_call_execution(
            request_id=request_id,
            execution_success=execution_success,
            execution_result=execution_result
        )

        logger.info(f"Recorded execution result for {request_id}: {execution_success}")
