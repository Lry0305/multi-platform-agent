#!/usr/bin/env bash
set -e

# ============================================================
# 🍒 多平台内容发布 Agent - 一键环境配置
# 用法: bash setup.sh
# ============================================================

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo ""
echo "🍒 多平台内容发布 Agent - 环境配置中..."
echo ""

# ── 1. Python 版本检查 ──
PYTHON=$(command -v python3 || command -v python)
if [ -z "$PYTHON" ]; then
    echo -e "${RED}❌ 未找到 Python3，请先安装 Python 3.8+${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Python: $($PYTHON --version)${NC}"

# ── 2. 创建 .env（如果不存在） ──
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo -e "${YELLOW}📝 已创建 .env 文件，请编辑填入 SILICONFLOW_API_KEY${NC}"
    else
        echo -e "${YELLOW}📝 未找到 .env.example，手动创建 .env${NC}"
        echo "# 多平台内容发布 Agent - 环境变量" > .env
        echo "SILICONFLOW_API_KEY=" >> .env
        echo -e "${YELLOW}📝 已创建 .env，请编辑填入 SILICONFLOW_API_KEY${NC}"
    fi
else
    echo -e "${GREEN}✅ .env 文件已存在${NC}"
fi

# ── 3. 检查 API Key ──
if grep -q "SILICONFLOW_API_KEY=sk-" ".env" 2>/dev/null; then
    echo -e "${GREEN}✅ SiliconFlow API Key 已配置${NC}"
else
    echo -e "${YELLOW}⚠️  请编辑 .env 文件，填入你的 SILICONFLOW_API_KEY${NC}"
    echo -e "${YELLOW}   注册: https://cloud.siliconflow.cn/${NC}"
fi

# ── 4. 安装 Python 依赖 ──
echo ""
echo "📦 安装 Python 依赖..."
$PYTHON -m pip install --upgrade pip -q 2>/dev/null || true
$PYTHON -m pip install requests -q 2>/dev/null && echo -e "${GREEN}✅ requests 已安装${NC}" || echo -e "${YELLOW}⚠️  requests 安装失败（不影响核心功能）${NC}"

# ── 5. 检查输出目录 ──
mkdir -p output/posts output/images
echo -e "${GREEN}✅ 输出目录已准备: output/posts/ output/images/${NC}"

# ── 6. 验证运行 ──
echo ""
echo -e "${GREEN}══════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ 环境配置完毕！${NC}"
echo ""
echo "  🚀 快速体验："
echo "    $PYTHON agent.py --topic \"好用的护手霜推荐\" --interactive"
echo ""
echo "  📝 更多用法："
echo "    $PYTHON agent.py --topic \"周末咖啡馆探店\" --platform xiaohongshu --images 2"
echo "    $PYTHON agent.py --topic \"护手霜推荐\" --platform wechat --style tech"
echo "    $PYTHON agent.py --interactive"
echo ""
echo -e "${GREEN}══════════════════════════════════════════${NC}"
echo ""
