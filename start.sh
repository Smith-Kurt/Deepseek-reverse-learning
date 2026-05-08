#!/bin/bash

# ============================================================
# DeepSeek API 学习项目 - 启动脚本
# 声明：本项目完全由 AI 生成，仅供个人学习研究使用
# ============================================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# ============================================================
# 检查依赖
# ============================================================

echo -e "${BLUE}检查依赖...${NC}"

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}错误: 未找到 python3，请先安装 Python 3.9+${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo -e "  Python: ${GREEN}$PYTHON_VERSION${NC}"

# 检查 Node.js
if ! command -v node &> /dev/null; then
    echo -e "${RED}错误: 未找到 node，请先安装 Node.js 16+${NC}"
    echo -e "${YELLOW}安装方法: https://nodejs.org/${NC}"
    exit 1
fi

NODE_VERSION=$(node --version)
echo -e "  Node.js: ${GREEN}$NODE_VERSION${NC}"

# 安装 Python 依赖
echo -e "${BLUE}安装 Python 依赖...${NC}"
pip3 install -q -r requirements.txt 2>/dev/null || pip install -q -r requirements.txt 2>/dev/null

# ============================================================
# 加载环境变量
# ============================================================

# 如果存在 .env 文件，加载它
if [ -f .env ]; then
    echo -e "${BLUE}加载 .env 配置...${NC}"
    export $(cat .env | grep -v '^#' | grep -v '^$' | xargs)
fi

# 设置默认值
export DEEPSEEK_TOKEN="${DEEPSEEK_TOKEN:-}"
export DEEPSEEK_EMAIL="${DEEPSEEK_EMAIL:-}"
export DEEPSEEK_PASSWORD="${DEEPSEEK_PASSWORD:-}"
export SERVER_HOST="${SERVER_HOST:-0.0.0.0}"
export SERVER_PORT="${SERVER_PORT:-8000}"
export API_KEY="${API_KEY:-}"

# ============================================================
# 验证配置
# ============================================================

echo -e "${BLUE}验证配置...${NC}"

if [ -n "$DEEPSEEK_TOKEN" ]; then
    echo -e "  登录方式: ${GREEN}Token${NC}"
    echo -e "  Token: ${GREEN}${DEEPSEEK_TOKEN:0:20}...${NC}"
elif [ -n "$DEEPSEEK_EMAIL" ]; then
    if [ -z "$DEEPSEEK_PASSWORD" ]; then
        echo -e "${RED}错误: 使用邮箱登录时必须同时设置 DEEPSEEK_PASSWORD${NC}"
        exit 1
    fi
    echo -e "  登录方式: ${GREEN}邮箱密码${NC}"
    echo -e "  邮箱: ${GREEN}$DEEPSEEK_EMAIL${NC}"
else
    echo -e "${RED}错误: 请设置 DEEPSEEK_TOKEN 或 DEEPSEEK_EMAIL+DEEPSEEK_PASSWORD${NC}"
    echo ""
    echo -e "${YELLOW}配置方法 (选择一种):${NC}"
    echo -e "  1. ${BLUE}创建 .env 文件:${NC}"
    echo -e "     cp .env.example .env"
    echo -e "     # 编辑 .env 填入配置"
    echo ""
    echo -e "  2. ${BLUE}设置环境变量:${NC}"
    echo -e "     export DEEPSEEK_TOKEN='your_token'"
    echo -e "     # 或"
    echo -e "     export DEEPSEEK_EMAIL='your_email'"
    echo -e "     export DEEPSEEK_PASSWORD='your_password'"
    exit 1
fi

# ============================================================
# 启动服务
# ============================================================

echo ""
echo -e "${GREEN}============================================================${NC}"
echo -e "${GREEN}  DeepSeek Reverse API Server${NC}"
echo -e "${GREEN}============================================================${NC}"
echo -e "  服务地址: ${BLUE}http://$SERVER_HOST:$SERVER_PORT${NC}"
echo -e "  API 文档: ${BLUE}http://$SERVER_HOST:$SERVER_PORT/docs${NC}"
echo -e "  Cherry Studio: ${BLUE}http://127.0.0.1:$SERVER_PORT/v1${NC}"
echo -e "${GREEN}============================================================${NC}"
echo ""

# 启动 FastAPI 服务
python3 server.py
