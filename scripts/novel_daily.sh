#!/usr/bin/env bash
# novel_daily.sh — 每日巡检组合脚本（novel-cron 的 no_agent 入口）
# 依次执行：违禁词扫描 → 伏笔提醒 → 章节统计 → AI味评分
# 用法: bash novel_daily.sh [--book <书名>] [--chapters N]
# 输出: 汇总报告到 stdout；有违禁词/超期伏笔时 exit 1（触发 cron 告警）

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BOOK=""
CHAPTERS=5
EXIT_CODE=0

# 解析参数（支持 --book <名> 和 --chapters <N>）
while [[ $# -gt 0 ]]; do
  case "$1" in
    --book) BOOK="${2:-}"; shift 2 ;;
    --chapters) CHAPTERS="${2:-5}"; shift 2 ;;
    *) shift ;;
  esac
done

echo "📋 每日巡检 — $(date '+%Y-%m-%d %H:%M')"
echo "═══════════════════════════════"

# 1. 违禁词扫描
echo ""
echo "【1/4】违禁词扫描..."
if python3 "$SCRIPT_DIR/novel_scan.py" --book "$BOOK" --chapters "$CHAPTERS"; then
  echo "  ✅ 无违禁词"
else
  echo "  ⚠️ 发现违禁词（exit $?）"
  EXIT_CODE=1
fi

# 2. 伏笔到期提醒
echo ""
echo "【2/4】伏笔到期提醒..."
if python3 "$SCRIPT_DIR/foreshadow_check.py" --book "$BOOK" --chapters "$CHAPTERS"; then
  echo "  ✅ 无超期伏笔"
else
  echo "  ⚠️ 发现超期伏笔"
  EXIT_CODE=1
fi

# 3. 章节统计
echo ""
echo "【3/4】章节统计..."
python3 "$SCRIPT_DIR/chapter_stats.py" --book "$BOOK" || EXIT_CODE=1

# 4. AI味评分
echo ""
echo "【4/4】AI味健康评分..."
python3 "$SCRIPT_DIR/ai_score.py" --book "$BOOK" --chapters "$CHAPTERS" || EXIT_CODE=1

echo ""
echo "═══════════════════════════════"
echo "巡检完成（exit code: $EXIT_CODE）"
exit $EXIT_CODE
