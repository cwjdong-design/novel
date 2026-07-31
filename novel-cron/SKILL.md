---
name: novel-cron
description: 每日自动巡检 — 全量备份、违禁词扫描脚本、伏笔到期提醒、章节统计、网络热榜监控、AI味健康评分
category: novel
---

# 每日自动巡检

> **所有 Python 脚本已提取到独立文件：** `~/novels/_shared/scripts/` 下。
> - `novel_scan.py` — 违禁词扫描
> - `foreshadow_check.py` — 伏笔超期检测  
> - `chapter_stats.py` — 章节统计
> - `trending_news.py` — 热榜拉取
> - `ai_score.py` — AI味健康评分
>
> 本文件中的嵌入代码仅供文档参考，以独立 .py 文件为准。修复 bug 请改 .py 文件，不要改此 MD。

## 触发
由 Hermes cron job 每日定时触发（建议 04:00 UTC+8），也可手动触发 `hermes cron run novel-cron`。

### Cron 配置建议
```yaml
# ~/.hermes/cron/novel-cron.yaml
jobs:
  - name: novel-daily-patrol
    skill: novel-cron
    schedule: "0 4 * * *"
    no_agent: false         # 脚本已提取到 ~/novels/_shared/scripts/，可改为 no_agent: true 配合 script 参数使用
    notify_on: error        # 仅在发现违禁词/伏笔超期时通知
```

---

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

### 1.2 备份命令
```bash
#!/bin/bash
# novel-backup.sh — 由 novel-cron 调用

NOVEL_ROOT="$HOME/novels"
BACKUP_DIR="$NOVEL_ROOT/_shared/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M)
KEEP_DAYS=7

mkdir -p "$BACKUP_DIR"

for book_dir in "$NOVEL_ROOT"/books/*/; do
  book_name=$(basename "$book_dir")
  
  # 正文存稿打包
  tar -czf "$BACKUP_DIR/${book_name}_正文_${TIMESTAMP}.tar.gz" \
      -C "$book_dir" 01-正文存稿/ 2>/dev/null || true
  
  # 设定文档打包
  tar -czf "$BACKUP_DIR/${book_name}_设定_${TIMESTAMP}.tar.gz" \
      -C "$book_dir" 02-设定文档/ 2>/dev/null || true
  
  # 大纲打包
  tar -czf "$BACKUP_DIR/${book_name}_大纲_${TIMESTAMP}.tar.gz" \
      -C "$book_dir" 00-大纲细纲/ 2>/dev/null || true
done

# 清理超过 KEEP_DAYS 天的备份
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +$KEEP_DAYS -delete

# 输出统计
echo "备份完成: $(ls "$BACKUP_DIR"/*${TIMESTAMP}* 2>/dev/null | wc -l) 个文件"
du -sh "$BACKUP_DIR"
```

### 1.3 备份验证
```
备份后验证:
  1. tar -tzf <file> | head -5  # 抽查每个 tar.gz 可读
  2. 检查每个 tar.gz 大小 > 1KB（不为空）
  3. 检查备份目录总大小 < 500MB（如超过则告警）
```

---

## 二、违禁词扫描

> 脚本：`~/novels/_shared/scripts/novel_scan.py`
> 用法：`python3 novel_scan.py --book-dir <书籍目录> [--days 5]`
> 详细代码逻辑见脚本文件，此处仅列出配置和接口。
违禁词库存储在 `~/.hermes/skills/novel/knowledge/违禁词库.json`，内容结构：

```json
{
  "version": "2.0",
  "updated": "2026-07-24",
  "categories": {
    "political": {
      "level": 1,
      "words": ["政府", "中央", "国家领导人", "共产党", "共产主义", "解放军",
                "台湾", "香港", "西藏", "革命", "反革命", "上访", "维权", "抗议",
                "屠杀", "大屠杀", "分裂国家", "颠覆政权", "法轮功"]
    },
    "sexual": {
      "level": 1,
      "words": ["呻吟", "娇喘", "春药", "催情", "脱衣", "裸露", "交合", "云雨",
                "翻云覆雨", "强暴", "凌辱", "侵犯", "双修"],
      "context_patterns": ["胸.*形状", "大腿.*白皙", "臀部.*翘", "抚摸.*胸",
                           "揉捏.*腿", "床.*两人", "卧室.*独处"]
    },
    "violence": {
      "level": 1,
      "words": ["碎尸", "肢解", "分尸", "脑浆", "内脏", "肠子", "虐杀",
                "食人", "吃人", "活剥", "剥皮"]
    },
    "platform_special": {
      "level": 1,
      "real_brands": ["iPhone", "华为", "小米", "OPPO", "vivo",
                      "奔驰", "宝马", "奥迪", "特斯拉", "耐克", "阿迪达斯",
                      "星巴克", "麦当劳", "肯德基", "微信", "支付宝", "抖音",
                      "快手", "淘宝", "京东", "拼多多"],
      "real_cities": ["北京", "上海", "广州", "深圳", "成都", "重庆", "杭州",
                      "武汉", "南京", "西安", "长沙", "郑州"],
      "banned_relationships": ["未成年恋爱", "师生恋", "近亲",
                               "乱伦", "恋童"],
      "patterns": ["未成年\\.*恋爱"]
    },
    "writing_style": {
      "level": 2,
      "words": ["然而", "此外", "总而言之", "值得注意的是", "不可否认",
                "显而易见", "综上所述", "从某种意义上说", "毫无疑问"],
      "patterns": ["随着.*的发展", "在.*的过程中", "不仅.*而且",
                   "一方面.*另一方面"]
    },
    "ai_signature": {
      "level": 2,
      "words": ["不得不承认的是", "值得我们深思的是", "可以这么说",
                "不知不觉中", "时光荏苒", "岁月如梭", "弹指一挥间",
                "蓦然回首", "曾几何时", "沧海桑田", "时光飞逝",
                "光阴似箭", "犹如", "仿佛", "宛若"],
      "patterns": ["在这个充满\\.*的时代", "在这个瞬息万变的\\.*"]
    }
  }
}
```

