#!/usr/bin/env python3
"""
review_scan.py — DRAFT 后自动扫描（novel-main 步骤4 REVIEW 第1步调用）
用法: 
  python3 review_scan.py <章节文件路径> [--book <书名>]
  python3 review_scan.py <章节文件路径> --config <书配置路径>

扫描项:
1. 系统面板违禁术语（从书配置读取，回退到默认列表）
2. 地名白名单外检查（从书配置读取）
3. 真实地名黑名单检查（从书配置读取）
4. AI禁用词检查
5. 对话框式检查（禁止 ╔══╗ 等 box-drawing 字符）
6. 双引号检测（禁止 ASCII 双引号 "，应使用「」）
7. 章末禁止标记 + 标题格式检查

返回: 命中列表（JSON），零命中 = 通过。
"""
import json
import re
import sys
import os
import argparse
from pathlib import Path

# === 默认值（书配置缺失时回退） ===

DEFAULT_SYSTEM_BANNED_TERMS = [
    "投放回收比", "宿主", "检测到", "解锁", "阶段", "动态上浮",
    "循环状态", "回报周期", "回报周期预估", "子系统激活", "暴击触发",
    "新手礼包", "新手任务", "每日任务", "成就系统", "升级条件",
    "关联人口", "预估", "建议", "预警", "争夺",
]

DEFAULT_AI_BANNED_WORDS = [
    "或许", "仿佛", "然而", "于是", "顷刻间", "悄然", "似乎",
    "一丝", "泛起", "充斥", "勾勒", "雕琢", "绽放", "氤氲",
    "缱绻", "旖旎", "斑驳", "婆娑", "呢喃",
]

BOX_DRAWING_CHARS = ["╔", "╗", "╚", "╝", "║", "═", "╠", "╣", "╦", "╩", "╬"]

BANNED_ENDING_PATTERNS = [
    r'第\d+章\s*结束',
    r'本章完',
    r'（本章完）',
    r'（第\d+章\s*完）',
    r'<center>',
    r'</center>',
]

BANNED_HEADER_PATTERNS = [
    r'^【第\d+章',
]

PLACE_SUSPICIOUS_PATTERNS = [
    (r'([^\s]{1,3}(?:港|城|市|县|镇|村|岛|湾|塘|码头|市场|广场|大厦))', '疑似地名'),
]

# === 书配置加载 ===

def load_book_config(book_name=None, config_path=None):
    """从书配置.md 加载该书专属规则。
    
    查找顺序：
    1. --config 指定的路径
    2. ~/novels/books/<book_name>/02-设定文档/书配置.md
    3. 回退到默认值
    """
    if config_path is None and book_name:
        config_path = os.path.expanduser(
            f"~/novels/books/{book_name}/02-设定文档/书配置.md"
        )
    
    config = {
        "place_whitelist": [],
        "real_place_blacklist": [],
        "system_banned_terms": DEFAULT_SYSTEM_BANNED_TERMS,
        "ai_banned_words": DEFAULT_AI_BANNED_WORDS,
    }
    
    if config_path and os.path.isfile(config_path):
        content = Path(config_path).read_text(encoding='utf-8')
        
        # 提取地名白名单（```代码块中的内容，跳过说明行和空行）
        whitelist_match = re.search(
            r'## 地名白名单\s*\n.*?```\n(.*?)```', content, re.DOTALL
        )
        if whitelist_match:
            raw = whitelist_match.group(1)
            for line in raw.split('\n'):
                line = line.strip()
                if line and not line.startswith('#') and not line.startswith('以下') and '区名' not in line:
                    # 按顿号、逗号分割
                    for p in re.split(r'[、,，]', line):
                        p = p.strip()
                        if p:
                            config["place_whitelist"].append(p)
        
        # 提取真实地名黑名单
        blacklist_match = re.search(
            r'## 真实地名黑名单\s*\n.*?```\n(.*?)```', content, re.DOTALL
        )
        if blacklist_match:
            raw = blacklist_match.group(1)
            for line in raw.split('\n'):
                line = line.strip()
                if line and not line.startswith('#'):
                    for p in re.split(r'[、,，]', line):
                        p = p.strip()
                        if p:
                            config["real_place_blacklist"].append(p)
        
        # 提取禁止措辞
        banned_match = re.search(
            r'### 禁止措辞\s*\n+`([^`]+)`', content
        )
        if banned_match:
            raw = banned_match.group(1)
            terms = re.split(r'[、,\s]+', raw)
            config["system_banned_terms"] = [t.strip() for t in terms if t.strip()]
    
    return config


