#!/usr/bin/env python3
"""
consistency_check.py — 跨文档一致性检查
用法: python3 consistency_check.py --book <书名> [--json]

检查维度:
  C1: 人物卡 ↔ 人物总表 双向一致性
  C2: 章节规划 ↔ 正文存稿 章数/标题一致性  
  C3: 故事线状态 覆盖所有正文章节
  C4: 前文时间线速查 覆盖范围
  C5: 伏笔表引用有效章节号
  C6: 正文人物 → 人物库注册核查
  C7: 大纲分卷章数总和 vs 总章数
"""
import json
import re
import sys
from pathlib import Path
from collections import defaultdict

NOVEL_ROOT = Path.home() / "novels" / "books"


# ─── 工具函数 ───────────────────────────────────────────

def normalize_name(name: str) -> str:
    """归一化人名: 去除括号和括号内别名（如 '周德海（老周）' → '周德海'）"""
    # 去掉括号内容和斜杠别名
    name = re.sub(r'[（(][^)）]*[)）]', '', name).strip()
    name = re.sub(r'/[^,\s]+', '', name).strip()
    return name


def parse_chapter_num(text: str) -> int:
    """从文本提取章节号: '第8章' → 8, 'Ch.15' → 15"""
    m = re.search(r'第\s*(\d+)\s*章', text)
    if m:
        return int(m.group(1))
    m = re.search(r'Ch\.\s*(\d+)', text)
    if m:
        return int(m.group(1))
    return 0


def extract_md_table(filepath: Path, col_count: int) -> list[dict]:
    """提取 Markdown 表格为 dict 列表"""
    if not filepath.exists():
        return []
    content = filepath.read_text(encoding='utf-8')
    rows = []
    in_table = False
    headers = []
    for line in content.split('\n'):
        if line.startswith('|') and '|' in line[1:]:
            if not in_table:
                headers = [c.strip() for c in line.split('|')[1:-1]]
                in_table = True
                continue
            if re.match(r'^\|[\s\-:]+\|', line):
                continue
            cols = [c.strip() for c in line.split('|')[1:-1]]
            if cols and cols[0] and cols[0] not in headers:
                row = {headers[i]: cols[i] if i < len(cols) else '' for i in range(len(headers))}
                rows.append(row)
    return rows


# ─── C1: 人物卡 ↔ 人物总表 ─────────────────────────────

def check_c1(book_dir: Path) -> list:
    """检查人物库卡片与人物总表的双向一致性"""
    issues = []
    char_dir = book_dir / "02-设定文档" / "人物库"
    roster_path = book_dir / "02-设定文档" / "人物总表.md"
    
    # 收集人物库中的卡片名
    card_names = set()
    for f in sorted(char_dir.glob("*.md")):
        name = f.stem
        card_names.add(name)
    
    # 从人物总表提取核心/次要角色名
    if not roster_path.exists():
        issues.append({"check": "C1", "severity": "🔴", "detail": "人物总表.md 不存在"})
        return issues
    
    roster_text = roster_path.read_text(encoding='utf-8')
    
    # 提取总表中的所有角色名（从列表项 "- 姓名（..." ）
    roster_names = set()
    roster_raw = set()
    for m in re.finditer(r'-\s*([^\s(（]+)(?:[（(][^)）]*[)）])?', roster_text):
        raw = m.group(1).strip()
        if raw and not raw.startswith('#') and not raw.startswith('>'):
            roster_raw.add(raw)
            roster_names.add(normalize_name(raw))
    
    # 卡片文件名归一化
    card_normalized = {normalize_name(n): n for n in card_names}
    
    # 卡片有但总表无（用归一化名比较）
    for norm_name, orig_name in sorted(card_normalized.items()):
        if norm_name not in roster_names:
            issues.append({
                "check": "C1", "severity": "🔴",
                "detail": f"人物卡「{orig_name}」存在但未在人物总表中注册"
            })
    
    # 总表有但卡片无
    roster_normalized = {normalize_name(r): r for r in roster_raw}
    for norm_name, orig_name in sorted(roster_normalized.items()):
        if norm_name not in card_normalized:
            issues.append({
                "check": "C1", "severity": "🟡",
                "detail": f"人物总表中有「{orig_name}」但人物库中无对应卡片"
            })
    
    if not issues:
        issues.append({"check": "C1", "severity": "✅", "detail": "人物卡与人物总表一致"})
    return issues