### 2.2 扫描脚本实现
```python
#!/usr/bin/env python3
"""
novel_scan.py — 违禁词扫描脚本
用法: python3 novel_scan.py [--book <book_name>] [--chapters 5]
"""

import json
import re
import os
import sys
from pathlib import Path
from datetime import datetime

NOVEL_ROOT = Path(os.path.expanduser("~/novels"))
DICT_PATH = Path(os.path.expanduser("~/.hermes/skills/novel/knowledge/违禁词库.json"))
LOG_DIR = NOVEL_ROOT / "_shared" / "logs"


def load_dict():
    with open(DICT_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def scan_chapter(filepath: Path, word_dict: dict) -> list:
    """扫描单章，返回命中列表"""
    hits = []
    try:
        content = filepath.read_text(encoding='utf-8')
    except Exception as e:
        return [{"file": str(filepath), "error": str(e)}]
    
    lines = content.split('\n')
    
    for cat_name, cat_data in word_dict.get("categories", {}).items():
        level = cat_data.get("level", 1)
        
        # 收集该类别所有待匹配词（words + platform_special 子项）
        words = list(cat_data.get("words", []))
        # platform_special 类别有额外的词列表（real_brands、real_cities、banned_relationships）
        words.extend(cat_data.get("real_brands", []))
        words.extend(cat_data.get("real_cities", []))
        words.extend(cat_data.get("banned_relationships", []))
        
        # 收集正则模式（context_patterns + patterns）
        all_patterns = cat_data.get("context_patterns", []) + cat_data.get("patterns", [])
        
        # 合并为单次行遍历，避免重复循环
        for i, line in enumerate(lines, 1):
            # 精确词匹配
            for word in words:
                if word in line:
                    start = max(0, i - 2)
                    end = min(len(lines), i + 2)
                    context = '\n'.join(lines[start:end])
                    hits.append({
                        "file": str(filepath),
                        "line": i,
                        "category": cat_name,
                        "level": level,
                        "word": word,
                        "context": context[:200]
                    })
            
            # 正则模式匹配
            for pattern in all_patterns:
                if re.search(pattern, line):
                    start = max(0, i - 2)
                    end = min(len(lines), i + 2)
                    context = '\n'.join(lines[start:end])
                    hits.append({
                        "file": str(filepath),
                        "line": i,
                        "category": cat_name,
                        "level": level,
                        "word": f"[Pattern] {pattern}",
                        "context": context[:200]
                    })
    
    return hits


def scan_book(book_dir: Path, chapters: int = 5) -> list:
    """扫描一本书的最近 N 章"""
    draft_dir = book_dir / "01-正文存稿"
    if not draft_dir.exists():
        return []
    
    word_dict = load_dict()
    all_hits = []
    
    # 获取最近 N 章（按文件名排序）
    chapter_files = sorted(
        draft_dir.glob("第*章*.md"),
        key=lambda f: f.stat().st_mtime,
        reverse=True
    )[:chapters]
    
    for cf in chapter_files:
        hits = scan_chapter(cf, word_dict)
        all_hits.extend(hits)
    
    return all_hits


def generate_report(all_books_hits: dict) -> str:
    """生成扫描报告"""
    report_lines = [
        f"## 违禁词扫描报告 — {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        ""
    ]
    
    total_hits = 0
    for book_name, hits in all_books_hits.items():
        level1 = [h for h in hits if h.get("level") == 1]
        level2 = [h for h in hits if h.get("level") == 2]
        total_hits += len(hits)
        
        if hits:
            report_lines.append(f"### 📕 {book_name}")
            report_lines.append(f"一级命中: {len(level1)} | 二级命中: {len(level2)}")
            report_lines.append("")
            report_lines.append("| 级别 | 类别 | 文件 | 行号 | 命中词 | 上下文 |")
            report_lines.append("|------|------|------|------|--------|--------|")
            for h in hits:
                level_icon = "🔴" if h["level"] == 1 else "⚠️"
                fname = Path(h["file"]).name
                report_lines.append(
                    f"| {level_icon} | {h['category']} | {fname} | "
                    f"{h['line']} | `{h['word']}` | {h.get('context', '')[:50]}... |"
                )
            report_lines.append("")
        else:
            report_lines.append(f"### 📕 {book_name}: ✅ 未发现")
            report_lines.append("")
    
    if total_hits == 0:
        report_lines.insert(1, "✅ 所有书籍未发现违禁词/禁用词。")
    
    return '\n'.join(report_lines)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--book", help="指定书名，不指定则扫描全部")
    parser.add_argument("--chapters", type=int, default=5, help="扫描最近N章，默认5")
    args = parser.parse_args()
    
    books_dir = NOVEL_ROOT / "books"
    
    if args.book:
        book_dirs = [books_dir / args.book]
    else:
        book_dirs = sorted(books_dir.glob("*/"))
    
    all_hits = {}
    for book_dir in book_dirs:
        if not book_dir.is_dir() or book_dir.name.startswith("_"):
            continue
        book_name = book_dir.name
        hits = scan_book(book_dir, args.chapters)
        all_hits[book_name] = hits
    
    report = generate_report(all_hits)
    
    # 保存到日志
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_file = LOG_DIR / f"违禁词扫描_{datetime.now().strftime('%Y%m%d')}.md"
    log_file.write_text(report, encoding='utf-8')
    
    print(report)
    
    # 如果有一级命中，exit code 1 用于 cron 告警
    has_level1 = any(
        any(h.get("level") == 1 for h in hits)
        for hits in all_hits.values()
    )
    sys.exit(1 if has_level1 else 0)
```

---

## 三、伏笔到期提醒算法

### 3.1 数据结构（伏笔追踪表格式）
```
~/novels/books/<book>/02-设定文档/伏笔追踪表.md

| ID | 内容 | 铺垫章 | 计划回收章 | 实际回收章 | 状态 | 回收方式 | 回收质量 |
```

