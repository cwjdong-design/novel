# -*- coding: utf-8 -*-
"""
RED 测试套件 — scripts/review_scan.py 的新行为契约（字数门禁 / 重复意象 / 疑似死水段）。

本套件定义 review_scan.py 即将新增的行为，这些行为在【当前旧实现中完全不存在】：
  - statistics.fanqie_word_count / statistics.word_count_status
  - type="字数不合格"（level=1 阻塞）
  - type="重复意象"（level=2 机械提示，第 3 次起命中）
  - type="疑似死水段"（level=2 机械提示，连续 ≥3 个静态段且累计 ≥150 番茄字符）

因此当前实现下这些测试应当【全部失败】（因缺失新行为），而不是因为语法错误失败。
实现 review_scan.py 的新逻辑后，测试应当转绿。

运行：
  python3 -m pytest tests -q            # 需要 pytest
  python3 -m unittest discover -s tests -v   # 纯标准库亦可（unittest.TestCase 被 pytest 兼容）
"""

import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "review_scan.py"


# ---------------------------------------------------------------------------
# 字数状态词族（实现方可选具体措辞，测试只要求落到正确语义桶）
# ---------------------------------------------------------------------------
STATUS_INSUFFICIENT = ("不足", "偏少", "未达标", "不够", "过短", "欠")
STATUS_QUALIFIED = ("合格", "达标", "正常", "在范围", "适宜", "通过", "ok", "pass")
STATUS_OVER = ("超标", "超量", "过多", "超长", "溢出")


def _status_in(status, tokens):
    if not isinstance(status, str):
        return False
    s = status.strip()
    return any(tok in s for tok in tokens)


def run_scan(content):
    """把 content 写入临时 .md 文件，调用 review_scan.py，返回解析后的 JSON dict。

    review_scan.py 在存在 level=1 命中时 sys.exit(1)；这里不检查返回码，
    只取 stdout 的 JSON。当前旧实现能正常输出 JSON（只是不含 statistics）。
    """
    fd, path = tempfile.mkstemp(suffix=".md", prefix="review_scan_test_")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
        proc = subprocess.run(
            [sys.executable, str(SCRIPT), path],
            capture_output=True,
            text=True,
        )
        try:
            return json.loads(proc.stdout)
        except json.JSONDecodeError:
            raise AssertionError(
                "review_scan 未输出合法 JSON。stdout=%r stderr=%r"
                % (proc.stdout, proc.stderr)
            )
    finally:
        if os.path.exists(path):
            os.unlink(path)


def make_chapter(n_chars, title="## 第1章 测试章节标题"):
    """构造番茄显示字数恰好为 n_chars 的章节正文。

    定义（契约 1）：去掉首行章节标题、所有空白，保留标点/数字/字母（含汉字）。
    这里正文用纯汉字「字」填充，并故意插入空白（换行/空格）以验证空白被剥离——
    无论实现按「非空白字符数」还是「汉字数」计数，结果都应等于 n_chars。
    """
    body = "字" * n_chars
    # 每 50 个字切成一段，段间空行，制造「有空白但不计入」的样本
    chunks = [body[i:i + 50] for i in range(0, len(body), 50)]
    body_text = "\n\n".join(chunks)
    return title + "\n" + body_text + "\n"


def hits_of_type(result, type_name):
    return [h for h in result.get("hits", []) if h.get("type") == type_name]


