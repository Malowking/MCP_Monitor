# 快速测试指南

## ✅ 问题已修复

### 修复的问题
1. ✅ **缺少greenlet依赖** - 已添加到requirements.txt
2. ✅ **config.yaml格式错误** - 已修复YAML缩进
3. ✅ **PostgreSQL用户名错误** - 已更新为当前系统用户
4. ✅ **数据库初始化成功** - 测试通过！

---

## 🚀 快速启动步骤

### 1. 确认环境
```bash
# 检查Python版本
python --version  # 应该是3.9+

# 检查PostgreSQL状态
pg_isready
```

### 2. 安装依赖
```bash
# 如果还没安装，运行：
pip install -r requirements.txt
```

### 3. 配置数据库
编辑 `config/config.yaml`，确认数据库配置：
```yaml
database:
  postgresql:
    host: "localhost"
    port: 5432
    database: "mcp_monitor"
    user: "YOUR_USERNAME"  # 改成你的用户名
    password: ""  # 如果需要密码，填写这里
```

### 4. 创建数据库（如果还没创建）
```bash
createdb mcp_monitor
# 或者
psql postgres -c "CREATE DATABASE mcp_monitor;"
```

### 5. 初始化数据库
```bash
python scripts/init_database.py
```

**预期输出**:
```
2025-10-13 15:51:52.978 | INFO     | utils.config_loader:load_config:23 - Loaded configuration from config/config.yaml
2025-10-13 15:51:53.850 | INFO     | database.postgresql:__init__:51 - PostgreSQL manager initialized: localhost:5432/mcp_monitor
2025-10-13 15:51:53.851 | INFO     | database.faiss_db:_create_index:64 - Created new Faiss index: IVFFlat
2025-10-13 15:51:53.851 | INFO     | database.faiss_db:__init__:44 - Faiss manager initialized: ./data/faiss_index, dimension=1536
2025-10-13 15:51:53.851 | INFO     | database:__init__:28 - Database manager initialized
2025-10-13 15:51:53.851 | INFO     | __main__:init_database:26 - Creating database tables...
2025-10-13 15:51:53.962 | INFO     | database.postgresql:init_database:57 - Database tables created successfully
2025-10-13 15:51:53.962 | INFO     | __main__:init_database:29 - Database initialized successfully!
```

### 6. 启动服务
```bash
python main.py
```

**预期输出**:
```
INFO:     Started server process [xxxxx]
INFO:     Waiting for application startup.
2025-10-13 15:52:00.000 | INFO     | Starting MCP Monitor...
2025-10-13 15:52:00.000 | INFO     | Initializing database...
2025-10-13 15:52:00.000 | INFO     | Initializing model...
2025-10-13 15:52:00.000 | INFO     | Initializing orchestrator...
2025-10-13 15:52:00.000 | INFO     | MCP Monitor started successfully!
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

### 7. 测试API
打开浏览器访问: http://localhost:8000/docs

你会看到交互式API文档（Swagger UI）

---

## 🧪 验证测试

### 测试1: 健康检查
```bash
curl http://localhost:8000/api/v1/health
```

**预期响应**:
```json
{
  "status": "healthy",
  "service": "MCP Monitor"
}
```

### 测试2: 服务列表
```bash
curl http://localhost:8000/api/v1/services/list
```

### 测试3: 注册测试服务
```bash
curl -X POST http://localhost:8000/api/v1/services/register \
  -H "Content-Type: application/json" \
  -d '{
    "service_name": "test_service",
    "service_url": "http://localhost:9000",
    "description": "测试服务",
    "tools": [],
    "layer": "L1",
    "domain": "test"
  }'
```

---

## 📊 检查数据库

### 查看创建的表
```bash
psql mcp_monitor -c "\dt"
```

**应该看到**:
```
                   List of relations
 Schema |          Name          | Type  |  Owner
--------+------------------------+-------+----------
 public | mcp_services           | table | 00568200
 public | tool_call_history      | table | 00568200
 public | tool_call_metrics      | table | 00568200
 public | user_preferences       | table | 00568200
```

### 查看Faiss索引文件
```bash
ls -lh data/faiss_index/
```

**应该看到**:
```
total 8
-rw-r--r--  1 user  staff   1.0K Oct 13 15:51 id_map.pkl
-rw-r--r--  1 user  staff   512B Oct 13 15:51 index.faiss
```

---

## 🐛 常见问题

### 1. ModuleNotFoundError
**问题**: `ModuleNotFoundError: No module named 'xxx'`

**解决**:
```bash
pip install -r requirements.txt
```

### 2. PostgreSQL连接失败
**问题**: `connection to server failed`

**解决**:
```bash
# 启动PostgreSQL
brew services start postgresql  # macOS
sudo systemctl start postgresql  # Linux

# 检查状态
pg_isready
```

### 3. 数据库不存在
**问题**: `database "mcp_monitor" does not exist`

**解决**:
```bash
createdb mcp_monitor
```

### 4. 用户不存在
**问题**: `role "xxx" does not exist`

**解决**: 编辑 `config/config.yaml`，将 `user` 改为你的系统用户名：
```bash
whoami  # 查看当前用户名
```

### 5. 端口被占用
**问题**: `Address already in use`

**解决**: 修改 `main.py` 中的端口：
```python
uvicorn.run(
    "main:app",
    host="0.0.0.0",
    port=8001,  # 改成其他端口
    reload=False
)
```

---

## ✨ 完整的测试命令序列

一键测试所有功能：
```bash
# 1. 环境检查
python scripts/check_environment.py

# 2. 安装依赖
pip install -r requirements.txt

# 3. 创建数据库
createdb mcp_monitor

# 4. 初始化数据库
python scripts/init_database.py

# 5. 测试核心组件
python -c "
import sys
sys.path.insert(0, '.')
from utils.config_loader import load_config
from models import OpenAIAdapter

config = load_config()
model = OpenAIAdapter(config.get('model', {}))
print('✓ 所有测试通过！')
"

# 6. 启动服务（在新终端）
python main.py
```

---

## 📈 下一步

项目现在可以正常运行了！你可以：

1. **查看示例**: `python examples/usage_example.py`
2. **阅读文档**: 查看 API.md 了解接口
3. **发布GitHub**: 运行 `./publish_to_github.sh YOUR_USERNAME`

---

## 🎉 成功指标

如果你看到以下输出，说明一切正常：
- ✅ 数据库初始化成功
- ✅ 4个表已创建
- ✅ Faiss索引已创建
- ✅ 服务在 http://localhost:8000 运行
- ✅ API文档可访问

**恭喜！MCP Monitor 已成功运行！** 🚀