### 3.2 检查算法
```python
#!/usr/bin/env python3
"""
foreshadow_check.py — 伏笔到期提醒
"""

import os
import re
import sys
from pathlib import Path
from datetime import datetime

NOVEL_ROOT = Path(os.path.expanduser("~/novels"))


def parse_foreshadow_table(filepath: Path) -> list:
    """解析伏笔追踪表 Markdown 表格"""
    content = filepath.read_text(encoding='utf-8')
    foreshadows = []
    
    in_table = False
    for line in content.split('\n'):
        if line.startswith('| ID'):
            in_table = True
            continue
        if in_table and line.startswith('|') and '|' in line[1:]:
            # 跳过表头分隔行 (如 |------|------|------|)
            if re.match(r'^\|[\s\-:]+\|', line):
                continue
            cols = [c.strip() for c in line.split('|')[1:-1]]
            if len(cols) >= 8 and cols[0] and cols[0] != 'ID':
                foreshadows.append({
                    "id": cols[0],
                    "content": cols[1],
                    "plant_chapter": parse_chapter_num(cols[2]),
                    "recycle_chapter": parse_chapter_num(cols[3]),
                    "actual_chapter": parse_chapter_num(cols[4]),
                    "status": cols[5],
                    "method": cols[6] if len(cols) > 6 else "",
                    "quality": cols[7] if len(cols) > 7 else ""
                })
    return foreshadows


def parse_chapter_num(s: str) -> int:
    """从纯数字或'第X章'提取章节号，同步支持两种格式。
    
    支持输入: "5", "第5章", "第 5 章", "第5章 (计划)", " 5 "
    不支持: "第五章" (中文数字)
    """
    s = s.strip()
    if not s:
        return 0
    # 优先匹配 '第X章' 格式
    m = re.search(r'第\s*(\d+)\s*章', s)
    if m:
        return int(m.group(1))
    # 回退: 尝试作为纯数字解析
    try:
        return int(s)
    except ValueError:
        return 0


def get_latest_chapter(book_dir: Path) -> int:
    """获取该书最新章节号"""
    draft_dir = book_dir / "01-正文存稿"
    if not draft_dir.exists():
        return 0
    max_ch = 0
    for f in draft_dir.glob("第*章*.md"):
        ch = parse_chapter_num(f.name)
        if ch > max_ch:
            max_ch = ch
    return max_ch


def check_overdue(book_dir: Path) -> list:
    """检查超期伏笔"""
    table_path = book_dir / "02-设定文档" / "伏笔追踪表.md"
    if not table_path.exists():
        return []
    
    foreshadows = parse_foreshadow_table(table_path)
    latest_ch = get_latest_chapter(book_dir)
    
    overdue = []
    for fs in foreshadows:
        # 计划回收章 ≤ 当前最新章 且 状态不是「已回收」
        is_overdue = (
            fs["recycle_chapter"] > 0 and
            fs["recycle_chapter"] <= latest_ch and
            "已回收" not in fs["status"] and
            "✅" not in fs["status"]
        )
        if is_overdue:
            overdue.append({
                **fs,
                "overdue_by": latest_ch - fs["recycle_chapter"],
                "latest_chapter": latest_ch
            })
    
    return overdue


def check_abandoned(book_dir: Path, days_threshold: int = 30) -> list:
    """检查可能被遗忘的伏笔（铺垫章数超过阈值仍未回收）"""
    table_path = book_dir / "02-设定文档" / "伏笔追踪表.md"
    if not table_path.exists():
        return []
    
    foreshadows = parse_foreshadow_table(table_path)
    latest_ch = get_latest_chapter(book_dir)
    abandoned = []
    
    for fs in foreshadows:
        if "已回收" in fs["status"] or "✅" in fs["status"]:
            continue
        # 检查是否有明确回收计划
        if fs["recycle_chapter"] == 0:
            abandoned.append({
                **fs,
                "issue": "无计划回收章节",
                "age_days": "未知"
            })
        # 无 created 字段，改用铺垫章数作为替代判断
        elif fs.get("plant_chapter", 0) > 0:
            chapters_ago = latest_ch - fs["plant_chapter"]
            if chapters_ago > days_threshold:
                abandoned.append({
                    **fs,
                    "issue": f"铺垫 {chapters_ago} 章未回收",
                    "age_days": f"≈{chapters_ago}章"
                })
    
    return abandoned


def generate_reminder(overdue: dict, abandoned: dict) -> str:
    """生成提醒报告"""
    lines = [
        f"## 🚨 伏笔到期提醒 — {datetime.now().strftime('%Y-%m-%d')}",
        ""
    ]
    
    has_issues = False
    
    for book_name, items in overdue.items():
        if items:
            has_issues = True
            lines.append(f"### 📕 {book_name} — 超期未回收")
            lines.append("")
            lines.append("| 伏笔ID | 内容 | 铺垫章 | 计划回收章 | 超期 |")
            lines.append("|--------|------|--------|-----------|------|")
            for item in items:
                lines.append(
                    f"| {item['id']} | {item['content'][:30]} | "
                    f"第{item['plant_chapter']}章 | 第{item['recycle_chapter']}章 | "
                    f"🚨 +{item['overdue_by']}章 |"
                )
            lines.append("")
    
    for book_name, items in abandoned.items():
        if items:
            has_issues = True
            lines.append(f"### 📕 {book_name} — 可能被遗忘的伏笔")
            lines.append("")
            lines.append("| 伏笔ID | 内容 | 铺垫章 | 问题 |")
            lines.append("|--------|------|--------|------|")
            for item in items:
                lines.append(
                    f"| {item['id']} | {item['content'][:30]} | "
                    f"第{item['plant_chapter']}章 | {item.get('issue', '')} |"
                )
            lines.append("")
    
    if not has_issues:
        lines.append("✅ 所有伏笔状态正常，无超期或遗忘项。")
    
    return '\n'.join(lines)


if __name__ == "__main__":
    import argparse
    import sys
    
    parser = argparse.ArgumentParser(description="伏笔到期提醒")
    parser.add_argument("--book", help="指定书名，不指定则扫描全部")
    parser.add_argument("--days", type=int, default=30, help="遗忘检测阈值天数，默认30")
    args = parser.parse_args()
    
    books_dir = NOVEL_ROOT / "books"
    if args.book:
        book_dirs = [books_dir / args.book]
    else:
        book_dirs = sorted(books_dir.glob("*/"))
    
    overdue_all = {}
    abandoned_all = {}
    
    for book_dir in book_dirs:
        if not book_dir.is_dir() or book_dir.name.startswith("_"):
            continue
        book_name = book_dir.name
        overdue = check_overdue(book_dir)
        abandoned = check_abandoned(book_dir, args.days)
        if overdue:
            overdue_all[book_name] = overdue
        if abandoned:
            abandoned_all[book_name] = abandoned
    
    report = generate_reminder(overdue_all, abandoned_all)
    print(report)
    
    # 有超期伏笔时 exit code 1，用于 cron 告警
    has_overdue = any(len(items) > 0 for items in overdue_all.values())
    sys.exit(1 if has_overdue else 0)
```