# ===========================================================================
# 契约 1：番茄显示字数定义 + statistics + 字数不合格命中
# ===========================================================================
class TestFanqieWordCount(unittest.TestCase):
    """番茄显示字数：2199 不足 / 2200 与 2400 合格 / 2401 超标。"""

    def test_under_2199_is_insufficient_and_blocking(self):
        result = run_scan(make_chapter(2199))
        self.assertIn("statistics", result, "review_scan JSON 必须包含 statistics 块")
        stats = result["statistics"]
        self.assertIn("fanqie_word_count", stats, "statistics 必须含 fanqie_word_count")
        self.assertEqual(stats["fanqie_word_count"], 2199)
        self.assertIn("word_count_status", stats, "statistics 必须含 word_count_status")
        self.assertTrue(
            _status_in(stats["word_count_status"], STATUS_INSUFFICIENT),
            "2199 字应判不足，status=%r" % stats["word_count_status"],
        )
        bad = hits_of_type(result, "字数不合格")
        self.assertTrue(bad, "2199 字必须产生 type=字数不合格 命中")
        self.assertEqual(bad[0].get("level"), 1, "字数不足为 level=1 阻塞")

    def test_2200_is_qualified_no_word_count_hit(self):
        result = run_scan(make_chapter(2200))
        self.assertIn("statistics", result)
        stats = result["statistics"]
        self.assertEqual(stats["fanqie_word_count"], 2200)
        self.assertTrue(
            _status_in(stats["word_count_status"], STATUS_QUALIFIED),
            "2200 字应判合格，status=%r" % stats["word_count_status"],
        )
        self.assertFalse(
            hits_of_type(result, "字数不合格"),
            "2200 字合格，不应产生 字数不合格 命中",
        )

    def test_2400_is_qualified_no_word_count_hit(self):
        result = run_scan(make_chapter(2400))
        self.assertIn("statistics", result)
        stats = result["statistics"]
        self.assertEqual(stats["fanqie_word_count"], 2400)
        self.assertTrue(
            _status_in(stats["word_count_status"], STATUS_QUALIFIED),
            "2400 字应判合格，status=%r" % stats["word_count_status"],
        )
        self.assertFalse(
            hits_of_type(result, "字数不合格"),
            "2400 字合格，不应产生 字数不合格 命中",
        )

    def test_over_2401_is_over_and_blocking(self):
        result = run_scan(make_chapter(2401))
        self.assertIn("statistics", result)
        stats = result["statistics"]
        self.assertEqual(stats["fanqie_word_count"], 2401)
        self.assertTrue(
            _status_in(stats["word_count_status"], STATUS_OVER),
            "2401 字应判超标，status=%r" % stats["word_count_status"],
        )
        bad = hits_of_type(result, "字数不合格")
        self.assertTrue(bad, "2401 字必须产生 type=字数不合格 命中")
        self.assertEqual(bad[0].get("level"), 1, "字数超标为 level=1 阻塞")


# ===========================================================================
# 契约 2：高置信重复意象的机械提示（候选短语「航标灯」，第 3 次起命中）
# ===========================================================================
class TestRepetitionImagery(unittest.TestCase):
    PHRASE = "航标灯"

    def _chapter(self, times):
        title = "## 第2章 重复意象测试"
        lines = []
        for _ in range(times):
            lines.append("他望着远处的%s，没有说话。" % self.PHRASE)
        return title + "\n\n" + "\n".join(lines) + "\n"

    def test_no_false_positive_on_first_two_occurrences(self):
        result = run_scan(self._chapter(2))
        self.assertEqual(
            hits_of_type(result, "重复意象"),
            [],
            "候选短语第 1/2 次出现不得误报 重复意象",
        )

    def test_third_occurrence_triggers_level2_hint(self):
        result = run_scan(self._chapter(3))
        rep = hits_of_type(result, "重复意象")
        self.assertTrue(rep, "候选短语「%s」第 3 次出现应命中 重复意象" % self.PHRASE)
        self.assertEqual(
            rep[0].get("level"),
            2,
            "重复意象是机械提示（level=2），不得作为 level=1 阻塞",
        )


# ===========================================================================
# 契约 3：连续无功能静态段落的保守提示（疑似死水段）
# ===========================================================================
STATIC_SENTENCES = [
    "天空灰蒙蒙的，云层压得很低。",
    "风从远处缓缓吹过来，带着一股潮湿的气味。",
    "海面安静得没有任何波纹，整片水域像凝固了一样。",
    "他站在岸边没有动，也没有说话。",
    "远处的天际线模糊不清，分不清哪里是水哪里是天。",
    "时间就这样一点一点地过去，什么也没有发生。",
    "周围的空气又湿又冷，静得让人发慌。",
    "他只是等着，等一个不知道会不会来的结果。",
    "光线越来越暗，影子拉得很长。",
    "潮气贴在皮肤上，凉丝丝的。",
]


def static_paragraphs(n, min_chars_each):
    """生成 n 个互不相同、内容明显静态/等待的段落，每段不少于 min_chars_each 字。"""
    paras = []
    idx = 0
    total = len(STATIC_SENTENCES)
    for _ in range(n):
        s = ""
        while len(s) < min_chars_each:
            s += STATIC_SENTENCES[idx % total]
            idx += 1
        paras.append(s)
    return paras


