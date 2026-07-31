---
name: novel-cron
description: 每日自动巡检 — 全量备份、违禁词扫描、伏笔到期提醒、章节统计、网络热榜监控、AI味健康评分
category: novel
---

# 每日自动巡检

> **所有 Python 脚本已提取到独立文件：** `~/.hermes/skills/novel/scripts/`
> 本文件只保留接口说明，不内嵌代码。修复 bug 请改 .py 文件。

## 触发

由 Hermes cron job 每日定时触发（建议 04:00 UTC+8），也可手动触发 `hermes cron run novel-cron`。

### Cron 配置建议

```yaml
# ~/.hermes/cron/novel-cron.yaml
jobs:
  - name: novel-daily-patrol
    skill: novel-cron
    schedule: "0 4 * * *"
    no_agent: true          # 纯脚本巡检，无需 LLM
    script: ~/.hermes/skills/novel/scripts/novel_daily.sh
    notify_on: error        # 仅在发现违禁词/伏笔超期时通知
```

## 巡检项清单

| # | 巡检项 | 脚本 | 调用方式 |
|---|--------|------|---------|
| 1 | 全量备份 | backup 逻辑（见 novel-backup） | 打包 01-正文存稿/02-设定文档/00-大纲细纲 |
| 2 | 违禁词扫描 | `novel_scan.py` | `python3 ~/.hermes/skills/novel/scripts/novel_scan.py [--book <书名>] [--chapters N]` |
| 3 | 伏笔到期提醒 | `foreshadow_check.py` | `python3 ~/.hermes/skills/novel/scripts/foreshadow_check.py [--book <书名>] [--chapters N]` |
| 4 | 章节统计 | `chapter_stats.py` | `python3 ~/.hermes/skills/novel/scripts/chapter_stats.py [--book <书名>]` |
| 5 | 网络热榜 | `trending_news.py` | `python3 ~/.hermes/skills/novel/scripts/trending_news.py` |
| 6 | AI味健康评分 | `ai_score.py` | `python3 ~/.hermes/skills/novel/scripts/ai_score.py [--book <书名>]` |

> ⚠️ OOC 角色一致性检测**不在 cron 中运行**（需要人物库上下文，由 REVIEW 步骤人工执行）。

## 一、全量备份

### 1.1 备份范围

```
~/novels/books/
  ├── <book1>/
  │   ├── 01-正文存稿/       ← 打包
  │   ├── 02-设定文档/       ← 打包
  │   └── 00-大纲细纲/       ← 打包
  └── <book2>/...
```

### 1.2 备份命令（简化版）

```bash
#!/bin/bash
# 由 novel-cron 调用，完整逻辑见 novel-backup 技能
NOVEL_ROOT="$HOME/novels"
BACKUP_DIR="$NOVEL_ROOT/_shared/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M)
KEEP_DAYS=7

mkdir -p "$BACKUP_DIR"

for book_dir in "$NOVEL_ROOT"/books/*/; do
  book_name=$(basename "$book_dir")
  tar -czf "$BACKUP_DIR/${book_name}_正文_${TIMESTAMP}.tar.gz" -C "$book_dir" 01-正文存稿/ 2>/dev/null || true
  tar -czf "$BACKUP_DIR/${book_name}_设定_${TIMESTAMP}.tar.gz" -C "$book_dir" 02-设定文档/ 2>/dev/null || true
  tar -czf "$BACKUP_DIR/${book_name}_大纲_${TIMESTAMP}.tar.gz" -C "$book_dir" 00-大纲细纲/ 2>/dev/null || true
done

# 清理超过 KEEP_DAYS 天的备份
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +$KEEP_DAYS -delete

echo "备份完成: $(ls "$BACKUP_DIR"/*${TIMESTAMP}* 2>/dev/null | wc -l) 个文件"
du -sh "$BACKUP_DIR"
```

### 1.3 备份验证

```
1. tar -tzf <file> | head -5   # 抽查每个 tar.gz 可读
2. 检查每个 tar.gz 大小 > 1KB（不为空）
3. 检查备份目录总大小 < 500MB（如超过则告警）
```