### 3.3 告警阈值
| 场景 | 阈值 | 级别 |
|------|------|------|
| 计划回收章 = 当前章，未回收 | 恰好到期 | 🟡 提醒 |
| 计划回收章 < 当前章，超期 1-5 章 | 轻度超期 | 🟠 告警 |
| 计划回收章 < 当前章，超期 > 5 章 | 严重超期 | 🔴 紧急 |
| 无计划回收章节 + 创建 > 30 天 | 可能遗忘 | 🟡 提醒 |

---

## 四、章节统计

### 4.1 统计维度
| 指标 | 计算方式 |
|------|---------|
| 总章节数 | 正文存稿目录下 `第*章*.md` 文件数 |
| 总字数 | 所有章节文件字符数之和（含标点） |
| 最近7天更新频率 | 过去7天创建的章节文件数 |
| 今日是否更新 | 今天是否有新章节文件 |
| 断更天数 | 距离最后一个章节文件的修改日期过去了多少天 |
| 平均每章字数 | 总字数 ÷ 总章节数 |
| 字数趋势 | 最近7章字数列表，检查是否递减 |
| 更新时段分布 | 最近30天的更新时间段统计 |

### 4.2 统计脚本
```python
#!/usr/bin/env python3
"""chapter_stats.py"""

import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict

NOVEL_ROOT = Path(os.path.expanduser("~/novels"))


def count_chars(filepath: Path) -> int:
    """计算非空白字符数（含中文、英文、数字、标点、emoji等）"""
    text = filepath.read_text(encoding='utf-8')
    # 统计所有非空白字符（空格、换行、制表符不计入）
    return len([c for c in text if not c.isspace()])


def get_chapter_stats(book_dir: Path) -> dict:
    draft_dir = book_dir / "01-正文存稿"
    if not draft_dir.exists():
        return {"error": "无正文存稿目录"}
    
    chapter_files = sorted(draft_dir.glob("第*章*.md"))
    if not chapter_files:
        return {"error": "无章节文件"}
    
    total_chars = 0
    chapter_sizes = []
    chapter_times = []
    
    for cf in chapter_files:
        size = count_chars(cf)
        total_chars += size
        chapter_sizes.append(size)
        chapter_times.append(datetime.fromtimestamp(cf.stat().st_mtime))
    
    now = datetime.now()
    seven_days_ago = now - timedelta(days=7)
    thirty_days_ago = now - timedelta(days=30)
    
    # 最近7天更新
    recent_updates = [t for t in chapter_times if t > seven_days_ago]
    
    # 断更天数
    last_update = max(chapter_times)
    days_since_update = (now - last_update).days
    
    # 今日是否更新
    today_updated = last_update.date() == now.date()
    
    # 平均字数
    avg_chars = total_chars / len(chapter_files) if chapter_files else 0
    
    # 最近7章字数趋势
    recent_sizes = chapter_sizes[-7:] if len(chapter_sizes) >= 7 else chapter_sizes
    trend = "稳定"
    if len(recent_sizes) >= 3:
        if recent_sizes[-1] < recent_sizes[-2] < recent_sizes[-3]:
            trend = "⬇️ 递减"
        elif recent_sizes[-1] > recent_sizes[-2] > recent_sizes[-3]:
            trend = "⬆️ 递增"
    
    # 更新时段分布
    hour_dist = defaultdict(int)
    for t in chapter_times:
        if t > thirty_days_ago:
            hour_dist[t.hour] += 1
    peak_hour = max(hour_dist, key=hour_dist.get) if hour_dist else None
    
    return {
        "total_chapters": len(chapter_files),
        "total_chars": total_chars,
        "avg_chars_per_chapter": round(avg_chars, 0),
        "recent_7d_updates": len(recent_updates),
        "today_updated": today_updated,
        "days_since_update": days_since_update,
        "last_update": last_update.strftime("%Y-%m-%d %H:%M"),
        "size_trend": trend,
        "recent_chapter_sizes": recent_sizes,
        "peak_update_hour": peak_hour
    }


def generate_stats_report(all_stats: dict) -> str:
    lines = [
        f"## 📊 章节统计 — {datetime.now().strftime('%Y-%m-%d')}",
        "",
        "| 书名 | 章节数 | 总字数 | 均字 | 7天更新 | 更新状态 | 断更 | 字数趋势 |",
        "|------|--------|--------|------|---------|---------|------|---------|"
    ]
    
    for book_name, stats in all_stats.items():
        if "error" in stats:
            lines.append(f"| {book_name} | — | — | — | — | ⚠️ {stats['error']} | — | — |")
            continue
        
        update_status = "✅ 今日已更" if stats["today_updated"] else "⏸️"
        break_days = f"{stats['days_since_update']}天" if stats["days_since_update"] > 0 else "—"
        
        lines.append(
            f"| {book_name} | {stats['total_chapters']} | "
            f"{stats['total_chars']:,} | {stats['avg_chars_per_chapter']:.0f} | "
            f"{stats['recent_7d_updates']}章 | {update_status} | "
            f"{break_days} | {stats['size_trend']} |"
        )
    
    lines.append("")
    
    # 断更告警
    for book_name, stats in all_stats.items():
        if "error" in stats:
            continue
        if stats["days_since_update"] >= 3:
            lines.append(f"🚨 **{book_name}** 已断更 **{stats['days_since_update']}** 天！上次更新: {stats['last_update']}")
        elif stats["days_since_update"] >= 1:
            lines.append(f"🟡 **{book_name}** 断更 {stats['days_since_update']} 天，上次更新: {stats['last_update']}")
    
    return '\n'.join(lines)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="章节统计")
    parser.add_argument("--book", help="指定书名，不指定则统计全部")
    args = parser.parse_args()
    
    books_dir = NOVEL_ROOT / "books"
    if args.book:
        book_dirs = [books_dir / args.book]
    else:
        book_dirs = sorted(books_dir.glob("*/"))
    
    all_stats = {}
    for book_dir in book_dirs:
        if not book_dir.is_dir() or book_dir.name.startswith("_"):
            continue
        book_name = book_dir.name
        stats = get_chapter_stats(book_dir)
        all_stats[book_name] = stats
    
    report = generate_stats_report(all_stats)
    print(report)
    
    # 断更 >= 3 天时 exit code 1，用于 cron 告警
    has_long_break = any(
        s.get("days_since_update", 0) >= 3
        for s in all_stats.values() if "error" not in s
    )
    sys.exit(1 if has_long_break else 0)
```