def scan_file(filepath, config):
    """扫描单文件，返回命中列表"""
    path = Path(filepath)
    if not path.exists():
        return [{"error": f"文件不存在: {filepath}"}]
    
    content = path.read_text(encoding='utf-8')
    lines = content.split('\n')
    hits = []
    
    place_whitelist = set(config["place_whitelist"])
    real_place_blacklist = config["real_place_blacklist"]
    system_banned = config["system_banned_terms"]
    ai_banned = config["ai_banned_words"]
    
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith('#') or not stripped:
            continue
        
        # 1. 系统违禁术语
        for term in system_banned:
            if term in stripped:
                hits.append({
                    "type": "系统违禁术语",
                    "level": 1,
                    "line": i,
                    "word": term,
                    "context": stripped[:100]
                })
        
        # 2. AI禁用词
        in_quote = '「' in stripped
        for word in ai_banned:
            if word in stripped:
                hits.append({
                    "type": "AI禁用词(对话中)" if in_quote else "AI禁用词",
                    "level": 2 if in_quote else 1,
                    "line": i,
                    "word": word,
                    "context": stripped[:100]
                })
        
        # 3. 双引号检测
        if '"' in stripped:
            hits.append({
                "type": "双引号违禁",
                "level": 1,
                "line": i,
                "word": '"',
                "context": stripped[:100]
            })
        
        # 4. 对话框式字符
        for ch in BOX_DRAWING_CHARS:
            if ch in stripped:
                hits.append({
                    "type": "对话框式字符",
                    "level": 1,
                    "line": i,
                    "word": ch,
                    "context": stripped[:100]
                })
        
        # 5. 章末禁止标记
        for pattern in BANNED_ENDING_PATTERNS:
            if re.search(pattern, stripped):
                hits.append({
                    "type": "章末违禁标记",
                    "level": 1,
                    "line": i,
                    "word": f"[Pattern] {pattern}",
                    "context": stripped[:100]
                })
        
        # 6. 标题格式违规（仅第1行）
        if i == 1:
            for pattern in BANNED_HEADER_PATTERNS:
                if re.search(pattern, stripped):
                    hits.append({
                        "type": "标题格式违规",
                        "level": 1,
                        "line": i,
                        "word": f"[Pattern] {pattern}",
                        "context": stripped[:100]
                    })
    
    # 7. 地名白名单外检查
    for pattern, label in PLACE_SUSPICIOUS_PATTERNS:
        for match in re.finditer(pattern, content):
            matched_word = match.group(1)
            if matched_word not in place_whitelist:
                line_num = content[:match.start()].count('\n') + 1
                hits.append({
                    "type": f"地名白名单外: {label}",
                    "level": 1,
                    "line": line_num,
                    "word": matched_word,
                    "context": f"「{matched_word}」不在白名单中"
                })
    
    # 8. 真实地名黑名单
    for real_place in real_place_blacklist:
        if real_place in content:
            hits.append({
                "type": "真实地名违禁",
                "level": 1,
                "line": 0,
                "word": f"黑名单地名: {real_place}",
                "context": f"禁止在正文使用真实地名「{real_place}」"
            })
    
    return hits


def main():
    parser = argparse.ArgumentParser(
        description='DRAFT后自动扫描 — 系统违禁术语/地名/AI禁用词/格式检查'
    )
    parser.add_argument('filepath', help='章节文件路径')
    parser.add_argument('--book', '-b', help='书名（自动定位书配置.md）')
    parser.add_argument('--config', '-c', help='书配置.md 的完整路径')
    args = parser.parse_args()
    
    config = load_book_config(book_name=args.book, config_path=args.config)
    hits = scan_file(args.filepath, config)
    
    level1 = [h for h in hits if h.get("level") == 1]
    level2 = [h for h in hits if h.get("level") == 2]
    
    result = {
        "file": args.filepath,
        "total_hits": len(hits),
        "level1": len(level1),
        "level2": len(level2),
        "config_loaded": len(config["place_whitelist"]) > 0,
        "place_whitelist_count": len(config["place_whitelist"]),
        "hits": hits
    }
    
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(1 if level1 else 0)


if __name__ == "__main__":
    main()
