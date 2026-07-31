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
    moral_patterns = [
        '这就是', '或许这就是', '生活就是', '人生就是',
        '也许', '或许', '大概', '就像', '正如',
        '一切都是', '原来'
    ]
    moral_count = 0
    for p in text.split('\n\n')[:30]:  # 只检查前30段
        p = p.strip()
        if not p:
            continue
        # 按句号/感叹号/问号拆句
        sentences = re.split(r'(?<=[。！？])', p)
        sentences = [s.strip() for s in sentences if s.strip()]
        if not sentences:
            continue
        first_sentence = sentences[0]
        last_sentence = sentences[-1]
        if any(first_sentence.startswith(patt) for patt in moral_patterns) or \
           any(last_sentence.startswith(patt) for patt in moral_patterns):
            moral_count += 1
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
