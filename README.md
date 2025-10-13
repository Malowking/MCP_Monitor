# MCP Monitor

<p align="center">
  <img src="https://img.shields.io/badge/python-3.9+-blue.svg" alt="Python 3.9+"/>
  <img src="https://img.shields.io/badge/license-MIT-green.svg" alt="License MIT"/>
  <img src="https://img.shields.io/badge/platform-macOS%20%7C%20Windows%20%7C%20Linux-lightgrey.svg" alt="Platform"/>
  <img src="https://img.shields.io/badge/version-1.0.0-orange.svg" alt="Version"/>
</p>

<p align="center">
  <strong>智能MCP工具调用监控系统</strong><br>
  风险评估 • 历史学习 • 动态加载 • 跨平台支持
</p>

---

## 🌟 核心特性

### 🛡️ 智能风险评估
- ✅ RAG检索历史反馈，识别高风险操作
- ✅ 规则引擎检查黑名单和异常参数
- ✅ 基于阈值的自动确认机制（可配置）
- ✅ 动态prompt注入，提供个性化建议

### 🔄 动态工具加载
- **L1层**: 高频核心工具（始终可用）
- **L2层**: 领域专用工具（按需激活）
- **L3层**: 高风险工具（需显式授权）

### 📊 MCP服务监控
- 实时服务状态监控
- 服务队列管理
- 工具列表和说明展示
- 健康检查和熔断机制

### 💾 数据持久化
- PostgreSQL存储完整历史记录
- Faiss向量数据库高效检索
- 支持自定义存储路径

### 🌐 跨平台支持
- ✅ macOS (Intel & Apple Silicon)
- ✅ Windows 10/11
- ✅ Linux (Ubuntu, Debian, CentOS, RHEL)

---

## 📋 系统架构

```
用户提问
   ↓
大模型生成工具调用草案
   ↓
→【RAG 检索历史反馈】→ 若高风险 → 插入确认提示
   ↓
→【规则引擎检查】→ 若命中黑名单/异常参数 → 强制确认
   ↓
→【风险评分】→ 若高于阈值 → 需要用户确认
   ↓
→【动态 prompt 注入】→ 说明"根据您过去偏好..."
   ↓
输出给用户（含确认请求）
   ↓
用户反馈 → 存入数据库 → 用于强化学习
```

---

## 🚀 快速开始

### 系统要求
- **Python**: 3.9+
- **PostgreSQL**: 12+
- **内存**: 4GB+ （推荐8GB）

### 0. 环境检查（推荐）
```bash
python scripts/check_environment.py
```

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

如果遇到Faiss安装问题：
```bash
pip install faiss-cpu>=1.8.0
# 或使用conda
conda install -c pytorch faiss-cpu
```

### 2. 配置数据库
编辑 `config/config.yaml`：
```yaml
database:
  postgresql:
    host: "localhost"
    port: 5432
    database: "mcp_monitor"
    user: "your_user"
    password: "your_password"
```

### 3. 初始化数据库
```bash
python scripts/init_database.py
```

### 4. 启动服务
```bash
python main.py
```

### 5. 访问API
打开浏览器访问: http://localhost:8000/docs

---

## 📚 文档

- [📖 完整安装指南](INSTALL.md) - 平台特定的详细安装步骤
- [⚡ 快速开始](QUICKSTART.md) - 5分钟快速上手
- [🔌 API文档](API.md) - 完整的API接口说明
- [🏗️ 架构文档](ARCHITECTURE.md) - 系统设计和架构
- [🌍 跨平台支持](PLATFORM_SUPPORT.md) - 平台兼容性说明
- [🤝 贡献指南](CONTRIBUTING.md) - 如何参与贡献

---

## 💡 使用示例

### 处理高风险操作
```python
import httpx

async with httpx.AsyncClient() as client:
    response = await client.post(
        "http://localhost:8000/api/v1/query",
        json={
            "user_id": "user123",
            "question": "帮我删除/tmp目录下的所有文件"
        }
    )
    result = response.json()

    if result["requires_confirmation"]:
        print(f"⚠️  风险分数: {result['risk_score']}")
        print(f"📝 {result['tool_calls'][0]['confirmation_message']}")
```

### 注册MCP服务
```python
await client.post(
    "http://localhost:8000/api/v1/services/register",
    json={
        "service_name": "file_operations",
        "service_url": "http://localhost:9000",
        "description": "文件操作服务",
        "tools": [...],
        "layer": "L2",
        "domain": "file"
    }
)
```

完整示例: [examples/usage_example.py](examples/usage_example.py)

---

## 🛠️ 技术栈

- **Web框架**: FastAPI + Uvicorn
- **数据库**: PostgreSQL + SQLAlchemy
- **向量检索**: Faiss
- **模型接口**: OpenAI Compatible API
- **异步**: asyncio
- **日志**: loguru

---

## 📈 路线图

- [ ] Web UI 管理界面
- [ ] 更多模型适配器（Claude、Gemini等）
- [ ] 工具调用可视化
- [ ] 高级分析和报表
- [ ] 多语言支持
- [ ] 插件系统

---

## 🤝 贡献

欢迎贡献！请阅读 [CONTRIBUTING.md](CONTRIBUTING.md) 了解如何参与。

### 贡献者

感谢所有贡献者！

---

## 📝 许可证

本项目采用 [MIT License](LICENSE) 开源协议。

---

## 🙏 致谢

- [FastAPI](https://fastapi.tiangolo.com/) - 现代、快速的Web框架
- [Faiss](https://github.com/facebookresearch/faiss) - 高效的向量检索库
- [PostgreSQL](https://www.postgresql.org/) - 强大的关系型数据库

---

## 📧 联系方式

- **Issues**: [GitHub Issues](https://github.com/YOUR_USERNAME/MCP_Monitor/issues)
- **Discussions**: [GitHub Discussions](https://github.com/YOUR_USERNAME/MCP_Monitor/discussions)

---

<p align="center">
  如果这个项目对你有帮助，请给它一个⭐️
</p>
