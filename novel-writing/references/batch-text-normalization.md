# 批量全章文本统一工作流

**何时用**：全书已有章节的格式/术语/标点需要统一修改时。

## 标准流程

### 第1步：摸底
统计每章的现状，确认哪些章节已符合、哪些需要改。

```bash
# 统计双引号分布
cd 01-正文存稿/
for ch in 第*.md; do
  dq=$(grep -c '"' "$ch" 2>/dev/null || echo 0)
  jq=$(grep -c '「' "$ch" 2>/dev/null || echo 0)
  printf "%s: \"\"=%s  「」=%s\n" "$ch" "$dq" "$jq"
done
```

### 第2步：备份
受影响章节必须先备份，有回滚路径。

```bash
mkdir -p "03-版本备份/引号修复备份"
for f in 01-正文存稿/第*.md; do
  name=$(basename "$f")
  cp "$f" "03-版本备份/引号修复备份/${name%.md}_备份.md"
done
```

### 第3步：写 Python 替换脚本
用 `execute_code` 或本地脚本。优先非贪心正则，逐文件替换。

```python
import re
from pathlib import Path

SRC = Path("01-正文存稿")
SKIP = {"第X章.md"}  # 已正确的章节

def fix_quotes(text: str) -> str:
    """规则说明"""
    return re.sub(r'"([^"]*?)"', r'「\1」', text)

for f in sorted(SRC.glob("第*.md")):
    if f.name in SKIP: continue
    original = f.read_text(encoding="utf-8")
    fixed = fix_quotes(original)
    if original == fixed: continue
    print(f"{f.name}: {original.count('"')} → {fixed.count('"')}")
    f.write_text(fixed, encoding="utf-8")
```

### 第4步：验证
- 全量 grep 确认零残留
- 抽样看转换质量（边缘场景：嵌套引用、叙述中引号）
- 确认未改动的章节不受影响

### 第5步：三重锁定（防复发）
| 层 | 位置 | 改什么 |
|----|------|--------|
| 源头 | novel-skeleton 3条铁律 | 注入 opus 的 prompt 中约束输出 |
| 自检 | novel-draft 自检清单 | 生成前检查 |
| 拦截 | review_scan.py | DRAFT 后自动零容忍检测 |

### 第6步：边缘场景处理
- **嵌套引用**：对话中引用别人话时，外层用「」，内层用 `""`。但小说极少出现两层嵌套，偶尔出现的「他说「好」」可接受
- **叙述中引用的过去对话**：统一用「」保持全书一致
- **转义引号**：`\"` 在正则中不会被匹配，不影响

## 注意事项
- 脚本只改 `01-正文存稿/`，不改备份目录和历史版本
- 已发到番茄平台的章节需要用户手动去平台替换全文
- 确认替换后，用 `review_scan.py` 对所有修改过的章节重新扫描
