# 跨平台安装指南

本项目支持 **macOS**、**Windows** 和 **Linux** 系统。

## 系统要求

- Python 3.9 或更高版本
- PostgreSQL 12 或更高版本
- 4GB+ RAM（推荐8GB以上用于Faiss索引）

---

## macOS 安装指南

### 1. 安装 Python
```bash
# 使用 Homebrew 安装
brew install python@3.11

# 或者从 python.org 下载安装包
```

### 2. 安装 PostgreSQL
```bash
# 使用 Homebrew
brew install postgresql@15
brew services start postgresql@15

# 创建数据库
createdb mcp_monitor
```

### 3. 安装项目依赖
```bash
cd MCP_Monitor

# 创建虚拟环境（推荐）
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 4. 配置和启动
```bash
# 编辑配置文件
nano config/config.yaml

# 初始化数据库
python scripts/init_database.py

# 启动服务
python main.py
```

---

## Windows 安装指南

### 1. 安装 Python
从 [python.org](https://www.python.org/downloads/windows/) 下载并安装 Python 3.11+

**重要**: 安装时勾选 "Add Python to PATH"

### 2. 安装 PostgreSQL
从 [postgresql.org](https://www.postgresql.org/download/windows/) 下载安装包

安装完成后，使用 pgAdmin 或命令行创建数据库：
```cmd
psql -U postgres
CREATE DATABASE mcp_monitor;
\q
```

### 3. 安装项目依赖
```cmd
cd MCP_Monitor

# 创建虚拟环境（推荐）
python -m venv venv
venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

### 4. 配置和启动
```cmd
# 编辑配置文件（使用记事本或VS Code）
notepad config\config.yaml

# 初始化数据库
python scripts\init_database.py

# 启动服务
python main.py
```

---

## Linux 安装指南

### 1. 安装 Python（Ubuntu/Debian）
```bash
sudo apt update
sudo apt install python3.11 python3.11-venv python3-pip
```

### CentOS/RHEL
```bash
sudo yum install python3.11 python3-pip
```

### 2. 安装 PostgreSQL

**Ubuntu/Debian:**
```bash
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql

# 创建数据库
sudo -u postgres psql
CREATE DATABASE mcp_monitor;
\q
```

**CentOS/RHEL:**
```bash
sudo yum install postgresql-server postgresql-contrib
sudo postgresql-setup initdb
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

### 3. 安装项目依赖
```bash
cd MCP_Monitor

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 4. 配置和启动
```bash
# 编辑配置文件
nano config/config.yaml

# 初始化数据库
python scripts/init_database.py

# 启动服务
python main.py
```

---

## Docker 方式安装（推荐生产环境）

### 1. 创建 Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# 复制项目文件
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# 创建数据目录
RUN mkdir -p data/faiss_index logs

EXPOSE 8000

CMD ["python", "main.py"]
```

### 2. 创建 docker-compose.yml
```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: mcp_monitor
      POSTGRES_USER: mcp_user
      POSTGRES_PASSWORD: your_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  mcp_monitor:
    build: .
    ports:
      - "8000:8000"
    depends_on:
      - postgres
    volumes:
      - ./config:/app/config
      - ./data:/app/data
      - ./logs:/app/logs
    environment:
      - DATABASE_HOST=postgres

volumes:
  postgres_data:
```

### 3. 启动
```bash
docker-compose up -d
```

---

## 常见问题

### 1. Faiss 安装失败

**问题**: `ERROR: Could not find a version that satisfies the requirement faiss-cpu`

**解决方案**:
```bash
# 使用最新版本
pip install faiss-cpu>=1.8.0

# 或者使用 conda（推荐）
conda install -c pytorch faiss-cpu
```

### 2. PostgreSQL 连接失败

**macOS**:
```bash
# 检查服务状态
brew services list

# 重启服务
brew services restart postgresql@15
```

**Windows**:
- 打开服务管理器（services.msc）
- 找到 PostgreSQL 服务并启动

**Linux**:
```bash
sudo systemctl status postgresql
sudo systemctl restart postgresql
```

### 3. 权限问题（Linux/macOS）

```bash
# 给予执行权限
chmod +x scripts/init_database.py

# 创建日志目录
mkdir -p logs data
chmod 755 logs data
```

### 4. 端口被占用

编辑 `main.py` 修改端口：
```python
uvicorn.run(
    "main:app",
    host="0.0.0.0",
    port=8080,  # 改成其他端口
    reload=False
)
```

### 5. NumPy 兼容性问题

如果遇到 NumPy 版本问题：
```bash
pip install "numpy>=1.24.0,<2.0.0"
```

---

## 依赖说明

### 核心依赖
- **FastAPI**: Web框架
- **PostgreSQL**: 主数据库
- **Faiss**: 向量检索库
- **OpenAI**: 模型接口

### 平台特定注意事项

**macOS (Apple Silicon)**:
- 使用 `faiss-cpu` 而非 `faiss-gpu`
- 某些包可能需要通过 conda 安装

**Windows**:
- 确保安装 Visual C++ Build Tools（用于某些依赖编译）
- 路径使用反斜杠 `\`

**Linux**:
- 可能需要安装额外的系统库（gcc、postgresql-devel等）

---

## 验证安装

```bash
# 激活虚拟环境
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate      # Windows

# 检查依赖
pip list

# 测试导入
python -c "import faiss; import fastapi; import sqlalchemy; print('All imports successful!')"

# 启动服务
python main.py
```

访问 http://localhost:8000/docs 查看API文档

---

## 生产部署建议

1. **使用进程管理器**:
   - Linux: systemd, supervisor
   - Windows: NSSM (Non-Sucking Service Manager)

2. **配置反向代理**:
   - Nginx 或 Apache

3. **环境变量**:
   - 不要在配置文件中硬编码敏感信息
   - 使用 `.env` 文件

4. **监控和日志**:
   - 配置日志轮转
   - 使用监控工具（Prometheus、Grafana）

5. **备份**:
   - 定期备份 PostgreSQL 数据库
   - 备份 Faiss 索引文件

---

需要帮助？查看 [README.md](README.md) 或 [QUICKSTART.md](QUICKSTART.md)
