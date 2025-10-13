#!/bin/bash
# 快速发布到GitHub脚本

set -e  # 遇到错误立即退出

echo "🚀 MCP Monitor - GitHub发布助手"
echo "================================"
echo ""

# 检查是否提供了GitHub用户名
if [ -z "$1" ]; then
    echo "❌ 错误: 请提供GitHub用户名"
    echo ""
    echo "用法: ./publish_to_github.sh YOUR_GITHUB_USERNAME"
    echo ""
    echo "例如: ./publish_to_github.sh johnsmith"
    exit 1
fi

GITHUB_USERNAME=$1
REPO_NAME="MCP_Monitor"

echo "📝 配置信息:"
echo "   GitHub用户名: $GITHUB_USERNAME"
echo "   仓库名称: $REPO_NAME"
echo ""

# 检查Git状态
if [ ! -d ".git" ]; then
    echo "❌ 错误: 不是Git仓库"
    echo "   请先运行: git init"
    exit 1
fi

# 检查是否有远程仓库
if git remote | grep -q "origin"; then
    echo "⚠️  警告: 远程仓库已存在"
    echo "   当前远程仓库:"
    git remote -v
    echo ""
    read -p "是否要覆盖远程仓库? (y/N): " confirm
    if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
        echo "❌ 取消操作"
        exit 1
    fi
    git remote remove origin
fi

# 添加远程仓库
echo "🔗 添加远程仓库..."
git remote add origin "https://github.com/$GITHUB_USERNAME/$REPO_NAME.git"
echo "✓ 远程仓库已添加: https://github.com/$GITHUB_USERNAME/$REPO_NAME"
echo ""

# 确认分支名称
BRANCH_NAME=$(git branch --show-current)
echo "📌 当前分支: $BRANCH_NAME"
echo ""

# 提示用户在GitHub创建仓库
echo "🌐 请在GitHub上创建仓库:"
echo "   1. 访问: https://github.com/new"
echo "   2. Repository name: $REPO_NAME"
echo "   3. Description: 智能MCP工具调用监控系统 - 风险评估、历史学习、动态加载"
echo "   4. Visibility: Public 或 Private"
echo "   5. ⚠️  不要勾选 'Initialize this repository with a README'"
echo "   6. 点击 'Create repository'"
echo ""

read -p "已在GitHub创建仓库? (y/N): " created
if [ "$created" != "y" ] && [ "$created" != "Y" ]; then
    echo "❌ 请先在GitHub创建仓库，然后重新运行此脚本"
    exit 1
fi

# 推送代码
echo ""
echo "📤 推送代码到GitHub..."
git push -u origin $BRANCH_NAME

# 推送标签
echo ""
echo "🏷️  推送标签..."
git push origin --tags

echo ""
echo "================================"
echo "✅ 发布成功！"
echo "================================"
echo ""
echo "🎉 你的仓库已发布到GitHub:"
echo "   https://github.com/$GITHUB_USERNAME/$REPO_NAME"
echo ""
echo "📚 下一步:"
echo "   1. 访问仓库页面"
echo "   2. 添加描述和主题标签 (Topics)"
echo "   3. 创建Release: https://github.com/$GITHUB_USERNAME/$REPO_NAME/releases/new"
echo "   4. 分享你的项目!"
echo ""
echo "💡 提示: 查看 GITHUB_PUBLISH.md 了解更多发布选项"
