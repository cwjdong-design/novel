#!/usr/bin/env bash
# novel_step.sh — 小说创作流程锁 + 进度更新 + 产出物校验 + 骨架数字验证
# 用法:
#   novel_step.sh check <步骤名> [书名]     — 检查能否进入（不修改）
#   novel_step.sh done <步骤名> [书名]      — 标记步骤完成 + 产出物校验 + 自动推进
#   novel_step.sh validate <书名> [章节]     — 验证骨架数字（结算/违禁/地名/面板）
# 步骤: PREP PLOT DRAFT REVIEW POLISH TRACK MILESTONE BACKUP

set -euo pipefail

ACTION="${1:-}"
STEP="${2:-}"
BOOK_NAME="${3:-}"
STATE_DIR="${HOME}/.hermes/skills/novel/_state"
BOOKS_DIR="${HOME}/novels/books"

# === 帮助 ===
if [ -z "$ACTION" ] || [ "$ACTION" = "-h" ] || [ "$ACTION" = "--help" ]; then
    echo "用法: novel_step.sh <check|done|validate> <步骤名> [书名]"
    echo ""
    echo "  check PREP    — 检查能否进入 PREP"
    echo "  done  PREP    — 标记 PREP 完成，推进到下一步"
    echo "  validate 书名 [章节] — 验证骨架数字(结算/违禁/地名/面板)"
    echo ""
    echo "步骤: PREP PLOT DRAFT REVIEW POLISH TRACK MILESTONE BACKUP"
    echo ""
    echo "产出物校验（done 时强制执行）:"
    echo "  done PLOT   → 检查 00-大纲细纲/剧情推演/第N章.md 存在"
    echo "  done DRAFT  → 验证骨架数字 + 检查章节骨架文件存在"
    echo "  done REVIEW → 检查 05-审查报告/审查报告_第N章.md 存在"
    echo "  done POLISH → 检查 01-正文存稿/第N章.md 存在"
    exit 1
fi

# === validate 模式 ===
if [ "$ACTION" = "validate" ]; then
    [ -z "${STEP:-}" ] && echo "❌ validate 需要书名" && exit 2
    BOOK_NAME="$STEP"
    CHAPTER="${3:-}"

    if [ -z "$CHAPTER" ]; then
        if [ -f "${STATE_DIR}/current_book.txt" ] && [ "$(cat "${STATE_DIR}/current_book.txt")" = "$BOOK_NAME" ]; then
            if [ -f "${STATE_DIR}/${BOOK_NAME}_progress.json" ]; then
                CHAPTER=$(python3 -c "import json;print(json.load(open('${STATE_DIR}/${BOOK_NAME}_progress.json')).get('current_chapter',0))")
            fi
        fi
        [ -z "$CHAPTER" ] && echo "❌ 未指定章节号" && exit 2
    fi

    SKEL="${BOOKS_DIR}/${BOOK_NAME}/00-大纲细纲/章节骨架/第${CHAPTER}章_骨架.md"
    if [ ! -f "$SKEL" ]; then
        echo "🔴 骨架文件不存在: $SKEL"
        exit 1
    fi

    python3 - "$SKEL" "$CHAPTER" << 'PYEOF'
import re, sys
skel_path = sys.argv[1]
ch = sys.argv[2]
with open(skel_path) as f: t = f.read()
errors = []

# 1. 结算公式校验
pop_match = re.search(r'安居乐业人口[：:]\s*([\d,，]+)', t)
coef_match = re.search(r'幸福系数[：:]\s*([\d.]+)', t)
settle_match = re.search(r'昨日结算[：:]\s*[¥￥]\s*([\d,，]+)', t)
if pop_match and coef_match and settle_match:
    pop = int(re.sub(r'[,，]', '', pop_match.group(1)))
    coef = float(coef_match.group(1))
    settle = int(re.sub(r'[,，]', '', settle_match.group(1)))
    expected = round(pop * coef * 0.10)
    if settle != expected:
        errors.append(f'🔴 结算数字错误: 面板={settle:,}, 公式={pop}×{coef}×0.10={expected:,}')
    else:
        print(f'✅ 结算验证: {pop}×{coef}×0.10={expected:,} 匹配')
else:
    missing = []
    if not pop_match: missing.append('人口')
    if not coef_match: missing.append('系数')
    if not settle_match: missing.append('结算')
    if missing: errors.append(f'⚠️ 面板不完整: 缺{",".join(missing)}')

PYEOF
    # 违禁词/地名/面板字段检查委托给 review_scan.py（从书配置读取）
    SCAN_SCRIPT="${HOME}/.hermes/skills/novel/scripts/review_scan.py"
    if [ -f "$SCAN_SCRIPT" ]; then
        python3 "$SCAN_SCRIPT" "$SKEL" --book "$BOOK_NAME" || exit 1
    else
        echo "⚠️  review_scan.py 不存在，跳过违禁词/地名检查"
    fi
    exit 0