## 二、违禁词扫描

> 脚本：`~/.hermes/skills/novel/scripts/novel_scan.py`
> 用法：`python3 novel_scan.py --book <书名> [--chapters 5]`

违禁词库存储在 `knowledge/违禁词库.json`，结构：

```json
{
  "version": "2.0",
  "categories": {
    "political": {"level": 1, "words": [...]},
    "sexual": {"level": 1, "words": [...], "context_patterns": [...]},
    "violence": {"level": 1, "words": [...]},
    "platform_special": {"level": 1, "real_brands": [...], "real_cities": [...], "banned_relationships": [...]},
    "writing_style": {"level": 2, "words": [...], "patterns": [...]},
    "ai_signature": {"level": 2, "words": [...], "patterns": [...]}
  }
}
```

> 完整词表见 `knowledge/违禁词库.json`。一级命中 exit code 1（触发 cron 告警）。

## 三、伏笔到期提醒

> 脚本：`~/.hermes/skills/novel/scripts/foreshadow_check.py`
> 用法：`python3 foreshadow_check.py [--book <书名>] [--chapters 30]`

数据源：`02-设定文档/伏笔追踪表.md`

检查逻辑：
1. **超期检测**：计划回收章 ≤ 当前最新章 且 未回收 → 超期
2. **遗忘检测**：铺垫章数超过阈值仍未回收 → 可能被遗忘
3. 按超期程度分级：🟡轻度(1-3章) / 🟠中度(4-7章) / 🔴重度(8-15章) / 💀严重(>15章)

> 完整算法见脚本文件，本文件不内嵌。

## 四、章节统计

> 脚本：`~/.hermes/skills/novel/scripts/chapter_stats.py`
> 用法：`python3 chapter_stats.py [--book <书名>]`

统计维度：总字数、均字、7天更新、断更天数、字数趋势、更新时段。
断更超过阈值 → exit code 1（触发告警）。

## 五、网络热榜话题监控

> 脚本：`~/.hermes/skills/novel/scripts/trending_news.py`
> 用法：`python3 trending_news.py`

数据源：RSS 源（知乎日报/36氪），`feedparser` 解析。
无 feedparser 时优雅降级，提示用 web_search 替代。

## 六、AI味健康评分

> 脚本：`~/.hermes/skills/novel/scripts/ai_score.py`
> 用法：`python3 ai_score.py [--book <书名>] [--chapters N]`

8 维加权评分：模板句式(25%)、AI连接词(20%)、成语密度(15%)、排比密度(15%)、抽象表达(10%)、冗余(10%)、被动语态(5%)、陈词滥调(0%)。

评分 > 阈值 → 该章需 polish 去 AI 味。

## 综合输出格式

巡检完成后汇总为一份报告：

```markdown
## 一、备份状态
✅ 备份完成：N 本书，共 X MB

## 二、违禁词扫描
✅ 所有书籍未发现违禁词/禁用词。  # 或列出命中

## 三、🚨 伏笔提醒
- 超期未回收：N 条（列出）
- 可能被遗忘：N 条（列出）

## 四、章节统计
- 总字数 / 均字 / 断更天数 / 更新状态

## 五、AI味评分
- 各书 AI 味得分（>阈值标记需处理）
```

## 日志位置

巡检日志写入 `~/novels/_shared/logs/`：
- 违禁词扫描：`违禁词扫描_YYYYMMDD.md`
- 伏笔提醒：`伏笔提醒_YYYYMMDD.md`
- 其他：`巡检日志_YYYYMMDD.md`

## 注意事项

- **脚本与技能分离**：所有 Python 脚本已提取到 `scripts/`，修复 bug 应改 .py 文件，不改本文件
- **cron 未启用**：当前 Hermes cron 无 novel job（如需启用，按上文配置，且必须 pin model）
- **OOC 检测**：不在 cron 运行，由 REVIEW 步骤人工执行