# ─── C2: 章节规划 ↔ 正文存稿 ───────────────────────────

def check_c2(book_dir: Path) -> list:
    """检查章节规划与正文存稿的章数和标题一致性"""
    issues = []
    plan_path = book_dir / "00-大纲细纲" / "章节规划.md"
    draft_dir = book_dir / "01-正文存稿"
    
    if not plan_path.exists():
        issues.append({"check": "C2", "severity": "🔴", "detail": "章节规划.md 不存在"})
        return issues
    
    # 提取章节规划中的章节信息
    plan_rows = extract_md_table(plan_path, 6)
    plan_chapters = {}
    for row in plan_rows:
        ch_str = row.get("章节", "")
        ch_num = parse_chapter_num(f"第{ch_str}章")
        if ch_num > 0:
            plan_chapters[ch_num] = {
                "title": row.get("标题", ""),
                "event": row.get("核心事件", ""),
                "status": row.get("备注", "")
            }
    
    # 收集正文目录
    draft_chapters = {}
    for f in sorted(draft_dir.glob("第*章*.md")):
        ch_num = parse_chapter_num(f.name)
        if ch_num > 0:
            draft_chapters[ch_num] = f
    
    max_draft = max(draft_chapters.keys()) if draft_chapters else 0
    max_plan = max(plan_chapters.keys()) if plan_chapters else 0
    
    # 正文有但规划无
    for ch in sorted(draft_chapters.keys()):
        if ch not in plan_chapters:
            issues.append({
                "check": "C2", "severity": "🔴",
                "detail": f"第{ch}章正文存在但章节规划中无对应行"
            })
    
    # 规划中标记"已完成"但正文不存在
    for ch, info in plan_chapters.items():
        if "已完成" in info.get("status", "") and ch not in draft_chapters:
            issues.append({
                "check": "C2", "severity": "🔴",
                "detail": f"第{ch}章规划标记为已完成但正文文件缺失"
            })
    
    # 标题一致性
    for ch in sorted(set(draft_chapters.keys()) & set(plan_chapters.keys())):
        plan_title = plan_chapters[ch]["title"]
        if plan_title in ("待定", "TBD", "", "—"):
            issues.append({
                "check": "C2", "severity": "🟡",
                "detail": f"第{ch}章标题在章节规划中为占位/空白"
            })
    
    # 核心事件占位
    for ch in sorted(plan_chapters.keys()):
        if ch > max_draft:
            event = plan_chapters[ch].get("event", "")
            if not event or event in ("待定", "TBD", "", "—"):
                continue  # 未来章节可以没有详细事件
            if len(event) < 5:
                issues.append({
                    "check": "C2", "severity": "🟡",
                    "detail": f"第{ch}章核心事件描述过短（<5字）"
                })
    
    if not any(i.get("severity") in ("🔴", "🟡") for i in issues if i["check"] == "C2"):
        issues.append({"check": "C2", "severity": "✅", "detail": f"章节规划与正文一致（规划{max_plan}章/正文{max_draft}章）"})
    return issues


# ─── C3: 故事线状态覆盖 ────────────────────────────────

def check_c3(book_dir: Path) -> list:
    """检查故事线状态是否覆盖所有正文章节"""
    issues = []
    status_path = book_dir / "02-设定文档" / "故事线状态.md"
    draft_dir = book_dir / "01-正文存稿"
    
    draft_chs = sorted(set(parse_chapter_num(f.name) for f in draft_dir.glob("第*章*.md") if parse_chapter_num(f.name) > 0))
    
    if not status_path.exists():
        issues.append({"check": "C3", "severity": "🔴", "detail": "故事线状态.md 不存在"})
        return issues
    
    content = status_path.read_text(encoding='utf-8')
    status_chs = set()
    for m in re.finditer(r'第\s*(\d+)\s*章', content):
        status_chs.add(int(m.group(1)))
    
    missing = set(draft_chs) - status_chs
    if missing:
        issues.append({
            "check": "C3", "severity": "🟡",
            "detail": f"故事线状态缺失以下章节: {sorted(missing)}"
        })
    
    # 也检查是否有状态行但无正文
    extra = status_chs - set(draft_chs)
    if extra:
        issues.append({
            "check": "C3", "severity": "🟡",
            "detail": f"故事线状态有记录但正文缺失: {sorted(extra)}"
        })
    
    if not any(i.get("severity") in ("🔴", "🟡") for i in issues if i["check"] == "C3"):
        issues.append({"check": "C3", "severity": "✅", "detail": f"故事线状态覆盖全部{draft_chs[-1]}章正文"})
    return issues


