# 贡献指南

感谢你考虑为 MCP Monitor 做贡献！

## 如何贡献

### 报告 Bug

如果你发现了 bug，请创建一个 issue，包含：
- Bug 的详细描述
- 重现步骤
- 预期行为
- 实际行为
- 环境信息（操作系统、Python版本等）

### 提交功能请求

我们欢迎新功能的想法！请创建一个 issue，描述：
- 功能的用途
- 为什么需要这个功能
- 如何实现（如果有想法）

### 提交 Pull Request

1. Fork 这个仓库
2. 创建你的特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交你的改动 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建一个 Pull Request

### 代码规范

- 遵循 PEP 8 Python 代码风格
- 为新功能添加文档
- 添加必要的测试
- 确保所有测试通过

### 开发环境设置

```bash
# 克隆仓库
git clone https://github.com/yourusername/MCP_Monitor.git
cd MCP_Monitor

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# 安装开发依赖
pip install -r requirements.txt
pip install pytest black flake8

# 运行测试
pytest tests/
```

### 提交信息规范

使用清晰的提交信息：
- `feat: 添加新功能`
- `fix: 修复bug`
- `docs: 更新文档`
- `style: 代码格式调整`
- `refactor: 代码重构`
- `test: 添加测试`
- `chore: 构建/工具链更新`

## 行为准则

- 尊重所有贡献者
- 接受建设性的批评
- 专注于对项目最有利的事情
- 保持友好和专业

## 需要帮助？

如果你有任何问题，可以：
- 创建一个 issue
- 查看现有的 issues
- 阅读文档

感谢你的贡献！