---

## 五、网络热榜话题监控（🆕 修复版：RSS 方案）

> ⚠️ **已知限制**：微博/知乎/百度的官方热榜 API 和页面选择器均频繁变化，原 httpx+BeautifulSoup 方案已全线不可用。
> **修复方案**：改用 `feedparser` 拉取稳定 RSS 源（如知乎日报、36氪、少数派），获取当日热门主题作为创作素材。
> 如需真正的"热搜排行"，请在 **agent 模式**下使用 `web_search("今日微博热搜")` 或 `web_search("知乎热榜")` 手动获取。

### 5.1 数据源（RSS 方案）

| 源 | RSS URL | 可靠性 | 说明 |
|-----|-----|--------|------|
| 知乎每日精选 | `https://www.zhihu.com/rss` | ⭐⭐⭐ 稳定 | 知乎官方 RSS，无需认证 |
| 36氪快讯 | `https://36kr.com/feed` | ⭐⭐⭐ 稳定 | 科技/商业热点 |
| 少数派 | `https://sspai.com/feed` | ⭐⭐⭐ 稳定 | 科技/效率话题 |
| 澎湃新闻 | `https://www.thepaper.cn/feed` | ⭐⭐ 较稳定 | 时政社会热点 |
| 🔥 热搜排行 | — | ⚠️ 不稳定 | **无稳定公开 API**，建议 agent 模式下 `web_search("微博热搜")` |

### 5.2 拉取脚本（feedparser RSS 版）

依赖安装：`pip install feedparser`