# ─── C4: 前文时间线速查 ────────────────────────────────

def check_c4(book_dir: Path) -> list:
    """检查前文时间线速查覆盖范围（应至少包含最近3章）"""
    issues = []
    timeline_path = book_dir / "06-追踪记录" / "前文时间线速查.md"
    draft_dir = book_dir / "01-正文存稿"
    
    draft_chs = sorted(set(parse_chapter_num(f.name) for f in draft_dir.glob("第*章*.md") if parse_chapter_num(f.name) > 0))
    if not draft_chs:
        return [{"check": "C4", "severity": "✅", "detail": "无正文章节，跳过时间线检查"}]
    
    max_ch = max(draft_chs)
    
    if not timeline_path.exists():
        issues.append({"check": "C4", "severity": "🟡", "detail": "前文时间线速查.md 不存在"})
        return issues
    
    rows = extract_md_table(timeline_path, 4)
    timeline_chs = set()
    for row in rows:
        ch_str = row.get("章节", "")
        ch_num = parse_chapter_num(ch_str)
        if ch_num > 0:
            timeline_chs.add(ch_num)
    
    # 检查最近3章是否覆盖
    expected = set(range(max(1, max_ch - 2), max_ch + 1))
    missing = expected - timeline_chs
    if missing:
        issues.append({
            "check": "C4", "severity": "🟡",
            "detail": f"前文时间线速查缺失最近章节: {sorted(missing)}（应覆盖Ch.{max_ch-2}-{max_ch}）"
        })
    
    if not any(i.get("severity") in ("🔴", "🟡") for i in issues if i["check"] == "C4"):
        issues.append({"check": "C4", "severity": "✅", "detail": f"前文时间线速查完整（{len(timeline_chs)}章）"})
    return issues


# ─── C5: 伏笔表引用有效性 ──────────────────────────────

def check_c5(book_dir: Path) -> list:
    """检查伏笔追踪表引用章节是否有效"""
    issues = []
    ft_path = book_dir / "02-设定文档" / "伏笔追踪表.md"
    draft_dir = book_dir / "01-正文存稿"
    
    draft_chs = set(parse_chapter_num(f.name) for f in draft_dir.glob("第*章*.md") if parse_chapter_num(f.name) > 0)
    max_ch = max(draft_chs) if draft_chs else 0
    
    if not ft_path.exists():
        issues.append({"check": "C5", "severity": "🟡", "detail": "伏笔追踪表.md 不存在"})
        return issues
    
    rows = extract_md_table(ft_path, 8)
    
    for row in rows:
        vid = row.get("ID", "?")
        recycle_str = row.get("计划回收章", "")
        actual_str = row.get("实际回收章", "")
        
        # 检查计划回收章有效性
        recycle_ch = parse_chapter_num(recycle_str) if recycle_str else 0
        if recycle_ch > 0 and recycle_ch <= max_ch:
            status = row.get("状态", "")
            if "已回收" not in status and "✅" not in status:
                # 超期未回收
                overdue = max_ch - recycle_ch
                sev = "🔴" if overdue >= 3 else "🟡"
                issues.append({
                    "check": "C5", "severity": sev,
                    "detail": f"伏笔{vid}计划第{recycle_ch}章回收，已超期{overdue}章（当前第{max_ch}章）"
                })
    
    if not any(i.get("severity") in ("🔴", "🟡") for i in issues if i["check"] == "C5"):
        issues.append({"check": "C5", "severity": "✅", "detail": f"伏笔追踪表正常（{len(rows)}条）"})
    return issues


# ─── C6: 正文人物 → 人物库注册 ──────────────────────────