DYNAMIC_PARAGRAPH = (
    "「把钱放下。」他往前逼了一步，刀尖抵住对方的喉咙。"
    "对方脸色发白，手一抖，包裹掉在地上。他弯腰捡起来，打开看了一眼——"
    "里面是三万块，比说好的多了一倍。"
    "「多出来的是封口费。」对方咽了口唾沫，「你要是不收，明天你全家都别想活。」"
    "他盯着那叠钱看了三秒，然后把钱塞回对方怀里。"
    "「转告你老板，这事我没看见。下一次，我看见的就是他人头。」"
)


class TestDeadWaterParagraph(unittest.TestCase):
    def _chapter_from_paragraphs(self, paragraphs):
        title = "## 第3章 死水段测试"
        return title + "\n\n" + "\n\n".join(paragraphs) + "\n"

    def test_three_static_paragraphs_over_150_chars_triggers_level2(self):
        paras = static_paragraphs(3, 55)  # 3 段 × ≥55 ≈ ≥165 番茄字符
        total = sum(len(re.sub(r"\s", "", p)) for p in paras)
        self.assertGreaterEqual(total, 150)
        result = run_scan(self._chapter_from_paragraphs(paras))
        dw = hits_of_type(result, "疑似死水段")
        self.assertTrue(
            dw,
            "连续 ≥3 个明显静态/等待段且累计 ≥150 番茄字符，应命中 疑似死水段",
        )
        self.assertEqual(
            dw[0].get("level"),
            2,
            "疑似死水段是保守提示（level=2），不得作为 level=1 阻塞",
        )

    def test_conflict_decision_text_is_not_flagged(self):
        # 带明确选择/结果/冲突变化的文本不得误报为死水段
        result = run_scan(self._chapter_from_paragraphs([DYNAMIC_PARAGRAPH] * 3))
        self.assertEqual(
            hits_of_type(result, "疑似死水段"),
            [],
            "含明确冲突/决策/结果的段落不得误报 疑似死水段",
        )

    def test_two_paragraphs_below_count_threshold_not_flagged(self):
        # 仅 2 个静态段（即使累计 ≥150 字），未达「至少 3 段」阈值，不得命中
        paras = static_paragraphs(2, 85)  # 2 段 × ≥85 ≈ ≥170 字，但段数不足 3
        total = sum(len(re.sub(r"\s", "", p)) for p in paras)
        self.assertGreaterEqual(total, 150)
        result = run_scan(self._chapter_from_paragraphs(paras))
        self.assertEqual(
            hits_of_type(result, "疑似死水段"),
            [],
            "段数 <3 不得命中 疑似死水段",
        )

    def test_three_paragraphs_under_150_chars_not_flagged(self):
        # 3 个静态段但累计 <150 字，未达字符阈值，不得命中
        paras = static_paragraphs(3, 38)  # 3 段 × ≥38 ≈ ≥114 字，但 <150
        total = sum(len(re.sub(r"\s", "", p)) for p in paras)
        self.assertLess(total, 150)
        result = run_scan(self._chapter_from_paragraphs(paras))
        self.assertEqual(
            hits_of_type(result, "疑似死水段"),
            [],
            "累计 <150 番茄字符不得命中 疑似死水段",
        )


# ===========================================================================
# 契约 10：机械扫描只是提示，最终阻塞依据技能审查（不夸大语义判定）
# ===========================================================================
class TestMechanicalScanIsHintNotBlock(unittest.TestCase):
    """重复意象 / 疑似死水段 这类关键词扫描只能是 level=2 提示，
    不得被当作可靠的语义判定产生 level=1 阻塞。字数才是客观机械门禁。"""

    def test_repetition_and_deadwater_hits_never_level1(self):
        paras = static_paragraphs(3, 55)
        body = (
            "## 第4章 机械提示测试\n\n"
            + "\n\n".join(paras)
            + "\n\n他望着远处的航标灯。\n他望着远处的航标灯。\n他望着远处的航标灯。\n"
        )
        result = run_scan(body)
        mechanical = (
            hits_of_type(result, "重复意象")
            + hits_of_type(result, "疑似死水段")
        )
        self.assertTrue(mechanical, "样本应至少触发一种机械提示")
        for h in mechanical:
            self.assertNotEqual(
                h.get("level"),
                1,
                "机械关键词扫描不得产生 level=1 阻塞（type=%s）" % h.get("type"),
            )


if __name__ == "__main__":
    unittest.main()
