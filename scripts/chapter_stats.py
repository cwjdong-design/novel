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