def check_c6(book_dir: Path) -> list:
    """检查正文中出现的人物是否在人物库中注册"""
    issues = []
    char_dir = book_dir / "02-设定文档" / "人物库"
    draft_dir = book_dir / "01-正文存稿"
    roster_path = book_dir / "02-设定文档" / "人物总表.md"
    
    # 收集已知人名
    known_names = set()
    for f in char_dir.glob("*.md"):
        known_names.add(f.stem)
    if roster_path.exists():
        roster_text = roster_path.read_text(encoding='utf-8')
        for m in re.finditer(r'-\s*([^\s(（]+)', roster_text):
            name = m.group(1).strip()
            if name and not name.startswith('#'):
                known_names.add(name)
    
    # 扫描正文中的人名模式：「XXX」是人名标记 + 明确的专有名称
    # 策略：找「」中2-4字的中文名，排除已知角色和系统术语
    # 停用词：不是人名的常见「」内容
    # 从书配置加载方言停用词，回退到最小默认集
    book_config_path = book_dir / "02-设定文档" / "书配置.md"
    persona_stopwords = {
        "招租", "欠债", "老板", "该留", "安全生产", "合作愉快",
        "品质稳", "这个价", "好。", "不急", "真的？", "现钱",
        "好——", "说。", "成。", "知道了", "慢慢来", "不急这一时",
        "不吃亏", "等着看", "有意思", "在商言商", "按规矩来",
        # 常见非人名单字词
        "行。", "好。", "嗯。", "讲。", "走。", "来。", "去。",
        "有。", "够。", "稳", "收。", "查。", "接。", "等。",
        "成。", "对。", "没。", "能。", "会。", "该。", "要。",
        "好", "行", "嗯", "来", "去", "有", "收", "讲", "在",
    }
    # 尝试从书配置加载方言词表并添加到停用词
    if book_config_path.exists():
        config_content = book_config_path.read_text(encoding='utf-8')
        # 提取方言词表中的词
        dialect_match = re.search(r'## 方言设置.*?## ', config_content, re.DOTALL)
        if dialect_match:
            dialect_section = dialect_match.group(0)
            for m in re.finditer(r'\| (\S+) \|', dialect_section):
                word = m.group(1)
                if len(word) <= 4:
                    persona_stopwords.add(word)
    
    found_names = defaultdict(list)  # name → [chapters]
    
    for f in sorted(draft_dir.glob("第*章*.md")):
        ch_num = parse_chapter_num(f.name)
        content = f.read_text(encoding='utf-8')
        # 只匹配「」引号中2-3个中文字符且不在系统术语中
        for m in re.finditer(r'「([^\n]{2,4})」', content):
            name = m.group(1)
            if (re.match(r'^[\u4e00-\u9fff]{2,3}$', name) and 
                name not in persona_stopwords and 
                name not in known_names and
                not name.endswith(('的', '了', '是', '在', '和', '不', '也', '就', '说', '来', '去', '要', '有', '会', '能', '着', '过', '到', '这', '那', '他', '她', '它', '我', '你', '很', '都', '可', '把', '被', '从', '对', '与', '为', '以', '及', '或', '但', '若', '则', '而', '且', '然', '因', '所', '其', '之', '于', '由', '自', '至', '如', '此', '等', '者', '何', '哪', '怎', '吗', '吧', '呢', '啊', '哦', '嗯', '唉', '喂'))):
                found_names[name].append(ch_num)
    
    for name, chapters in sorted(found_names.items()):
        if len(chapters) >= 1:
            # 检查是否为已知角色的简称（如名字是已知角色全名的子串）
            is_alias = any(name in known for known in known_names if len(known) > len(name))
            if is_alias:
                continue
            issues.append({
                "check": "C6", "severity": "🟡",
                "detail": f"「{name}」在Ch.{chapters}中出现但未在人物库/总表中注册"
            })
    
    if not any(i.get("severity") in ("🔴", "🟡") for i in issues if i["check"] == "C6"):
        issues.append({"check": "C6", "severity": "✅", "detail": "正文中出场人物均在人物库中注册"})
    return issues


# ─── C7: 大纲分卷章数总和 ──────────────────────────────

