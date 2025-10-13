# 快速开始指南

## 1. 环境准备

### 安装依赖
```bash
pip install -r requirements.txt
```

### 配置数据库
确保已安装并启动PostgreSQL：
```bash
# macOS
brew install postgresql
brew services start postgresql

# 创建数据库
createdb mcp_monitor
```

### 配置文件
编辑 `config/config.yaml`，设置：
- PostgreSQL连接信息
- Faiss索引路径
- 模型API配置
- 风险阈值

## 2. 初始化数据库

```bash
python scripts/init_database.py
```

## 3. 实现模型适配器

创建你的模型实现文件（例如 `my_model.py`）：

```python
from models.base_model import BaseModel, Message, ToolDefinition, ModelResponse
from typing import List, Optional, AsyncGenerator

class MyModelAdapter(BaseModel):
    async def generate(
        self,
        messages: List[Message],
        tools: Optional[List[ToolDefinition]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> ModelResponse:
        # 实现你的模型调用逻辑
        # 返回 ModelResponse 对象
        pass

    async def generate_stream(
        self,
        messages: List[Message],
        tools: Optional[List[ToolDefinition]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        # 实现流式生成
        pass

    async def get_embedding(self, text: str) -> List[float]:
        # 实现embedding生成
        pass
```

如果使用OpenAI兼容的API（如Ollama、LM Studio等），可以直接使用内置的 `OpenAIAdapter`。

## 4. 启动服务

```bash
python main.py
```

服务将在 `http://localhost:8000` 启动。

## 5. API文档

访问 `http://localhost:8000/docs` 查看交互式API文档。

## 6. 使用示例

### 基本查询
```python
import httpx

async with httpx.AsyncClient() as client:
    response = await client.post(
        "http://localhost:8000/api/v1/query",
        json={
            "user_id": "user123",
            "question": "帮我删除/tmp目录下的文件"
        }
    )
    result = response.json()
    print(result)
```

### 注册MCP服务
```python
response = await client.post(
    "http://localhost:8000/api/v1/services/register",
    json={
        "service_name": "my_service",
        "service_url": "http://localhost:9000",
        "description": "My MCP Service",
        "tools": [...],
        "layer": "L2",
        "domain": "custom"
    }
)
```

运行完整示例：
```bash
python examples/usage_example.py
```

## 7. 配置调整

### 调整风险阈值
在 `config/config.yaml` 中：
```yaml
risk_assessment:
  confirmation_threshold: 0.6  # 降低此值会减少确认次数
  high_risk_threshold: 0.8
```

### 添加自定义规则
编辑 `config/rules.json` 添加新规则。

### 配置工具分层
在 `config/config.yaml` 中定义L1、L2、L3工具层级。

## 8. 常见问题

### 1. 数据库连接失败
检查PostgreSQL是否启动，配置是否正确。

### 2. Faiss索引错误
确保 `data/faiss_index` 目录存在且有写权限。

### 3. 模型API调用失败
检查模型配置，确认API端点可访问。

## 9. 监控和调试

查看日志：
```bash
tail -f logs/mcp_monitor.log
```

查看服务状态：
```bash
curl http://localhost:8000/api/v1/services/list
```

## 10. 生产部署建议

1. 使用环境变量管理敏感配置
2. 配置反向代理（Nginx）
3. 使用进程管理器（systemd、supervisor）
4. 配置日志轮转
5. 定期备份数据库
6. 监控服务健康状态

## 需要帮助？

查看完整文档：`README.md`
