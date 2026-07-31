#!/usr/bin/env bash
# novel_check.sh — 小说创作流程锁
# 用法: novel_check.sh <步骤名> [书名]
# 步骤: PREP PLOT DRAFT REVIEW POLISH TRACK MILESTONE BACKUP

set -euo pipefail

STEP="${1:-}"
BOOK_NAME="${2:-}"
STATE_DIR="${HOME}/.hermes/skills/novel/_state"

# === 帮助 ===
if [ -z "$STEP" ] || [ "$STEP" = "-h" ] || [ "$STEP" = "--help" ]; then
    echo "用法: novel_check.sh <步骤名> [书名]"
    echo "步骤: PREP PLOT DRAFT REVIEW POLISH TRACK MILESTONE BACKUP"
    echo "不传书名则从 ${STATE_DIR}/current_book.txt 读取"
    exit 1
fi

# 大写
STEP=$(echo "$STEP" | tr '[:lower:]' '[:upper:]')

# 验证步骤名
VALID_STEPS=("PREP" "PLOT" "DRAFT" "REVIEW" "POLISH" "TRACK" "MILESTONE" "BACKUP")
if ! printf '%s\n' "${VALID_STEPS[@]}" | grep -qx "$STEP"; then
    echo "❌ 无效步骤: $STEP"
    echo "有效步骤: ${VALID_STEPS[*]}"
    exit 2
fi

# === 获取书名 ===
if [ -z "$BOOK_NAME" ]; then
    if [ -f "${STATE_DIR}/current_book.txt" ]; then
        BOOK_NAME=$(cat "${STATE_DIR}/current_book.txt")
    else
        echo "❌ 未指定书名且 ${STATE_DIR}/current_book.txt 不存在"
        exit 2
    fi
fi

PROGRESS_FILE="${STATE_DIR}/${BOOK_NAME}_progress.json"

if [ ! -f "$PROGRESS_FILE" ]; then
    echo "⚠️ 进度文件不存在: ${PROGRESS_FILE}"
    echo "   可能还未开始创作，请先执行 novel-new-book"
    exit 1
fi

# === 用 Python 解析 JSON ===
RESULT=$(python3 - "$PROGRESS_FILE" "$STEP" "$STATE_DIR" "$BOOK_NAME" << 'PYEOF'
import json, sys

progress_file = sys.argv[1]
target_step = sys.argv[2]
state_dir = sys.argv[3]
book_name = sys.argv[4]

with open(progress_file) as f:
    data = json.load(f)

ALL_STEPS = ["PREP", "PLOT", "DRAFT", "REVIEW", "POLISH", "TRACK", "MILESTONE", "BACKUP"]
steps_completed = set(s.lower() for s in data.get("steps_completed", []))
current_chapter = data.get("current_chapter", 0)
milestone_blocked = data.get("milestone_blocked", False)

# 1. 检查 MILESTONE 阻塞
if milestone_blocked:
    print(f"🛑 MILESTONE_BLOCKED: 第{current_chapter}章里程碑审查未通过")
    print(f"   请先修正阻塞问题后再继续。阻塞报告见 00-大纲细纲/里程碑审查_第{current_chapter}章.md")
    sys.exit(1)

# 2. MILESTONE 只在5的倍数章执行
if target_step == "MILESTONE" and current_chapter % 5 != 0:
    print(f"⏭️  SKIP: 第{current_chapter}章不是5的倍数，跳过 MILESTONE")
    print(f"   下一步: BACKUP")
    sys.exit(0)

# 3. 找到目标步骤的索引
try:
    target_idx = ALL_STEPS.index(target_step)
except ValueError:
    print(f"❌ 未知步骤: {target_step}")
    sys.exit(2)

# 4. 检查前置步骤
prerequisites = [s.lower() for s in ALL_STEPS[:target_idx]]
missing = [p.upper() for p in prerequisites if p not in steps_completed]
completed = [p.upper() for p in prerequisites if p in steps_completed]

if missing:
    print(f"⚠️  BLOCKED: 不能进入 {target_step}")
    if missing:
        print(f"   缺少前置步骤: {' → '.join(missing)}")
    if completed:
        print(f"   已完成: {' → '.join(completed)}")
    else:
        print(f"   没有任何步骤完成。请从 PREP 开始。")
    sys.exit(1)
else:
    next_steps = ALL_STEPS[target_idx + 1:] if target_idx + 1 < len(ALL_STEPS) else []
    print(f"✅ PASS: 可以进入 {target_step}")
    print(f"   已完成: {' → '.join(completed)}")
    if target_step == "MILESTONE":
        print(f"   章节: 第{current_chapter}章 (是5的倍数)")
    print(f"   书籍: {book_name}")
    sys.exit(0)
PYEOF
)

echo "$RESULT"
exit $?