```python
#!/usr/bin/env python3
"""
trending_news.py — 每日热榜拉取（RSS 版）
基于 feedparser 拉取稳定 RSS 源，不可用时标记 skip。
依赖: pip install feedparser
"""

import os
import re
import json
from pathlib import Path
from datetime import datetime, timezone, timedelta

try:
    import feedparser
except ImportError:
    feedparser = None

NOVEL_ROOT = Path(os.path.expanduser("~/novels"))
LOG_DIR = NOVEL_ROOT / "_shared" / "logs"
TREND_FILE = NOVEL_ROOT / "_shared" / "logs" / f"热榜_{datetime.now().strftime('%Y%m%d')}.json"

# 北京时间
TZ = timezone(timedelta(hours=8))

# RSS 源配置
RSS_SOURCES = [
    {
        "name": "知乎日报",
        "url": "https://www.zhihu.com/rss",
        "max_items": 15,
        "extract_heat": False,
    },
    {
        "name": "36氪",
        "url": "https://36kr.com/feed",
        "max_items": 15,
        "extract_heat": False,
    },
    {
        "name": "少数派",
        "url": "https://sspai.com/feed",
        "max_items": 10,
        "extract_heat": False,
    },
    {
        "name": "澎湃新闻",
        "url": "https://www.thepaper.cn/feed",
        "max_items": 10,
        "extract_heat": False,
    },
]


def fetch_rss(source: dict) -> list:
    """拉取单个 RSS 源，返回条目列表。失败返回带 error 的列表。"""
    name = source["name"]
    url = source["url"]
    max_items = source.get("max_items", 15)

    if feedparser is None:
        return [{"source": name, "error": "feedparser 未安装，请执行: pip install feedparser"}]

    try:
        feed = feedparser.parse(url)
        if feed.bozo and not feed.entries:
            return [{"source": name, "error": f"RSS 解析失败: {feed.bozo_exception}"}]

        items = []
        for i, entry in enumerate(feed.entries[:max_items], 1):
            # 提取纯文本标题（去除 HTML 标签）
            title = entry.get("title", "")
            # 简单 HTML 去标签
            title = re.sub(r'<[^>]+>', '', title).strip()

            if not title:
                continue

            items.append({
                "source": name,
                "title": title,
                "rank": i,
                "heat": "—",  # RSS 源通常无热度数据
                "url": entry.get("link", ""),
                "published": entry.get("published", ""),
            })
        return items
    except Exception as e:
        return [{"source": name, "error": str(e)}]


def match_to_novel_genre(hot_items: list, book_genres: dict) -> list:
    """
    将热榜话题匹配到小说类型，推荐可融入的热点。
    book_genres: {"书名": ["都市", "玄幻", "言情", ...]}
    """
    genre_keywords = {
        "都市": ["职场", "创业", "房价", "教育", "结婚", "AI", "科技", "社畜",
                 "相亲", "职场", "裁员", "内卷", "躺平", "副业", "外卖", "租房"],
        "玄幻": ["神话", "修仙", "道士", "易经", "太极", "武术", "古墓", "考古"],
        "言情": ["恋爱", "CP", "分手", "出轨", "闺蜜", "婆媳", "相亲", "婚姻"],
        "悬疑": ["案件", "失踪", "凶杀", "法医", "推理", "反转", "警方", "犯罪"],
        "科幻": ["AI", "人工智能", "太空", "火星", "机器人", "基因", "VR",
                 "元宇宙", "大模型"],
        "历史": ["考古", "文物", "古墓", "朝代", "皇帝", "战争", "丝绸之路"],
        "游戏": ["电竞", "手游", "主机", "战队", "冠军", "直播", "氪金", "外挂"],
    }

    suggestions = []
    for item in hot_items:
        if "error" in item:
            continue
        title = item.get("title", "")
        for book, genres in book_genres.items():
            for genre in genres:
                keywords = genre_keywords.get(genre, [])
                matched = [kw for kw in keywords if kw in title]
                if matched:
                    suggestions.append({
                        "book": book,
                        "genre": genre,
                        "hot_topic": title,
                        "matched_keywords": matched,
                        "rank": item.get("rank", 0),
                        "source": item.get("source", ""),
                        "suggestion": (
                            f"可融入{genre}元素：将《{title}》中的"
                            f"「{'/'.join(matched)}」关键词化用为剧情桥段"
                        )
                    })

    # 按 rank 排序
    suggestions.sort(key=lambda x: x["rank"])
    return suggestions[:15]


def generate_trend_report():
    """生成热榜报告"""
    all_items = []
    success_count = 0
    fail_count = 0

    for src in RSS_SOURCES:
        items = fetch_rss(src)
        all_items.extend(items)
        if items and "error" not in items[0]:
            success_count += 1
        else:
            fail_count += 1

    # 保存原始数据
    TREND_FILE.parent.mkdir(parents=True, exist_ok=True)
    raw_data = {
        "date": datetime.now(TZ).strftime("%Y-%m-%d"),
        "total_items": len(all_items),
        "sources_succeeded": success_count,
        "sources_failed": fail_count,
        "note": "RSS 源拉取，不含实时热搜排行。如需热搜排行，请在 agent 模式下使用 web_search。",
        "items": all_items,
    }
    TREND_FILE.write_text(json.dumps(raw_data, ensure_ascii=False, indent=2))

    # 生成 Markdown 报告
    lines = [
        f"## 🔥 网络热榜 — {datetime.now(TZ).strftime('%Y-%m-%d')}",
        "",
        f"数据源: {' / '.join(s['name'] for s in RSS_SOURCES)}（RSS 源，不含实时热搜排行）",
        f"拉取时间: {datetime.now(TZ).strftime('%H:%M')}",
        f"成功: {success_count}/{len(RSS_SOURCES)} | "
        f"如需实时热搜排行，请在 agent 模式下使用 `web_search(\"今日热搜\")`",
        "",
    ]

    # 按源分组显示
    source_groups = {}
    for item in all_items:
        src = item.get("source", "其他")
        if src not in source_groups:
            source_groups[src] = []
        source_groups[src].append(item)

    for src_name in [s["name"] for s in RSS_SOURCES]:
        items = source_groups.get(src_name, [])
        if not items:
            continue
        lines.append(f"### {src_name} TOP{min(10, len(items))}")
        lines.append("| 排名 | 标题 | 链接 |")
        lines.append("|------|------|------|")
        for item in items[:10]:
            if "error" in item:
                lines.append(f"| — | ⚠️ 拉取失败: {item['error']} | — |")
                continue
            title = item.get("title", "-")
            url = item.get("url", "")
            title_link = f"[{title}]({url})" if url else title
            lines.append(f"| {item.get('rank', '-')} | {title_link} |")
        lines.append("")

    if success_count == 0:
        lines.insert(2, "⚠️ 所有 RSS 源拉取失败。请在 agent 模式下使用 `web_search` 获取热榜数据。")
        lines.insert(3, "   示例: web_search('今日微博热搜') / web_search('知乎热榜')")
        lines.insert(4, "")

    return '\n'.join(lines)


if __name__ == "__main__":
    report = generate_trend_report()
    print(report)
    
    # 保存 Markdown 报告到日志目录
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    report_file = LOG_DIR / f"热榜_{datetime.now(TZ).strftime('%Y%m%d')}.md"
    report_file.write_text(report, encoding='utf-8')
```

### 5.3 Agent 模式补充（有 LLM 时）
```
当 cron 以 no_agent=false 运行时，额外执行:
  1. web_search("今日微博热搜") → 补全实时热搜排行
  2. web_search("知乎热榜") → 补全知乎热榜
  3. 将 web_search 结果与 RSS 结果合并输出
```

### 5.4 融入热点建议
```
基于热榜拉取结果 + 各书类型标签 → 生成建议：
  - 都市文：热点社会事件可转化为剧情冲突
  - 玄幻/仙侠文：考古发现/神话传说可作为世界观测材料
  - 言情文：情感类热搜可作为人物互动灵感
  - 科幻文：科技新闻/太空探索可丰富未来设定
```

---

## 六、AI味健康评分（🆕 新增）

### 6.1 什么是「AI味」
AI写作的典型特征：
- 过度使用「不仅……而且」「一方面……另一方面」等模板句式
- 滥用「然而」「此外」「总而言之」等书面连接词
- 大量使用「仿佛」「犹如」「宛若」等比喻套话
- 心理描写采用「他心想」「他意识到」等生硬表达
- 环境描写用「阳光洒在」「微风拂过」等模板开头
- 对话开头高频使用「XXX道：」
- 段落结尾习惯性总结/升华
- 成语堆砌（连续使用 ≥3 个成语在一个自然段）

### 6.2 评分算法
```python
import os
import re
from pathlib import Path

