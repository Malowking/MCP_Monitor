"""
OpenAI兼容格式的模型适配器
支持所有兼容OpenAI API格式的模型服务
"""
from typing import List, Dict, Any, Optional, AsyncGenerator
import json
from openai import AsyncOpenAI
from loguru import logger

from models.base_model import (
    BaseModel,
    Message,
    ToolDefinition,
    ModelResponse
)


class OpenAIAdapter(BaseModel):
    """OpenAI兼容格式的模型适配器"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化OpenAI适配器

        Args:
            config: 配置字典，包含:
                - api_base: API端点
                - api_key: API密钥
                - model_name: 模型名称
                - temperature: 默认温度
                - max_tokens: 默认最大token数
        """
        super().__init__(config)

        openai_config = config.get("openai_compatible", {})

        self.api_base = openai_config.get("api_base")
        self.api_key = openai_config.get("api_key", "dummy")  # 某些本地模型不需要key
        self.model_name = openai_config.get("model_name")
        self.default_temperature = openai_config.get("temperature", 0.7)
        self.default_max_tokens = openai_config.get("max_tokens", 2000)

        # 初始化OpenAI客户端
        self.client = AsyncOpenAI(
            base_url=self.api_base,
            api_key=self.api_key
        )

        # Embedding配置
        embedding_config = config.get("embedding", {})
        self.embedding_api_base = embedding_config.get("api_base", self.api_base)
        self.embedding_api_key = embedding_config.get("api_key", self.api_key)
        self.embedding_model = embedding_config.get("model_name", "text-embedding-ada-002")

        # 初始化Embedding客户端
        self.embedding_client = AsyncOpenAI(
            base_url=self.embedding_api_base,
            api_key=self.embedding_api_key
        )

        logger.info(f"OpenAI adapter initialized: {self.api_base}, model={self.model_name}")

    def _convert_messages(self, messages: List[Message]) -> List[Dict[str, Any]]:
        """将Message对象转换为OpenAI格式"""
        result = []
        for msg in messages:
            msg_dict = {"role": msg.role, "content": msg.content}

            if msg.name:
                msg_dict["name"] = msg.name

            if msg.tool_calls:
                msg_dict["tool_calls"] = msg.tool_calls

            if msg.tool_call_id:
                msg_dict["tool_call_id"] = msg.tool_call_id

            result.append(msg_dict)

        return result

    def _convert_tools(self, tools: List[ToolDefinition]) -> List[Dict[str, Any]]:
        """将ToolDefinition对象转换为OpenAI格式"""
        return [tool.model_dump() for tool in tools]

    async def generate(
        self,
        messages: List[Message],
        tools: Optional[List[ToolDefinition]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> ModelResponse:
        """
        生成响应

        Args:
            messages: 对话历史消息列表
            tools: 可用工具列表
            temperature: 温度参数
            max_tokens: 最大生成token数
            **kwargs: 其他参数

        Returns:
            ModelResponse: 模型响应
        """
        try:
            # 转换消息格式
            openai_messages = self._convert_messages(messages)

            # 构建请求参数
            request_params = {
                "model": self.model_name,
                "messages": openai_messages,
                "temperature": temperature or self.default_temperature,
                "max_tokens": max_tokens or self.default_max_tokens,
                **kwargs
            }

            # 添加工具定义
            if tools:
                request_params["tools"] = self._convert_tools(tools)
                request_params["tool_choice"] = "auto"

            # 调用API
            logger.debug(f"Calling OpenAI API with {len(openai_messages)} messages")
            response = await self.client.chat.completions.create(**request_params)

            # 解析响应
            choice = response.choices[0]
            message = choice.message

            # 提取工具调用
            tool_calls = None
            if hasattr(message, 'tool_calls') and message.tool_calls:
                tool_calls = [
                    {
                        "id": tc.id,
                        "type": tc.type,
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    }
                    for tc in message.tool_calls
                ]

            # 构建响应
            model_response = ModelResponse(
                content=message.content,
                tool_calls=tool_calls,
                finish_reason=choice.finish_reason,
                usage={
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            )

            logger.info(
                f"Generated response: finish_reason={choice.finish_reason}, "
                f"tokens={response.usage.total_tokens}, "
                f"has_tool_calls={tool_calls is not None}"
            )

            return model_response

        except Exception as e:
            logger.error(f"Error generating response: {e}")
            raise

    async def generate_stream(
        self,
        messages: List[Message],
        tools: Optional[List[ToolDefinition]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        流式生成响应

        Args:
            messages: 对话历史消息列表
            tools: 可用工具列表
            temperature: 温度参数
            max_tokens: 最大生成token数
            **kwargs: 其他参数

        Yields:
            str: 生成的文本片段
        """
        try:
            # 转换消息格式
            openai_messages = self._convert_messages(messages)

            # 构建请求参数
            request_params = {
                "model": self.model_name,
                "messages": openai_messages,
                "temperature": temperature or self.default_temperature,
                "max_tokens": max_tokens or self.default_max_tokens,
                "stream": True,
                **kwargs
            }

            # 添加工具定义
            if tools:
                request_params["tools"] = self._convert_tools(tools)
                request_params["tool_choice"] = "auto"

            # 调用API
            logger.debug(f"Calling OpenAI API (stream) with {len(openai_messages)} messages")
            stream = await self.client.chat.completions.create(**request_params)

            # 流式返回
            async for chunk in stream:
                if chunk.choices and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    if delta.content:
                        yield delta.content

        except Exception as e:
            logger.error(f"Error in stream generation: {e}")
            raise

    async def get_embedding(self, text: str) -> List[float]:
        """
        获取文本的向量嵌入

        Args:
            text: 输入文本

        Returns:
            List[float]: 向量嵌入
        """
        try:
            logger.debug(f"Getting embedding for text (length={len(text)})")

            response = await self.embedding_client.embeddings.create(
                model=self.embedding_model,
                input=text
            )

            embedding = response.data[0].embedding
            logger.debug(f"Got embedding with dimension {len(embedding)}")

            return embedding

        except Exception as e:
            logger.error(f"Error getting embedding: {e}")
            raise

    async def health_check(self) -> bool:
        """
        健康检查

        Returns:
            bool: 模型是否健康
        """
        try:
            # 发送一个简单的请求测试连接
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": "test"}],
                max_tokens=5
            )
            logger.info("Model health check passed")
            return True
        except Exception as e:
            logger.error(f"Model health check failed: {e}")
            return False

    def validate_config(self) -> bool:
        """
        验证配置

        Returns:
            bool: 配置是否有效
        """
        if not self.api_base:
            logger.error("api_base is not configured")
            return False

        if not self.model_name:
            logger.error("model_name is not configured")
            return False

        logger.info("Configuration validated successfully")
        return True
