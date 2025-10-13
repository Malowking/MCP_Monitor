"""
风险评估引擎 - 综合评估工具调用的风险
"""
from typing import Dict, Any, List, Optional
from loguru import logger


class RiskAssessor:
    """风险评估器"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化风险评估器

        Args:
            config: 风险评估配置
        """
        self.config = config.get("risk_assessment", {})

        self.confirmation_threshold = self.config.get("confirmation_threshold", 0.6)
        self.high_risk_threshold = self.config.get("high_risk_threshold", 0.8)

        # 工具风险等级映射
        self.tool_risk_levels = {
            # 高风险操作
            "delete": 0.9,
            "remove": 0.9,
            "drop": 0.95,
            "truncate": 0.95,
            "format": 1.0,
            "execute": 0.85,
            "exec": 0.85,
            "eval": 0.85,
            "payment": 0.9,
            "transfer": 0.9,

            # 中风险操作
            "update": 0.6,
            "modify": 0.6,
            "write": 0.5,
            "insert": 0.5,
            "send": 0.5,
            "post": 0.5,

            # 低风险操作
            "read": 0.1,
            "get": 0.1,
            "list": 0.1,
            "search": 0.1,
            "query": 0.2,
        }

        logger.info(
            f"Risk assessor initialized: confirmation_threshold={self.confirmation_threshold}"
        )

    def assess_tool_risk(
        self,
        tool_name: str,
        tool_parameters: Dict[str, Any],
        historical_analysis: Optional[Dict[str, Any]] = None,
        rule_result: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        综合评估工具调用风险

        Args:
            tool_name: 工具名称
            tool_parameters: 工具参数
            historical_analysis: 历史分析结果
            rule_result: 规则引擎检查结果

        Returns:
            风险评估结果字典
        """
        logger.debug(f"Assessing risk for tool: {tool_name}")

        # 1. 基础风险分数（基于工具名称）
        base_score = self._calculate_base_risk(tool_name)

        # 2. 参数风险分数
        param_score = self._calculate_parameter_risk(tool_parameters)

        # 3. 历史风险分数
        history_score = self._calculate_historical_risk(historical_analysis)

        # 4. 规则引擎风险分数
        rule_score = self._calculate_rule_risk(rule_result)

        # 5. 综合计算（加权平均）
        weights = {
            "base": 0.3,
            "param": 0.2,
            "history": 0.3,
            "rule": 0.2
        }

        final_score = (
            base_score * weights["base"] +
            param_score * weights["param"] +
            history_score * weights["history"] +
            rule_score * weights["rule"]
        )

        # 确保分数在0-1之间
        final_score = max(0.0, min(1.0, final_score))

        # 判断是否需要确认
        requires_confirmation = final_score >= self.confirmation_threshold

        # 风险等级
        if final_score >= self.high_risk_threshold:
            risk_level = "high"
        elif final_score >= self.confirmation_threshold:
            risk_level = "medium"
        else:
            risk_level = "low"

        # 生成风险原因说明
        reasons = self._generate_risk_reasons(
            base_score, param_score, history_score, rule_score,
            historical_analysis, rule_result
        )

        result = {
            "risk_score": final_score,
            "risk_level": risk_level,
            "requires_confirmation": requires_confirmation,
            "breakdown": {
                "base_risk": base_score,
                "parameter_risk": param_score,
                "historical_risk": history_score,
                "rule_risk": rule_score
            },
            "reasons": reasons
        }

        logger.info(
            f"Risk assessment: score={final_score:.2f}, level={risk_level}, "
            f"confirmation={requires_confirmation}"
        )

        return result

    def _calculate_base_risk(self, tool_name: str) -> float:
        """计算基础风险分数（基于工具名称）"""
        tool_name_lower = tool_name.lower()

        # 检查是否包含高风险关键词
        for keyword, risk in self.tool_risk_levels.items():
            if keyword in tool_name_lower:
                return risk

        # 默认中等风险
        return 0.3

    def _calculate_parameter_risk(self, parameters: Dict[str, Any]) -> float:
        """计算参数风险分数"""
        if not parameters:
            return 0.0

        risk_score = 0.0
        risk_indicators = 0

        # 检查敏感参数
        sensitive_patterns = [
            "password", "secret", "token", "key", "credential",
            "root", "admin", "system", "sudo",
            "*", "all", "recursive", "force"
        ]

        for key, value in parameters.items():
            key_lower = str(key).lower()
            value_str = str(value).lower() if value is not None else ""

            # 检查参数名和值
            for pattern in sensitive_patterns:
                if pattern in key_lower or pattern in value_str:
                    risk_indicators += 1
                    risk_score += 0.3
                    break

        # 归一化
        if risk_indicators > 0:
            risk_score = min(risk_score, 1.0)

        return risk_score

    def _calculate_historical_risk(
        self,
        historical_analysis: Optional[Dict[str, Any]]
    ) -> float:
        """计算历史风险分数"""
        if not historical_analysis or not historical_analysis.get("has_history"):
            return 0.3  # 没有历史数据，默认中等风险

        risk_indication = historical_analysis.get("risk_indication", "unknown")

        risk_mapping = {
            "low": 0.2,
            "medium": 0.5,
            "high": 0.8,
            "unknown": 0.3
        }

        return risk_mapping.get(risk_indication, 0.3)

    def _calculate_rule_risk(
        self,
        rule_result: Optional[Dict[str, Any]]
    ) -> float:
        """计算规则引擎风险分数"""
        if not rule_result:
            return 0.0

        # 如果命中黑名单，直接高风险
        if rule_result.get("blacklist_hit"):
            return 1.0

        # 根据匹配的规则计算风险
        matched_rules = rule_result.get("matched_rules", [])
        if not matched_rules:
            return 0.0

        # 取最高风险规则的分数
        max_risk = max(
            (rule.get("risk_score", 0.5) for rule in matched_rules),
            default=0.0
        )

        return max_risk

    def _generate_risk_reasons(
        self,
        base_score: float,
        param_score: float,
        history_score: float,
        rule_score: float,
        historical_analysis: Optional[Dict[str, Any]],
        rule_result: Optional[Dict[str, Any]]
    ) -> List[str]:
        """生成风险原因说明"""
        reasons = []

        # 基础风险
        if base_score > 0.7:
            reasons.append("该工具属于高风险操作类型")
        elif base_score > 0.5:
            reasons.append("该工具可能涉及数据修改")

        # 参数风险
        if param_score > 0.5:
            reasons.append("工具参数包含敏感信息或危险选项")

        # 历史风险
        if historical_analysis and historical_analysis.get("has_history"):
            if history_score > 0.7:
                reasons.append("历史记录显示类似操作风险较高")

            patterns = historical_analysis.get("common_patterns", [])
            reasons.extend(patterns[:2])  # 最多添加2个历史模式

        # 规则风险
        if rule_result:
            if rule_result.get("blacklist_hit"):
                reasons.append("该操作命中黑名单规则，禁止执行")

            matched_rules = rule_result.get("matched_rules", [])
            for rule in matched_rules[:2]:  # 最多添加2个规则
                reasons.append(f"触发安全规则: {rule.get('name', 'Unknown')}")

        if not reasons:
            reasons.append("综合评估显示此操作需要谨慎处理")

        return reasons