fi

# 大写
STEP=$(echo "$STEP" | tr '[:lower:]' '[:upper:]')
VALID_STEPS=("PREP" "PLOT" "DRAFT" "REVIEW" "POLISH" "TRACK" "MILESTONE" "BACKUP")
if ! printf '%s\n' "${VALID_STEPS[@]}" | grep -qx "$STEP"; then
    echo "❌ 无效步骤: $STEP  有效: ${VALID_STEPS[*]}"
    exit 2
fi

# 获取书名
if [ -z "$BOOK_NAME" ]; then
    if [ -f "${STATE_DIR}/current_book.txt" ]; then
        BOOK_NAME=$(cat "${STATE_DIR}/current_book.txt")
    else
        echo "❌ 未指定书名且 ${STATE_DIR}/current_book.txt 不存在"
        exit 2
    fi
fi

PROGRESS_FILE="${STATE_DIR}/${BOOK_NAME}_progress.json"
BOOK_DIR="${BOOKS_DIR}/${BOOK_NAME}"
mkdir -p "$STATE_DIR"

# 确保进度文件存在
if [ ! -f "$PROGRESS_FILE" ]; then
    if [ "$ACTION" = "check" ] && [ "$STEP" = "PREP" ]; then
        echo "✅ PASS: 可以进入 PREP (新章节，无前置依赖)"
        exit 0
    fi
    echo "⚠️  进度文件不存在: ${PROGRESS_FILE}"
    echo "   请先执行 novel_step.sh done PREP 创建进度文件"
    exit 1
fi

# === 核心逻辑 ===
python3 - "$PROGRESS_FILE" "$STEP" "$ACTION" "$BOOK_NAME" "$BOOK_DIR" << 'PYEOF'
import json, sys, os

progress_file = sys.argv[1]
target_step = sys.argv[2]
action = sys.argv[3]
book_name = sys.argv[4]
book_dir = sys.argv[5]

ALL_STEPS = ["PREP", "PLOT", "DRAFT", "REVIEW", "POLISH", "TRACK", "MILESTONE", "BACKUP"]

with open(progress_file) as f:
    data = json.load(f)

steps_completed = set(s.lower() for s in data.get("steps_completed", []))
current_chapter = data.get("current_chapter", 0)
milestone_blocked = data.get("milestone_blocked", False)

# === 产出物校验 ===
def check_artifact(step, chapter):
    """检查步骤产出物是否存在。返回 (ok: bool, msg: str)"""
    artifacts = {
        "PLOT": f"{book_dir}/00-大纲细纲/剧情推演/第{chapter}章.md",
        "DRAFT": f"{book_dir}/00-大纲细纲/章节骨架/第{chapter}章_骨架.md",
        "REVIEW": f"{book_dir}/05-审查报告/审查报告_第{chapter}章.md",
        "POLISH": f"{book_dir}/01-正文存稿/第{chapter}章.md",
    }
    path = artifacts.get(step)
    if not path:
        return True, ""  # 不需要校验的步骤
    
    if not os.path.exists(path):
        return False, f"📄 产出物缺失: {path}"
    
    if step == "PLOT":
        size = os.path.getsize(path)
        if size < 200:
            return False, f"📄 产出物过小({size}字节): {path} (需>200字节)"
    
    return True, ""

# === CHECK 模式 ===
if action == "check":
    if milestone_blocked:
        print(f"🛑 MILESTONE_BLOCKED: 第{current_chapter}章里程碑未通过")
        sys.exit(1)

    if target_step == "MILESTONE" and current_chapter % 5 != 0:
        print(f"⏭️  SKIP: 第{current_chapter}章非5的倍数，跳过 MILESTONE → BACKUP")
        sys.exit(0)

    target_idx = ALL_STEPS.index(target_step)
    prerequisites = [s.lower() for s in ALL_STEPS[:target_idx]]
    missing = [p.upper() for p in prerequisites if p not in steps_completed]
    completed = [p.upper() for p in prerequisites if p in steps_completed]

    if missing:
        print(f"⚠️  BLOCKED: 缺少前置步骤 {' → '.join(missing)}")
        if completed:
            print(f"   已完成: {' → '.join(completed)}")
        sys.exit(1)
    else:
        print(f"✅ PASS: 可以进入 {target_step}")
        print(f"   已完成: {' → '.join(completed)}" if completed else "   新章节开始")
        sys.exit(0)