def check_c7(book_dir: Path) -> list:
    """检查大纲总纲的总章数与各分卷细纲章数是否一致"""
    issues = []
    outline_path = book_dir / "00-大纲细纲" / "故事总纲.md"
    volume_dir = book_dir / "00-大纲细纲" / "分卷细纲"
    
    if not outline_path.exists():
        return [{"check": "C7", "severity": "✅", "detail": "故事总纲不存在，跳过"}]
    
    content = outline_path.read_text(encoding='utf-8')
    m = re.search(r'总章节[：:]\s*(\d+)', content)
    total_planned = int(m.group(1)) if m else 0
    
    # 提取各卷的章数范围
    volume_ranges = []
    for m in re.finditer(r'第([一二三四五六七])卷[：:].*?(\d+)[–\-~至]+(\d+)', content):
        start, end = int(m.group(2)), int(m.group(3))
        volume_ranges.append((start, end))
    
    if volume_ranges:
        last_end = volume_ranges[-1][1] if volume_ranges else 0
        if total_planned > 0 and last_end != total_planned:
            issues.append({
                "check": "C7", "severity": "🟡",
                "detail": f"总纲总章数{total_planned} ≠ 最后卷结束章{last_end}"
            })
    
    # 检查各卷是否连续
    for i in range(1, len(volume_ranges)):
        prev_end = volume_ranges[i-1][1]
        curr_start = volume_ranges[i][0]
        if curr_start != prev_end + 1:
            issues.append({
                "check": "C7", "severity": "🟡",
                "detail": f"分卷章数不连续: 第{i}卷结束于{prev_end}章, 第{i+1}卷开始于{curr_start}章"
            })
    
    if not any(i.get("severity") in ("🔴", "🟡") for i in issues if i["check"] == "C7"):
        issues.append({"check": "C7", "severity": "✅", "detail": f"大纲分卷章数一致（总计{total_planned}章）"})
    return issues


# ─── 主入口 ─────────────────────────────────────────────

def run_all(book_dir: Path) -> dict:
    """运行所有7项检查"""
    all_issues = []
    for check_fn in [check_c1, check_c2, check_c3, check_c4, check_c5, check_c6, check_c7]:
        all_issues.extend(check_fn(book_dir))
    
    level_counts = defaultdict(int)
    for i in all_issues:
        level_counts[i["severity"]] += 1
    
    return {
        "book": book_dir.name,
        "total_issues": len(all_issues),
        "by_severity": dict(level_counts),
        "issues": all_issues
    }


def generate_report(result: dict) -> str:
    """生成 Markdown 报告"""
    lines = [
        f"## 跨文档一致性检查 — {result['book']}",
        "",
        f"| 维度 | 状态 |",
        f"|------|------|",
    ]
    
    by_check = defaultdict(list)
    for i in result["issues"]:
        by_check[i["check"]].append(i)
    
    check_labels = {
        "C1": "人物卡↔总表", "C2": "章节规划↔正文", "C3": "故事线状态",
        "C4": "前文时间线", "C5": "伏笔表", "C6": "正文人物注册",
        "C7": "大纲分卷一致性"
    }
    
    has_error = False
    for check_id in ["C1", "C2", "C3", "C4", "C5", "C6", "C7"]:
        items = by_check.get(check_id, [])
        worst = "✅"
        for i in items:
            if i["severity"] == "🔴":
                worst = "🔴"; has_error = True; break
            elif i["severity"] == "🟡" and worst != "🔴":
                worst = "🟡"
        lines.append(f"| {check_labels[check_id]} | {worst} |")
    
    lines.append("")
    
    # 非OK项详情
    problems = [i for i in result["issues"] if i["severity"] in ("🔴", "🟡")]
    if problems:
        lines.append("### 问题详情")
        lines.append("")
        for i in problems:
            lines.append(f"- {i['severity']} **{i['check']}**: {i['detail']}")
    
    if not has_error:
        lines.append("✅ 所有维度通过。")
    
    return '\n'.join(lines)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="跨文档一致性检查")
    parser.add_argument("--book", required=True, help="书名")
    parser.add_argument("--json", action="store_true", help="输出 JSON 而非 Markdown")
    args = parser.parse_args()
    
    book_dir = NOVEL_ROOT / args.book
    if not book_dir.exists():
        print(f"❌ 书籍目录不存在: {book_dir}")
        sys.exit(1)
    
    result = run_all(book_dir)
    
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(generate_report(result))
    
    # 有🔴问题 → exit code 1
    has_error = any(i["severity"] == "🔴" for i in result["issues"])
    sys.exit(1 if has_error else 0)


if __name__ == "__main__":
    main()
