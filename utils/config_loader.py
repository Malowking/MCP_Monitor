"""
配置加载工具
"""
import yaml
from typing import Dict, Any
from pathlib import Path
from loguru import logger


def load_config(config_path: str = "config/config.yaml") -> Dict[str, Any]:
    """
    加载配置文件

    Args:
        config_path: 配置文件路径

    Returns:
        配置字典
    """
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        logger.info(f"Loaded configuration from {config_path}")
        return config
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        raise


def validate_config(config: Dict[str, Any]) -> bool:
    """
    验证配置有效性

    Args:
        config: 配置字典

    Returns:
        是否有效
    """
    required_keys = ["database", "model", "risk_assessment"]

    for key in required_keys:
        if key not in config:
            logger.error(f"Missing required config key: {key}")
            return False

    return True