# === DONE 模式 ===
elif action == "done":
    # 1. 前置检查（MILESTONE 对非5章自动豁免）
    target_idx = ALL_STEPS.index(target_step)
    prerequisites = [s.lower() for s in ALL_STEPS[:target_idx]]
    if target_step == "BACKUP" and current_chapter % 5 != 0:
        prerequisites = [p for p in prerequisites if p != "milestone"]
    missing = [p.upper() for p in prerequisites if p not in steps_completed]
    if missing and target_step != "PREP":
        print(f"⚠️  无法标记: 前置步骤未完成 {' → '.join(missing)}")
        sys.exit(1)

    # 2. 产出物校验
    ok, msg = check_artifact(target_step, current_chapter)
    if not ok:
        print(f"🛑 产出物校验失败: {msg}")
        print(f"   请先完成 {target_step} 的实际工作，生成对应的产出物。")
        print(f"   PLOT  → 00-大纲细纲/剧情推演/第{current_chapter}章.md")
        print(f"   DRAFT  → 00-大纲细纲/章节骨架/第{current_chapter}章_骨架.md")
        print(f"   REVIEW → 05-审查报告/审查报告_第{current_chapter}章.md")
        print(f"   POLISH → 01-正文存稿/第{current_chapter}章.md")
        sys.exit(1)

    # 2.5 DRAFT 骨架数字验证（不可跳过）
    if target_step == "DRAFT":
        import re, subprocess
        skel_path = f"{book_dir}/00-大纲细纲/章节骨架/第{current_chapter}章_骨架.md"
        with open(skel_path) as f: t = f.read()
        verrors = []
        pop_match = re.search(r'安居乐业人口[：:]\s*([\d,，]+)', t)
        coef_match = re.search(r'幸福系数[：:]\s*([\d.]+)', t)
        settle_match = re.search(r'昨日结算[：:]\s*[¥￥]\s*([\d,，]+)', t)
        if pop_match and coef_match and settle_match:
            pop = int(re.sub(r'[,，]', '', pop_match.group(1)))
            coef = float(coef_match.group(1))
            settle = int(re.sub(r'[,，]', '', settle_match.group(1)))
            expected = round(pop * coef * 0.10)
            if settle != expected:
                verrors.append(f'结算: 面板={settle:,}, 公式={pop}×{coef}×0.10={expected:,}')
        # 违禁词/地名/面板检查委托给 review_scan.py
        scan_script = os.path.expanduser('~/.hermes/skills/novel/scripts/review_scan.py')
        if os.path.exists(scan_script):
            result = subprocess.run(
                ['python3', scan_script, skel_path, '--book', book_name],
                capture_output=True, text=True
            )
            if result.returncode != 0:
                verrors.append(f'review_scan: {result.stdout.strip() or result.stderr.strip()}')
        if verrors:
            msg = ' | '.join(verrors)
            print(f'🛑 骨架数字验证失败: {msg}')
            print(f'   请修正 00-大纲细纲/章节骨架/第{current_chapter}章_骨架.md 后重新提交')
            sys.exit(1)

    # 3. 添加当前步骤
    steps_completed.add(target_step.lower())

    if target_step == "BACKUP" and current_chapter % 5 != 0:
        steps_completed.add("milestone")

    data["steps_completed"] = sorted(steps_completed,
        key=lambda s: [x.lower() for x in ALL_STEPS].index(s) if s in [x.lower() for x in ALL_STEPS] else 99)

    status_map = {
        "PREP": "prep_completed", "PLOT": "plot_completed",
        "DRAFT": "draft_completed", "REVIEW": "review_completed",
        "POLISH": "polish_completed", "TRACK": "track_completed",
        "MILESTONE": "milestone_completed", "BACKUP": "completed",
    }
    data["status"] = status_map.get(target_step, "completed")
    data["current_step"] = target_step.lower()

    # 4. 章节号进阶
    if target_step == "BACKUP":
        data["current_chapter"] = current_chapter + 1
        data["steps_completed"] = []
        data["status"] = "idle"
        data["current_step"] = "idle"
        data["milestone_blocked"] = False
        print(f"✅ BACKUP 完成 → 第{current_chapter}章已归档。下一章: 第{current_chapter+1}章")

    # 5. 保存
    with open(progress_file, 'w') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    # 6. 输出
    try:
        next_idx = target_idx + 1
        if next_idx < len(ALL_STEPS):
            next_s = ALL_STEPS[next_idx]
            if next_s == "MILESTONE" and data.get("current_chapter", 0) % 5 != 0:
                next_s = "BACKUP (跳过MILESTONE)"
            print(f"✅ {target_step} 完成 → 下一步: {next_s}")
        else:
            print(f"✅ {target_step} 完成 → 全部完成!")
    except:
        print(f"✅ {target_step} 完成")

    sys.exit(0)
PYEOF
