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

    # 保存原始数据（每次调用时动态计算日期）
    trend_file = NOVEL_ROOT / "_shared" / "logs" / f"热榜_{datetime.now().strftime('%Y%m%d')}.json"
    trend_file.parent.mkdir(parents=True, exist_ok=True)
    raw_data = {
        "date": datetime.now(TZ).strftime("%Y-%m-%d"),
        "total_items": len(all_items),
        "sources_succeeded": success_count,
        "sources_failed": fail_count,
        "note": "RSS 源拉取，不含实时热搜排行。如需热搜排行，请在 agent 模式下使用 web_search。",
        "items": all_items,
    }
    trend_file.write_text(json.dumps(raw_data, ensure_ascii=False, indent=2))

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
