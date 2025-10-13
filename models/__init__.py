"""
模型模块初始化
"""
from models.base_model import BaseModel, Message, ToolDefinition, ModelResponse
from models.openai_adapter import OpenAIAdapter

__all__ = [
    "BaseModel",
    "Message",
    "ToolDefinition",
    "ModelResponse",
    "OpenAIAdapter"
]
