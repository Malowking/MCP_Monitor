# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-10-13

### Added
- 🎉 首次发布 MCP Monitor
- ✨ 智能风险评估系统（RAG检索 + 规则引擎 + 风险评分）
- 🔄 动态工具加载和路由机制
- 📊 MCP服务监控和健康检查
- 🛡️ 熔断机制和降级策略
- 💾 PostgreSQL + Faiss 双重数据持久化
- 🔧 分层工具架构（L1/L2/L3）
- 📝 动态prompt注入
- 🌐 跨平台支持（macOS、Windows、Linux）
- 🔌 OpenAI兼容的模型接口
- 📚 完整的API文档
- 🧪 环境检查工具

### Features
- 基于阈值的自动确认机制
- 历史反馈学习和相似案例检索
- 黑名单和自定义规则引擎
- 用户偏好管理
- 工具调用指标统计
- RESTful API接口
- 流式响应支持
- 健康检查和监控端点

### Documentation
- README.md - 项目概述
- INSTALL.md - 跨平台安装指南
- QUICKSTART.md - 快速开始指南
- API.md - API接口文档
- ARCHITECTURE.md - 系统架构文档
- PLATFORM_SUPPORT.md - 跨平台支持说明
- CONTRIBUTING.md - 贡献指南

### Infrastructure
- FastAPI web框架
- PostgreSQL 数据库
- Faiss 向量检索
- SQLAlchemy ORM
- Pydantic 数据验证
- Loguru 日志系统
- Docker 支持

---

## [Unreleased]

### Planned
- [ ] Web UI 管理界面
- [ ] 更多模型适配器（Anthropic Claude、Google Gemini等）
- [ ] 工具调用可视化
- [ ] 高级分析和报表
- [ ] 多语言支持
- [ ] 插件系统

---

[1.0.0]: https://github.com/yourusername/MCP_Monitor/releases/tag/v1.0.0
