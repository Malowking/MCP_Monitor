"""
数据库模型定义
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class ToolCallHistory(Base):
    """工具调用历史记录"""
    __tablename__ = "tool_call_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    request_id = Column(String(64), unique=True, index=True, nullable=False)
    user_id = Column(String(128), index=True, nullable=False)

    # 用户问题
    user_question = Column(Text, nullable=False)
    user_question_embedding_id = Column(Integer, index=True)  # 对应Faiss向量ID

    # 工具调用信息
    tool_name = Column(String(256), index=True, nullable=False)
    tool_parameters = Column(JSON)

    # 风险评估
    risk_score = Column(Float, default=0.0)
    requires_confirmation = Column(Boolean, default=False)
    confirmation_reason = Column(Text)

    # 规则引擎结果
    matched_rules = Column(JSON)  # 匹配到的规则列表
    blacklist_hit = Column(Boolean, default=False)

    # 用户反馈
    user_confirmed = Column(Boolean, nullable=True)
    user_feedback = Column(Text)
    execution_success = Column(Boolean, nullable=True)
    execution_result = Column(JSON)

    # 上下文信息
    conversation_context = Column(JSON)
    similar_history_ids = Column(JSON)  # 检索到的相似历史记录ID列表

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    confirmed_at = Column(DateTime)
    executed_at = Column(DateTime)

    def __repr__(self):
        return f"<ToolCallHistory(id={self.id}, tool={self.tool_name}, user={self.user_id})>"


class MCPService(Base):
    """MCP服务注册表"""
    __tablename__ = "mcp_services"

    id = Column(Integer, primary_key=True, autoincrement=True)
    service_name = Column(String(256), unique=True, index=True, nullable=False)
    service_url = Column(String(512))
    description = Column(Text)

    # 工具信息
    tools = Column(JSON)  # 该服务提供的所有工具列表

    # 分层信息
    layer = Column(String(16), index=True)  # L1, L2, L3
    domain = Column(String(64), index=True)  # weather, email, etc.

    # 状态信息
    is_active = Column(Boolean, default=True, index=True)
    health_status = Column(String(32), default="healthy")  # healthy, degraded, down

    # 监控指标
    total_calls = Column(Integer, default=0)
    success_calls = Column(Integer, default=0)
    failed_calls = Column(Integer, default=0)
    avg_latency_ms = Column(Float, default=0.0)

    # 熔断状态
    circuit_breaker_state = Column(String(16), default="closed")  # closed, open, half_open
    circuit_breaker_opened_at = Column(DateTime)

    # 时间戳
    registered_at = Column(DateTime, default=datetime.utcnow)
    last_health_check = Column(DateTime)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<MCPService(id={self.id}, name={self.service_name}, status={self.health_status})>"


class ToolCallMetrics(Base):
    """工具调用指标"""
    __tablename__ = "tool_call_metrics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tool_name = Column(String(256), index=True, nullable=False)
    service_id = Column(Integer, index=True)  # 关联的MCP服务ID

    # 调用信息
    request_id = Column(String(64), index=True)
    user_id = Column(String(128), index=True)

    # 性能指标
    latency_ms = Column(Float)
    success = Column(Boolean)
    error_message = Column(Text)

    # 时间戳
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    def __repr__(self):
        return f"<ToolCallMetrics(tool={self.tool_name}, success={self.success})>"


class UserPreference(Base):
    """用户偏好设置"""
    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(128), unique=True, index=True, nullable=False)

    # 风险偏好
    risk_threshold = Column(Float, default=0.6)  # 个性化的风险阈值
    auto_confirm_tools = Column(JSON)  # 用户信任的工具列表，无需确认

    # 工具偏好
    preferred_tools = Column(JSON)  # 用户偏好的工具
    blocked_tools = Column(JSON)  # 用户屏蔽的工具

    # 设置
    settings = Column(JSON)

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<UserPreference(user_id={self.user_id})>"