def ai_score(text: str) -> dict:
    """
    返回 AI味评分 (0-100，越低越好) 和各维度得分
    """
    scores = {}
    
    # 1. 模板句式密度 (权重 25%)
    template_patterns = [
        r'不仅.{1,20}而且', r'一方面.{1,20}另一方面',
        r'随着.{1,30}的发展', r'在.{1,30}的过程中',
        r'更重要的是', r'除此之外',
        r'从某种意义上说', r'不可否认的是',
        r'值得.{1,10}的是', r'可以这么说',
    ]
    template_count = sum(len(re.findall(p, text)) for p in template_patterns)
    # 每1000字模板句数
    chars = len([c for c in text if not c.isspace()])
    density = template_count / max(chars / 1000, 1)
    scores["template_sentence"] = min(100, density * 40)  # 密度>2.5/千字=满100
    
    # 2. AI连接词密度 (权重 20%)
    ai_connectors = [
        '然而', '此外', '总而言之', '值得注意的是', '不可否认',
        '显而易见', '综上所述', '从某种意义上说', '毫无疑问',
        '不仅如此', '更为重要的是', '需要指出的是'
    ]
    connector_count = sum(text.count(w) for w in ai_connectors)
    density2 = connector_count / max(chars / 1000, 1)
    scores["ai_connector"] = min(100, density2 * 30)
    
    # 3. 比喻套话密度 (权重 15%)
    cliche_metaphors = [
        '仿佛', '犹如', '宛若', '仿佛.*一般', '如同.*一样',
        '像.*似的', '恍若'
    ]
    metaphor_count = sum(len(re.findall(p, text)) for p in cliche_metaphors)
    density3 = metaphor_count / max(chars / 1000, 1)
    scores["cliche_metaphor"] = min(100, density3 * 20)
    
    # 4. 「XXX道」对话引导比例 (权重 10%)
    dialogue_lines = re.findall(r'[「「"](.+?)[」」"]', text)
    xxx_dao = len(re.findall(r'.{1,4}道[：:].{0,10}[「「"]', text))
    dao_ratio = xxx_dao / max(len(dialogue_lines), 1)
    scores["dialogue_dao"] = min(100, dao_ratio * 200)  # >50%的话用「道」=满100
    
    # 5. 「心想」「意识到」「觉得」心理描写密度 (权重 10%)
    mental_words = ['心想', '暗想', '心道', '意识到', '觉得', '认为', 
                    '感到', '感觉到', '觉察到', '不禁想']
    mental_count = sum(text.count(w) for w in mental_words)
    density5 = mental_count / max(chars / 1000, 1)
    scores["mental_telling"] = min(100, density5 * 25)
    
    # 6. 环境描写模板 (权重 10%)
    env_templates = [
        '阳光洒', '阳光透过', '阳光照',
        '微风拂', '微风轻拂', '清风吹',
        '天空.*蓝', '万里无云',
        '夜色.*笼罩', '夜幕降临', '华灯初上',
        '月光.*洒', '繁星点点',
        '空气.*清新', '鸟语花香'
    ]
    env_count = sum(len(re.findall(p, text)) for p in env_templates)
    density6 = env_count / max(chars / 1000, 1)
    scores["env_template"] = min(100, density6 * 50)
    
    # 7. 段落结尾升华 (权重 5%)
    paragraph_ends = [p.strip()[-50:] for p in text.split('\n\n') if p.strip()]
    moral_patterns = [
        '这就是', '或许这就是', '生活就是', '人生就是',
        '也许', '或许', '大概', '就像', '正如',
        '一切都是', '原来'
    ]
    moral_count = sum(
        1 for end in paragraph_ends[:30]  # 只检查前30段
        if any(end.startswith(p) for p in moral_patterns)
    )
    scores["paragraph_moral"] = min(100, moral_count / 30 * 100)
    
    # 8. 成语堆砌检测 (权重 5%)
    # ⚠️ 此检测需接入真实成语词典才可启用。当前正则 '([一-鿿]{4}){3}'
    #    会匹配任意 12 个连续汉字，误判率接近 100%（如「今天天气真好我们出去走走」也会命中）。
    #    在没有成语词典的情况下，此维度默认跳过（计 0 分），不参与加权计算。
    #    如需启用，请将 chengyu_dict_path 指向一个成语列表文件（每行一个成语）。
    chengyu_dict_path = None  # 设置为 Path("~/novels/_shared/data/成语词典.txt") 以启用
    chengyu_overdose = 0
    if chengyu_dict_path and Path(os.path.expanduser(str(chengyu_dict_path))).exists():
        chengyu_dict = set(
            Path(os.path.expanduser(str(chengyu_dict_path)))
            .read_text(encoding='utf-8').strip().split('\n')
        )
        for p in text.split('\n'):
            four_char = re.findall(r'[一-鿿]{4}', p)
            chengyu_hits = [w for w in four_char if w in chengyu_dict]
            if len(chengyu_hits) >= 3:
                chengyu_overdose += 1
        scores["chengyu_abuse"] = min(100, chengyu_overdose * 20)
    else:
        scores["chengyu_abuse"] = 0  # 成语词典缺失，默认跳过
    # 原始误判正则（已禁用，保留注释以供参考）:
    # chengyu_pattern = re.compile(r'([一-鿿]{4})([一-鿿]{4})([一-鿿]{4})')
    # matches = chengyu_pattern.findall(text)
    # for p in text.split('\n'):
    #     four_char = re.findall(r'[一-鿿]{4}', p)
    #     if len(four_char) >= 3:
    #         for i in range(len(four_char) - 2):
    #             seq = ''.join(four_char[i:i+3])
    #             if chengyu_pattern.search(seq):
    #                 chengyu_overdose += 1
    # 计算加权总分
    weights = {
        "template_sentence": 0.25,
        "ai_connector": 0.20,
        "cliche_metaphor": 0.15,
        "dialogue_dao": 0.10,
        "mental_telling": 0.10,
        "env_template": 0.10,
        "paragraph_moral": 0.05,
        "chengyu_abuse": 0.05
    }
    
    total = sum(scores[k] * weights[k] for k in weights)
    
    return {
        "total_score": round(total, 1),
        "dimensions": {k: round(v, 1) for k, v in scores.items()},
        "grade": _ai_grade(total)
    }


def _ai_grade(score: float) -> str:
    if score <= 15:
        return "🟢 自然 (几乎无AI痕迹)"
    elif score <= 30:
        return "🟢 良好 (轻微AI味，可接受)"
    elif score <= 50:
        return "🟡 注意 (AI味明显，建议润色)"
    elif score <= 70:
        return "🟠 较重 (读者可能察觉AI痕迹)"
    else:
        return "🔴 严重 (强烈建议人工重写)"


