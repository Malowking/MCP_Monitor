"""
规则引擎 - 基于规则检查工具调用
"""
import json
import re
from typing import Dict, Any, List, Optional
from loguru import logger


class RuleEngine:
    """规则引擎"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化规则引擎

        Args:
            config: 规则引擎配置
        """
        self.config = config.get("rule_engine", {})

        self.blacklist_file = self.config.get("blacklist_file")
        self.rules_file = self.config.get("rules_file")

        # 加载规则
        self.blacklist = self._load_blacklist()
        self.rules = self._load_rules()

        logger.info(
            f"Rule engine initialized: {len(self.blacklist.get('blocked_tools', []))} blacklist items, "
            f"{len(self.rules)} rules"
        )

    def _load_blacklist(self) -> Dict[str, Any]:
        """加载黑名单配置"""
        try:
            with open(self.blacklist_file, 'r', encoding='utf-8') as f:
                blacklist = json.load(f)
            logger.info(f"Loaded blacklist from {self.blacklist_file}")
            return blacklist
        except Exception as e:
            logger.error(f"Failed to load blacklist: {e}")
            return {"blocked_tools": [], "blocked_parameters": []}

    def _load_rules(self) -> List[Dict[str, Any]]:
        """加载规则配置"""
        try:
            with open(self.rules_file, 'r', encoding='utf-8') as f:
                rules_data = json.load(f)
            rules = rules_data.get("rules", [])
            logger.info(f"Loaded {len(rules)} rules from {self.rules_file}")
            return rules
        except Exception as e:
            logger.error(f"Failed to load rules: {e}")
            return []

    def check_tool_call(
        self,
        tool_name: str,
        tool_parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        检查工具调用是否符合规则

        Args:
            tool_name: 工具名称
            tool_parameters: 工具参数

        Returns:
            检查结果字典
        """
        logger.debug(f"Checking rules for tool: {tool_name}")

        result = {
            "blacklist_hit": False,
            "matched_rules": [],
            "blocked": False,
            "force_confirm": False,
            "messages": []
        }

        # 1. 检查黑名单
        blacklist_check = self._check_blacklist(tool_name, tool_parameters)
        if blacklist_check["blocked"]:
            result["blacklist_hit"] = True
            result["blocked"] = True
            result["messages"].extend(blacklist_check["messages"])
            logger.warning(f"Tool {tool_name} hit blacklist")
            return result

        # 2. 检查规则
        for rule in self.rules:
            if self._match_rule(rule, tool_name, tool_parameters):
                result["matched_rules"].append(rule)

                # 处理规则动作
                action = rule.get("action", "log")
                if action == "force_confirm":
                    result["force_confirm"] = True
                elif action == "block":
                    result["blocked"] = True

                message = f"匹配规则: {rule.get('name', rule.get('rule_id'))}"
                result["messages"].append(message)

                logger.info(f"Matched rule {rule.get('rule_id')}: {rule.get('name')}")

        if result["matched_rules"]:
            logger.info(f"Tool {tool_name} matched {len(result['matched_rules'])} rules")

        return result

    def _check_blacklist(
        self,
        tool_name: str,
        tool_parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """检查黑名单"""
        result = {
            "blocked": False,
            "messages": []
        }

        # 检查工具黑名单
        for blocked_tool in self.blacklist.get("blocked_tools", []):
            tool_name_pattern = blocked_tool.get("tool_name", "")
            if tool_name == tool_name_pattern or re.search(tool_name_pattern, tool_name):
                result["blocked"] = True
                reason = blocked_tool.get("reason", "此工具已被禁用")
                result["messages"].append(f"黑名单拦截: {reason}")
                break

        # 检查参数黑名单
        for blocked_param in self.blacklist.get("blocked_parameters", []):
            pattern = blocked_param.get("pattern", "")
            case_sensitive = blocked_param.get("case_sensitive", False)

            # 检查所有参数
            for param_name, param_value in tool_parameters.items():
                param_str = f"{param_name}={param_value}"

                # 编译正则表达式
                flags = 0 if case_sensitive else re.IGNORECASE
                if re.search(pattern, param_str, flags):
                    result["blocked"] = True
                    reason = blocked_param.get("reason", "参数包含敏感信息")
                    result["messages"].append(f"参数拦截: {reason}")
                    break

            if result["blocked"]:
                break

        return result

    def _match_rule(
        self,
        rule: Dict[str, Any],
        tool_name: str,
        tool_parameters: Dict[str, Any]
    ) -> bool:
        """
        判断工具调用是否匹配规则

        Args:
            rule: 规则定义
            tool_name: 工具名称
            tool_parameters: 工具参数

        Returns:
            是否匹配
        """
        condition = rule.get("condition", {})

        # 1. 检查工具名称模式
        tool_name_pattern = condition.get("tool_name_pattern")
        if tool_name_pattern:
            if not re.search(tool_name_pattern, tool_name, re.IGNORECASE):
                return False

        # 2. 检查参数条件
        parameter_check = condition.get("parameter_check", {})
        if parameter_check:
            for param_name, param_pattern in parameter_check.items():
                if param_name not in tool_parameters:
                    return False

                param_value = str(tool_parameters[param_name])
                if not re.search(param_pattern, param_value, re.IGNORECASE):
                    return False

        return True

    def reload_rules(self):
        """重新加载规则（热更新）"""
        logger.info("Reloading rules...")
        self.blacklist = self._load_blacklist()
        self.rules = self._load_rules()
        logger.info("Rules reloaded successfully")

    def add_custom_rule(self, rule: Dict[str, Any]) -> bool:
        """
        动态添加自定义规则

        Args:
            rule: 规则定义

        Returns:
            是否添加成功
        """
        try:
            # 验证规则格式
            if "rule_id" not in rule or "condition" not in rule:
                logger.error("Invalid rule format")
                return False

            # 检查是否已存在
            existing_ids = [r.get("rule_id") for r in self.rules]
            if rule["rule_id"] in existing_ids:
                logger.warning(f"Rule {rule['rule_id']} already exists")
                return False

            # 添加规则
            self.rules.append(rule)
            logger.info(f"Added custom rule: {rule['rule_id']}")
            return True

        except Exception as e:
            logger.error(f"Failed to add custom rule: {e}")
            return False

    def remove_rule(self, rule_id: str) -> bool:
        """
        移除规则

        Args:
            rule_id: 规则ID

        Returns:
            是否移除成功
        """
        initial_count = len(self.rules)
        self.rules = [r for r in self.rules if r.get("rule_id") != rule_id]

        if len(self.rules) < initial_count:
            logger.info(f"Removed rule: {rule_id}")
            return True
        else:
            logger.warning(f"Rule {rule_id} not found")
            return False

    def get_all_rules(self) -> List[Dict[str, Any]]:
        """获取所有规则"""
        return self.rules.copy()

    def get_rule_by_id(self, rule_id: str) -> Optional[Dict[str, Any]]:
        """根据ID获取规则"""
        for rule in self.rules:
            if rule.get("rule_id") == rule_id:
                return rule.copy()
        return None
