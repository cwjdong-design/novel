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


def check_abandoned(book_dir: Path, chapter_threshold: int = 30) -> list:
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
            if chapters_ago > chapter_threshold:
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
    parser.add_argument("--chapters", type=int, default=30, help="遗忘检测阈值章数，默认30")
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
        abandoned = check_abandoned(book_dir, args.chapters)
        if overdue:
            overdue_all[book_name] = overdue
        if abandoned:
            abandoned_all[book_name] = abandoned
    
    report = generate_reminder(overdue_all, abandoned_all)
    print(report)
    
    # 有超期伏笔时 exit code 1，用于 cron 告警
    has_overdue = any(len(items) > 0 for items in overdue_all.values())
    sys.exit(1 if has_overdue else 0)
