#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"

echo "=== linuxdo Skill 初始化 ==="

# Python 3
if ! command -v python3 &>/dev/null; then
    echo "错误: 需要 python3，请先安装"
    exit 1
fi
echo "python3: $(python3 --version)"

# Chromium
CHROMIUM="${CHROMIUM_PATH:-/usr/bin/chromium}"
if [ ! -x "$CHROMIUM" ]; then
    echo "错误: 找不到 chromium（$CHROMIUM）"
    echo "  Debian/Ubuntu: sudo apt install chromium"
    echo "  或设置环境变量 CHROMIUM_PATH 指向实际路径"
    exit 1
fi
echo "chromium: $($CHROMIUM --version 2>/dev/null | head -1)"

# Python 依赖
echo "检查 Python 依赖..."
MISSING=()
python3 -c "import playwright" 2>/dev/null || MISSING+=("playwright")
python3 -c "import playwright_stealth" 2>/dev/null || MISSING+=("playwright-stealth")

if [ ${#MISSING[@]} -gt 0 ]; then
    echo "安装: ${MISSING[*]}"
    pip install "${MISSING[@]}" --break-system-packages 2>/dev/null \
        || pip install "${MISSING[@]}"
else
    echo "依赖已就绪"
fi

# 验证：解析链接
echo "验证 parse_linuxdo_url ..."
OUT=$(python3 "$SCRIPT_DIR/parse_linuxdo_url.py" "https://linux.do/t/topic/1588286/5")
echo "$OUT" | python3 -c "import sys,json; d=json.load(sys.stdin); assert d['topic_id']==1588286"
echo "  OK"

# 验证：搜索脚本可调用
echo "验证 search_linuxdo ..."
python3 "$SCRIPT_DIR/search_linuxdo.py" --help > /dev/null
echo "  OK"

# 验证：fetch 脚本可导入（不发网络请求）
echo "验证 fetch_linuxdo_content ..."
python3 -c "import sys; sys.path.insert(0,'$SCRIPT_DIR'); import fetch_linuxdo_content"
echo "  OK"

echo ""
echo "初始化完成！"
echo ""
echo "快速开始："
echo "  python3 $SCRIPT_DIR/fetch_linuxdo_content.py \"https://linux.do/t/topic/1588286\" --pretty"
echo "  python3 $SCRIPT_DIR/search_linuxdo.py \"OpenAI\""
