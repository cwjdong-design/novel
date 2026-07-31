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