if __name__ == "__main__":
    import argparse
    import sys
    
    parser = argparse.ArgumentParser(description="AI味健康评分")
    parser.add_argument("file", nargs="?", help="要评估的章节文件路径")
    parser.add_argument("--book", help="指定书名，扫描最新章节")
    args = parser.parse_args()
    
    if args.file:
        # 直接评估指定文件
        text = Path(args.file).read_text(encoding='utf-8')
        result = ai_score(text)
        print(f"文件: {args.file}")
        print(f"AI味评分: {result['total_score']} — {result['grade']}")
        print("\n各维度得分:")
        for dim, score in result['dimensions'].items():
            bar = "█" * int(score / 5) + "░" * (20 - int(score / 5))
            print(f"  {dim:20s}: {bar} {score:5.1f}")
        sys.exit(0 if result['total_score'] <= 50 else 1)
    
    elif args.book:
        # 扫描指定书籍的最新章
        draft_dir = Path(os.path.expanduser("~/novels/books")) / args.book / "01-正文存稿"
        if not draft_dir.exists():
            print(f"错误: 找不到书籍 '{args.book}' 的正文存稿目录")
            sys.exit(2)
        chapter_files = sorted(
            draft_dir.glob("第*章*.md"),
            key=lambda f: f.stat().st_mtime,
            reverse=True
        )[:1]
        if not chapter_files:
            print(f"错误: '{args.book}' 无章节文件")
            sys.exit(2)
        cf = chapter_files[0]
        text = cf.read_text(encoding='utf-8')
        result = ai_score(text)
        print(f"书籍: {args.book} | 章节: {cf.name}")
        print(f"AI味评分: {result['total_score']} — {result['grade']}")
        print("\n各维度得分:")
        for dim, score in result['dimensions'].items():
            bar = "█" * int(score / 5) + "░" * (20 - int(score / 5))
            print(f"  {dim:20s}: {bar} {score:5.1f}")
        sys.exit(0 if result['total_score'] <= 50 else 1)
    
    else:
        print("用法: python ai_score.py [--book <书名>] [<文件路径>]")
        print("示例:")
        print("  python ai_score.py ~/novels/books/仙途/01-正文存稿/第45章.md")
        print("  python ai_score.py --book 仙途")
        sys.exit(0)
```

### 6.3 AI味抽查策略
```
触发条件:
  - 每本书每累计 10 章 → 抽取最新 1 章评估
  - 或按 cron 配置每周日做全量抽查

抽查输出:
  - 每章 AI味总分 + 各维度得分
  - 标记最高分的 3 个维度 = 最大问题来源
  - 给出具体示例（从该章中摘取 3 句最像AI写的）

建议:
  - AI味评分 > 50 的章节 → 提示作者用 novel-polish 针对性润色
  - 连续 3 章评分上升 → 趋势告警（越写越像AI？）
```

---

## 七、OOC 角色一致性检测（⚠️ 不在 cron 中运行）

> **OOC（Out-of-Character）检测依赖 LLM 的 6 维特征提取**（性格一致性、语言风格、行为逻辑、情感反应、知识边界、关系互动），
> 无法以纯脚本（`no_agent` 模式）在 cron 中运行。
>
> **OOC 检测保留在 `novel-review`（agent 模式）中**，通过 LLM 对最新章节进行角色一致性评分。
>
> cron 巡检只负责：
> - ✅ 违禁词扫描（规则匹配，不需要 LLM）
> - ✅ AI味健康评分（规则匹配，不需要 LLM）
>
> 如需触发 OOC 检测，请运行 agent 模式的 `novel-review`。

---

## 综合输出格式

每日巡检报告保存到 `~/novels/_shared/logs/巡检_YYYY-MM-DD.md`：

```markdown
# 📋 小说项目每日巡检 — 2026-07-24

## 一、备份状态
| 书名 | 正文备份 | 设定备份 | 大小 |
|------|---------|---------|------|
| 《仙途》 | ✅ | ✅ | 2.3 MB |
| 《都市战神》 | ✅ | ✅ | 1.8 MB |

备份完成时间: 04:02 | 保留最近 7 天

---

## 二、违禁词扫描
（嵌入 novel_scan.py 输出）

---

## 三、🚨 伏笔提醒
（嵌入 foreshadow_check.py 输出）

---

## 四、章节统计
（嵌入 chapter_stats.py 输出）

---

## 五、🔥 网络热榜
（嵌入 trending_news.py 输出）

如有匹配到可融入热点 → 列出建议

---

## 六、🤖 AI味健康评分
最新抽查结果:

| 书名 | 最近抽查章 | AI味评分 | 评级 | 主要问题 |
|------|-----------|---------|------|---------|
| 《仙途》 | 第45章 | 23.5 | 🟢 良好 | 模板句式略多 |

---

## 七、改进建议
（综合以上结果给出行动建议）
```

---

## 注意事项
- 所有脚本不修改任何正文或设定文件
- 违禁词扫描结果仅供作者参考，不做自动屏蔽
- **OOC 角色一致性检测不在 cron 中运行**，依赖 LLM 的 6 维特征提取，保留在 agent 模式的 `novel-review` 中
- **热榜拉取已改用稳定 RSS 源**（知乎日报、36氪、少数派、澎湃新闻），失败时自动跳过并在报告中标注；如需实时热搜排行，请在 agent 模式下使用 `web_search("微博热搜")` 等
- 抖音热搜不实现自动拉取（需处理反爬），可代用 `web_search("抖音热搜")`
- AI味评分仅供参考，不强制修改
- 报告保存到 `~/novels/_shared/logs/巡检_YYYY-MM-DD.md`
- 所有脚本文件独立放在 `~/novels/_shared/scripts/` 目录下
- cron 配置使用 `no_agent=false`（脚本嵌入在 MD 中无法被 no_agent 模式直接执行）。如需 no_agent 模式省 token，需先将脚本提取为独立的 `.py` 文件放入 `~/novels/_shared/scripts/`，再在 cron 配置中引用脚本路径而非 MD 文件
- **热榜拉取失败不阻塞其他巡检项目**（网络不稳定时优雅降级，报告标题行标注 ⚠️ 拉取失败）
