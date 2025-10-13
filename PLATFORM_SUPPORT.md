# 跨平台支持更新总结

## 已完成的修改

### 1. ✅ 更新依赖版本（requirements.txt）

**修改前问题**:
- `faiss-cpu==1.7.4` 在Mac上找不到对应版本
- 固定版本号导致平台兼容性差

**修改后**:
```txt
# 使用版本范围，兼容所有平台
faiss-cpu>=1.8.0          # 支持Mac/Windows/Linux
numpy>=1.24.0,<2.0.0      # 避免NumPy 2.0兼容性问题
fastapi>=0.104.1          # 使用最新版本
```

**优势**:
- ✓ Mac (Apple Silicon & Intel)
- ✓ Windows (x64)
- ✓ Linux (x64, ARM)

---

### 2. ✅ 创建跨平台安装指南（INSTALL.md）

包含详细的平台特定安装说明：

#### macOS 安装
- 使用Homebrew安装依赖
- PostgreSQL配置
- Apple Silicon特别说明

#### Windows 安装
- 下载安装包方式
- pgAdmin使用
- Visual C++ Build Tools提示

#### Linux 安装
- Ubuntu/Debian方式
- CentOS/RHEL方式
- systemd服务配置

#### Docker 方式
- 提供Dockerfile和docker-compose.yml
- 适合所有平台的生产环境部署

---

### 3. ✅ 环境检查脚本（scripts/check_environment.py）

**功能**:
- 自动检测操作系统和架构
- 检查Python版本
- 检查PostgreSQL安装状态
- 检查Python依赖包
- 验证目录结构
- 自动创建缺失目录
- 根据平台给出定制化安装建议

**使用方法**:
```bash
python scripts/check_environment.py
```

**输出示例**:
```
============================================================
MCP Monitor - 环境检查
============================================================
✓ Python版本: 3.12.7
✓ 操作系统: Darwin (macOS)
✓ 架构: arm64

检查依赖:
  ✓ FastAPI
  ✓ SQLAlchemy
  ✓ NumPy
  ✓ Faiss
  ✓ Pydantic
  ✓ Uvicorn

✓ 环境检查通过！
```

---

### 4. ✅ 更新文档（README.md）

**添加内容**:
- 系统要求说明
- 跨平台支持声明
- 环境检查步骤
- Faiss安装替代方案
- 指向INSTALL.md的链接

---

## 文件清单

### 新增文件
1. `INSTALL.md` - 详细的跨平台安装指南
2. `scripts/check_environment.py` - 环境检查工具

### 修改文件
1. `requirements.txt` - 更新依赖版本
2. `README.md` - 添加跨平台说明

### 保持不变的文件
- `database/faiss_db.py` - 已经兼容所有平台
- 其他Python代码 - 都是跨平台的

---

## 安装步骤（所有平台通用）

### 快速安装
```bash
# 1. 克隆项目
cd MCP_Monitor

# 2. 检查环境
python scripts/check_environment.py

# 3. 安装依赖
pip install -r requirements.txt

# 4. 如果Faiss安装失败
pip install faiss-cpu>=1.8.0
# 或使用conda
conda install -c pytorch faiss-cpu

# 5. 配置数据库
# 编辑 config/config.yaml

# 6. 初始化数据库
python scripts/init_database.py

# 7. 启动服务
python main.py
```

---

## 平台特定注意事项

### macOS
- ✅ Intel和Apple Silicon都支持
- 推荐使用Homebrew安装依赖
- Faiss建议通过conda安装（如果遇到问题）

### Windows
- ✅ Windows 10/11 支持
- 需要Visual C++ Build Tools（某些包需要）
- 使用反斜杠路径 `\`
- PostgreSQL使用pgAdmin管理

### Linux
- ✅ Ubuntu, Debian, CentOS, RHEL 支持
- 可能需要安装额外的系统库（gcc, postgresql-devel）
- 推荐使用包管理器安装PostgreSQL

---

## 常见问题解决方案

### 1. Faiss安装失败
```bash
# Mac用户
pip install faiss-cpu>=1.8.0
# 或
conda install -c pytorch faiss-cpu

# Windows用户
pip install faiss-cpu>=1.8.0
# 确保安装了 Visual C++ Build Tools

# Linux用户
pip install faiss-cpu>=1.8.0
# 如果失败，安装编译工具
sudo apt install build-essential  # Ubuntu/Debian
```

### 2. PostgreSQL连接失败
- 检查PostgreSQL服务是否启动
- 验证配置文件中的连接信息
- 确保数据库已创建

### 3. NumPy版本冲突
```bash
pip install "numpy>=1.24.0,<2.0.0"
```

---

## 测试验证

运行以下命令验证安装：

```bash
# 1. 检查环境
python scripts/check_environment.py

# 2. 测试导入
python -c "import faiss; import fastapi; import sqlalchemy; print('✓ 所有依赖导入成功!')"

# 3. 初始化数据库
python scripts/init_database.py

# 4. 启动服务
python main.py

# 5. 访问API文档
# 打开浏览器: http://localhost:8000/docs
```

---

## Docker部署（推荐生产环境）

Docker方式完全跨平台，适合所有系统：

```bash
# 使用Docker Compose
docker-compose up -d

# 访问服务
curl http://localhost:8000/health
```

优势：
- 无需手动安装依赖
- 环境一致性
- 易于部署和扩展

---

## 文档索引

- **README.md** - 项目概述和快速开始
- **INSTALL.md** - 详细的平台特定安装指南
- **QUICKSTART.md** - 快速开始指南
- **API.md** - API接口文档
- **ARCHITECTURE.md** - 系统架构文档

---

## 下一步

你现在可以在Mac、Windows或Linux上安装MCP_Monitor：

1. 运行环境检查：`python scripts/check_environment.py`
2. 安装依赖：`pip install -r requirements.txt`
3. 初始化数据库：`python scripts/init_database.py`
4. 启动服务：`python main.py`

如果遇到问题，查看 INSTALL.md 获取详细帮助！
