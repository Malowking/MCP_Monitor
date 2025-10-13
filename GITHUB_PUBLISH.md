# 发布到GitHub指南

## 步骤1: 初始化Git仓库

```bash
cd /Users/00568200/PycharmProjects/MCP_Monitor

# 初始化Git仓库
git init

# 添加所有文件
git add .

# 创建首次提交
git commit -m "🎉 Initial commit: MCP Monitor v1.0.0

- 智能风险评估系统（RAG + 规则引擎）
- 动态工具加载和分层架构
- MCP服务监控和熔断机制
- PostgreSQL + Faiss 数据持久化
- 跨平台支持（macOS/Windows/Linux）
- 完整的API文档和示例"
```

## 步骤2: 在GitHub上创建仓库

### 方法1: 使用GitHub网页

1. 访问 https://github.com/new
2. 填写仓库信息：
   - **Repository name**: `MCP_Monitor`
   - **Description**: `智能MCP工具调用监控和管理系统 - 支持风险评估、用户确认、历史学习和动态工具加载`
   - **Visibility**: Public（或 Private）
   - ⚠️ **不要**勾选 "Initialize this repository with a README"（我们已经有了）
   - ⚠️ **不要**添加 .gitignore 或 license（我们已经有了）
3. 点击 "Create repository"

### 方法2: 使用GitHub CLI（如果已安装）

```bash
# 创建仓库
gh repo create MCP_Monitor --public --source=. --remote=origin

# 推送代码
git push -u origin main
```

## 步骤3: 连接远程仓库并推送

在GitHub创建仓库后，会显示类似这样的命令：

```bash
# 添加远程仓库（替换为你的GitHub用户名）
git remote add origin https://github.com/YOUR_USERNAME/MCP_Monitor.git

# 检查分支名称（可能是main或master）
git branch -M main

# 推送代码
git push -u origin main
```

## 步骤4: 添加仓库主题和标签

在GitHub仓库页面：
1. 点击 "About" 旁边的齿轮图标
2. 添加描述
3. 添加主题标签（Topics）：
   ```
   mcp
   tool-monitoring
   risk-assessment
   rag
   faiss
   fastapi
   python
   postgresql
   vector-database
   machine-learning
   llm-tools
   openai
   model-safety
   ```

## 步骤5: 配置GitHub Pages（可选）

如果你想托管文档：

1. 进入仓库的 Settings → Pages
2. Source 选择 "main" 分支
3. 文件夹选择 "/ (root)"
4. 保存

## 步骤6: 创建Release

```bash
# 创建标签
git tag -a v1.0.0 -m "Release v1.0.0: Initial release"

# 推送标签
git push origin v1.0.0
```

或在GitHub网页上：
1. 进入仓库的 "Releases" 页面
2. 点击 "Create a new release"
3. 选择标签 `v1.0.0` 或创建新标签
4. 填写发布说明（可以参考 CHANGELOG.md）
5. 点击 "Publish release"

## 步骤7: 添加徽章（可选）

在 README.md 顶部添加徽章：

```markdown
# MCP Monitor

![Python](https://img.shields.io/badge/python-3.9+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20Windows%20%7C%20Linux-lightgrey.svg)
[![GitHub stars](https://img.shields.io/github/stars/YOUR_USERNAME/MCP_Monitor.svg)](https://github.com/YOUR_USERNAME/MCP_Monitor/stargazers)
[![GitHub issues](https://img.shields.io/github/issues/YOUR_USERNAME/MCP_Monitor.svg)](https://github.com/YOUR_USERNAME/MCP_Monitor/issues)
```

## 完整命令总结

```bash
# 1. 初始化Git
cd /Users/00568200/PycharmProjects/MCP_Monitor
git init
git add .
git commit -m "🎉 Initial commit: MCP Monitor v1.0.0"

# 2. 在GitHub创建仓库后，连接远程仓库
git remote add origin https://github.com/YOUR_USERNAME/MCP_Monitor.git
git branch -M main
git push -u origin main

# 3. 创建标签和发布
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0
```

## 推荐的仓库描述

**Short description:**
```
智能MCP工具调用监控系统 - 风险评估、历史学习、动态加载 | Smart MCP tool monitoring with risk assessment, RAG, and dynamic loading
```

**About:**
```
MCP Monitor 是一个智能的 MCP 工具调用监控和管理系统，提供风险评估、用户确认、历史学习和动态工具加载功能。支持 macOS、Windows 和 Linux 平台。

核心特性：
• 🛡️ 智能风险评估（RAG + 规则引擎 + 多维评分）
• 🔄 动态工具路由和分层加载（L1/L2/L3）
• 📊 实时服务监控和熔断机制
• 💾 PostgreSQL + Faiss 向量检索
• 🌐 跨平台支持
• 🔌 OpenAI 兼容接口
```

## 检查清单

发布前确认：
- [ ] 所有敏感信息已从代码中移除
- [ ] config/config.yaml 中的密码改为示例值
- [ ] .gitignore 正确配置
- [ ] README.md 完整且清晰
- [ ] LICENSE 文件已添加
- [ ] 所有文档都已更新
- [ ] 代码可以正常运行

## 后续维护

### 添加更新时：
```bash
git add .
git commit -m "feat: 添加新功能"
git push origin main
```

### 创建新版本：
```bash
git tag -a v1.1.0 -m "Release v1.1.0"
git push origin v1.1.0
```

### 查看状态：
```bash
git status
git log --oneline
git remote -v
```

## 故障排除

### 推送被拒绝
```bash
git pull origin main --rebase
git push origin main
```

### 修改最后一次提交
```bash
git commit --amend -m "新的提交信息"
git push -f origin main  # 谨慎使用
```

### 删除远程标签
```bash
git push --delete origin v1.0.0
git tag -d v1.0.0
```

---

祝你发布顺利！🚀
