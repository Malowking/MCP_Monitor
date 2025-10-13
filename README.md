# MCP Monitor

一个智能的MCP工具调用监控和管理系统，支持风险评估、用户确认、历史学习和动态工具加载。

## 核心特性

### 1. 智能风险评估
- RAG检索历史反馈，识别高风险操作
- 规则引擎检查黑名单和异常参数
- 基于阈值的自动确认机制
- 动态prompt注入，提供个性化建议

### 2. 分层工具架构
- **L1层**: 高频核心工具（始终可用）
- **L2层**: 领域专用工具（按需激活）
- **L3层**: 高风险工具（需显式授权）

### 3. 动态工具加载
- 按需注册，避免prompt过载
- 工具路由器智能预判所需工具
- 场景化工具集管理

### 4. MCP服务监控
- 实时服务状态监控
- 服务队列管理
- 工具列表和说明展示
- 健康检查和熔断机制

### 5. 数据持久化
- PostgreSQL存储完整历史记录
- Faiss向量数据库高效检索用户问题
- 支持自定义存储路径

## 系统架构

```
用户提问
   ↓
大模型生成工具调用草案
   ↓
→【RAG检索历史反馈】→ 若高风险 → 插入确认提示
   ↓
→【规则引擎检查】→ 若命中黑名单/异常参数 → 强制确认
   ↓
→【风险评分】→ 若高于阈值 → 需要用户确认
   ↓
→【动态prompt注入】→ 说明"根据您过去偏好..."
   ↓
输出给用户（含确认请求）
   ↓
用户反馈 → 存入数据库 → 用于强化学习
```

## 系统要求

- **操作系统**: macOS, Windows, Linux
- **Python**: 3.9 或更高版本
- **数据库**: PostgreSQL 12+
- **内存**: 4GB+ （推荐8GB以上）

## 快速开始

### 0. 环境检查（推荐）
```bash
# 运行环境检查脚本，自动检测系统并给出安装建议
python scripts/check_environment.py
```

### 1. 安装依赖

**所有平台通用**:
```bash
pip install -r requirements.txt
```

**如果遇到Faiss安装问题**:
```bash
# 方法1: 安装最新版本
pip install faiss-cpu>=1.8.0

# 方法2: 使用conda（推荐）
conda install -c pytorch faiss-cpu
```

**详细的平台特定安装说明**: 请查看 [INSTALL.md](INSTALL.md)

### 2. 配置数据库
编辑 `config/config.yaml`，设置PostgreSQL和Faiss配置：
```yaml
database:
  postgresql:
    host: "localhost"
    port: 5432
    database: "mcp_monitor"
    user: "your_user"
    password: "your_password"

  faiss:
    index_path: "./data/faiss_index"
    dimension: 1536
```

### 3. 初始化数据库
```bash
python scripts/init_database.py
```

### 4. 实现模型适配器
创建你的模型实现，继承 `BaseModel` 抽象类：
```python
from models.base_model import BaseModel

class MyModelAdapter(BaseModel):
    async def generate(self, messages, tools=None):
        # 实现你的模型调用逻辑
        pass
```

### 5. 启动服务
```bash
python main.py
```

## 项目结构

```
MCP_Monitor/
├── config/           # 配置文件
├── database/         # 数据库模块
├── models/           # 模型抽象类和适配器
├── core/             # 核心功能（RAG、规则引擎、风险评估）
├── mcp_manager/      # MCP服务管理和监控
├── api/              # API接口
├── utils/            # 工具函数
├── tests/            # 测试
└── main.py           # 入口文件
```

## API示例

### 处理用户查询
```python
POST /api/v1/query
{
  "user_id": "user123",
  "question": "帮我删除/tmp目录下的所有文件",
  "context": {}
}
```

响应：
```json
{
  "requires_confirmation": true,
  "risk_score": 0.85,
  "tool_calls": [...],
  "confirmation_message": "此操作涉及文件删除，风险较高，是否确认执行？",
  "reason": "根据您过去的偏好，类似操作需要谨慎处理"
}
```

### 确认工具调用
```python
POST /api/v1/confirm
{
  "request_id": "req_xyz",
  "user_id": "user123",
  "confirmed": true,
  "feedback": "这个操作是安全的"
}
```

## 配置说明

### 风险阈值
在 `config/config.yaml` 中调整：
```yaml
risk_assessment:
  confirmation_threshold: 0.6  # 调整此值控制确认频率
```

### 工具分层
定义不同层级的工具：
```yaml
tool_layers:
  L1_core_tools:      # 始终加载
  L2_domain_tools:    # 按需加载
  L3_high_risk_tools: # 需授权
```

## 扩展开发

### 添加自定义规则
编辑 `config/rules.json`，添加新的规则定义。

### 实现新的模型适配器
继承 `BaseModel` 并实现必要方法。

### 添加MCP服务
通过API注册新的MCP服务。

## License
MIT
