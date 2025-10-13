"""
模型基类定义
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, AsyncGenerator
from pydantic import BaseModel, Field


class Message(BaseModel):
    """消息模型"""
    role: str = Field(..., description="消息角色: system, user, assistant, tool")
    content: str = Field(..., description="消息内容")
    name: Optional[str] = Field(None, description="消息发送者名称")
    tool_calls: Optional[List[Dict[str, Any]]] = Field(None, description="工具调用列表")
    tool_call_id: Optional[str] = Field(None, description="工具调用ID")


class ToolDefinition(BaseModel):
    """工具定义模型"""
    type: str = Field(default="function", description="工具类型")
    function: Dict[str, Any] = Field(..., description="函数定义")


class ModelResponse(BaseModel):
    """模型响应模型"""
    content: Optional[str] = Field(None, description="响应内容")
    tool_calls: Optional[List[Dict[str, Any]]] = Field(None, description="工具调用列表")
    finish_reason: str = Field(..., description="结束原因: stop, tool_calls, length")
    usage: Optional[Dict[str, int]] = Field(None, description="token使用统计")


class BaseModel(ABC):
    """
    模型基类 - 所有模型适配器必须继承此类

    这是一个抽象基类，定义了模型必须实现的接口。
    用户需要继承此类并实现具体的模型调用逻辑。
    """

    def __init__(self, config: Dict[str, Any]):
        """
        初始化模型

        Args:
            config: 模型配置字典
        """
        self.config = config

    @abstractmethod
    async def generate(
        self,
        messages: List[Message],
        tools: Optional[List[ToolDefinition]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> ModelResponse:
        """
        生成响应（异步方法）

        Args:
            messages: 对话历史消息列表
            tools: 可用工具列表
            temperature: 温度参数，控制随机性
            max_tokens: 最大生成token数
            **kwargs: 其他模型特定参数

        Returns:
            ModelResponse: 模型响应对象

        Raises:
            NotImplementedError: 子类必须实现此方法
        """
        raise NotImplementedError("Subclass must implement generate method")

    @abstractmethod
    async def generate_stream(
        self,
        messages: List[Message],
        tools: Optional[List[ToolDefinition]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        流式生成响应（异步生成器）

        Args:
            messages: 对话历史消息列表
            tools: 可用工具列表
            temperature: 温度参数
            max_tokens: 最大生成token数
            **kwargs: 其他模型特定参数

        Yields:
            str: 生成的文本片段

        Raises:
            NotImplementedError: 子类必须实现此方法
        """
        raise NotImplementedError("Subclass must implement generate_stream method")

    @abstractmethod
    async def get_embedding(self, text: str) -> List[float]:
        """
        获取文本的向量嵌入

        Args:
            text: 输入文本

        Returns:
            List[float]: 向量嵌入

        Raises:
            NotImplementedError: 子类必须实现此方法
        """
        raise NotImplementedError("Subclass must implement get_embedding method")

    def validate_config(self) -> bool:
        """
        验证配置是否有效（可选实现）

        Returns:
            bool: 配置是否有效
        """
        return True

    async def health_check(self) -> bool:
        """
        健康检查（可选实现）

        Returns:
            bool: 模型是否健康
        """
        return True
