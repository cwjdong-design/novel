# -*- coding: utf-8 -*-
"""
RED 测试套件 — 六个 SKILL.md 的新契约（字数口径 / 容量门禁 / 反机械规则）。

本套件把「每章番茄显示字数 2200—2400，目标 2250；2200 字必须由有效剧情构成，
禁止环境/机械动作/等待/回忆/重复确认凑字」这条链路固化为可检验的文档契约。

当前六个 SKILL.md 仍是旧口径（2000-3000 / 目标2500 / 约2500 / 2200-2800；
draft 强制每轮插动作与每 200 字微钩子；polish 有「环境细节补字」与五感密度配额；
main 无容量预审），因此本套件在当前实现下应当【失败】——
失败原因应是「新规则尚未写入文档」，而非语法错误。

实现各 SKILL.md 改造后，测试应转绿。
运行：python3 -m pytest tests -q  或  python3 -m unittest discover -s tests -v
"""

import re
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

SIX_SKILLS = [
    "novel-plot",
    "novel-skeleton",
    "novel-draft",
    "novel-review",
    "novel-polish",
    "novel-main",
]


def skill_text(name):
    return (REPO / name / "SKILL.md").read_text(encoding="utf-8")


SKILLS = {name: skill_text(name) for name in SIX_SKILLS}


# ---------------------------------------------------------------------------
# 通用谓词
# ---------------------------------------------------------------------------
def has_wordcount_range(text):
    """统一口径「2200—2400」（容忍 - — – ~ 到 至 等连接符）。"""
    return re.search(r"2200\s*[-—–~到至]\s*2400", text) is not None


def has_target_2250(text):
    """「目标 2250」或等价明确表述（目标 与 2250 在 8 字以内邻近）。"""
    return re.search(r"目标[^0-9\n]{0,8}2250|2250[^0-9\n]{0,8}目标", text) is not None


def normalized(text):
    return re.sub(r"\s+", "", text)


FORBIDDEN_OLD_CALIBER = ["2000-3000", "2200-2800", "目标2500", "约2500"]


def forbidden_old_caliber_hits(text):
    norm = normalized(text)
    return [p for p in FORBIDDEN_OLD_CALIBER if p in norm]


# ===========================================================================
# 契约 4：六个 SKILL.md 的字数口径
# ===========================================================================
class TestWordCountCaliber(unittest.TestCase):
    def test_all_six_have_unified_range_2200_2400(self):
        missing = [n for n in SIX_SKILLS if not has_wordcount_range(SKILLS[n])]
        self.assertEqual(
            missing, [],
            "以下文件缺少统一口径「2200—2400」：%r" % missing,
        )

    def test_all_six_have_target_2250(self):
        missing = [n for n in SIX_SKILLS if not has_target_2250(SKILLS[n])]
        self.assertEqual(
            missing, [],
            "以下文件缺少「目标 2250」或等价表述：%r" % missing,
        )

    def test_no_skill_keeps_old_caliber_as_current_rule(self):
        offenders = {
            n: forbidden_old_caliber_hits(SKILLS[n])
            for n in SIX_SKILLS
            if forbidden_old_caliber_hits(SKILLS[n])
        }
        self.assertEqual(
            offenders, {},
            "以下文件仍保留旧口径（2000-3000/2200-2800/目标2500/约2500）：%r"
            % offenders,
        )


# ===========================================================================
# 契约 5：plot / skeleton 必须含有效剧情容量门禁
# ===========================================================================
class TestPlotSkeletonCapacityGate(unittest.TestCase):
    def _has_min_rounds(self, text):
        # 至少 4 个有效剧情回合
        return "回合" in text and re.search(
            r"(?:至少|≥|>=)\s*4|4\s*(?:个|次)\s*(?:有效)?回合|四个(?:有效)?回合|4回合",
            text,
        ) is not None

    def _has_min_changes(self, text):
        # 至少 3 次局势/利益变化
        return re.search(
            r"(?:局势|利益)[^。\n]{0,8}(?:变化|变动|转变|更替|转换)", text,
        ) is not None or (
            re.search(r"(?:至少|≥|>=)\s*3", text)
            and ("局势" in text or "利益" in text or "变化" in text)
        )

    def _has_protagonist_decision(self, text):
        # 至少 1 次主角主动决策
        return "主动" in text and re.search(r"决策|选择|抉择|决定", text) is not None

    def _has_capacity_block_before_draft(self, text):
        # 容量不足不得进入 DRAFT（草稿/填肉）
        return (
            "容量" in text
            and re.search(r"(?:不足|不够|未达标|缺|不达标)", text) is not None
            and re.search(r"DRAFT|草稿|填肉|正文", text) is not None
            and re.search(r"(?:不得|禁止|不能|不可|阻断|拦截|回退|回到|退回)", text) is not None
        )

    def _assert_capacity_gate(self, name):
        text = SKILLS[name]
        self.assertTrue(self._has_min_rounds(text), "%s 缺少「至少4个有效剧情回合」门禁" % name)
        self.assertTrue(self._has_min_changes(text), "%s 缺少「至少3次局势/利益变化」门禁" % name)
        self.assertTrue(self._has_protagonist_decision(text), "%s 缺少「主角主动决策」门禁" % name)
        self.assertTrue(
            self._has_capacity_block_before_draft(text),
            "%s 缺少「容量不足不得进入 DRAFT」门禁" % name,
        )

    def test_plot_has_capacity_gate(self):
        self._assert_capacity_gate("novel-plot")

    def test_skeleton_has_capacity_gate(self):
        self._assert_capacity_gate("novel-skeleton")


# ===========================================================================
# 契约 6：draft 必须明确禁止机械规则
# ===========================================================================
class TestDraftForbidsMechanicalRules(unittest.TestCase):
    def setUp(self):
        self.text = SKILLS["novel-draft"]

    def test_forbids_action_per_dialogue_turn(self):
        # 不得强制每轮对话插动作；需有明确「不强制/不要求」表述
        ok = re.search(
            r"不(?:强制|强求|要求|必)[^\n]{0,25}(?:每轮|每(?:个)?说话者|对话)[^\n]{0,25}动作"
            r"|禁止[^\n]{0,25}(?:强制)?[^\n]{0,10}(?:每轮|每(?:个)?说话者|对话)[^\n]{0,25}动作",
            self.text,
        )
        self.assertTrue(ok, "draft 须明确禁止「强制每轮对话插动作」")

    def test_forbids_200char_microhook_quota(self):
        ok = re.search(
            r"不(?:要求|强制|必)[^\n]{0,12}200字[^\n]{0,12}(?:微)?钩子"
            r"|不再要求[^\n]{0,12}(?:微钩子|200字)"
            r"|禁止[^\n]{0,12}200字[^\n]{0,12}(?:微)?钩子",
            self.text,
        )
        self.assertTrue(ok, "draft 须明确禁止「要求每 200 字微钩子」")

    def test_wordcount_gap_filled_only_by_effective_content(self):
        # 字数不足只能加有效冲突回合/主动决策/反方应对/收益反馈
        has_effective = re.search(r"有效[^\n]{0,6}(?:冲突|回合)|反方应对|收益反馈|主动决策", self.text)
        has_gap_context = re.search(r"字数[^\n]{0,6}(?:不足|不够|缺)|(?:不足|不够|缺)[^\n]{0,6}字数|补字|凑字|增.{0,4}有效", self.text)
        self.assertTrue(has_effective, "draft 须说明字数不足靠有效回合/决策/反方应对/收益反馈补足")
        self.assertTrue(has_gap_context, "draft 须在字数不足语境下给出补足手段")

    def test_forbids_padding_with_environment_waiting_memory_repeat(self):
        # 禁止用环境/等待/回忆/重复确认凑字
        ok = re.search(
            r"(?:禁止|不得|不能|不可|严禁)[^\n]{0,40}(?:环境|等待|回忆|重复确认)[^\n]{0,30}(?:补字|凑字|填充|凑|补)",
            self.text,
        )
        self.assertTrue(ok, "draft 须明确禁止用环境/等待/回忆/重复确认凑字")


# ===========================================================================
# 契约 7：review 必须把字数达标与有效内容分开验收
# ===========================================================================
class TestReviewSeparatesCountAndContent(unittest.TestCase):
    def setUp(self):
        self.text = SKILLS["novel-review"]

    def test_separates_wordcount_from_effective_content(self):
        self.assertIn("有效", self.text, "review 须引入「有效内容/密度」概念")
        self.assertTrue(
            re.search(r"分开|分别|独立|双门槛|两道门槛", self.text),
            "review 须把字数达标与有效内容分开/分别验收",
        )

    def test_requires_change_every_500_chars(self):
        self.assertTrue(
            re.search(r"500\s*字", self.text)
            and re.search(r"(?:局势|利益|变化)", self.text),
            "review 须含「每 500 字至少一次局势/利益变化」",
        )

    def test_flags_150char_deadwater_run(self):
        self.assertTrue(
            re.search(r"150\s*字", self.text) and "死水" in self.text,
            "review 须含「连续 150 字疑似死水段」检查",
        )

    def test_same_fact_once(self):
        self.assertTrue(
            re.search(r"同一事实|同一个事实", self.text)
            and re.search(r"(?:一次|一遍|不得重复|只(?:能|许)?一次)", self.text),
            "review 须含「同一事实原则上一次」",
        )

    def test_same_imagery_max_twice(self):
        self.assertTrue(
            "意象" in self.text
            and re.search(r"(?:最多|至多|不超过|≤)\s*2\s*(?:次|处)?|2\s*次|两次", self.text),
            "review 须含「同一意象最多 2 次」",
        )

    def test_payoff_two_of_three(self):
        self.assertTrue(
            "爽点" in self.text
            and re.search(r"三选二|2\s*/\s*3|二选一以上|至少.{0,3}二|满足其[中二].{0,4}[23]", self.text),
            "review 须含「爽点兑现三选二」",
        )

    def test_static_lyric_not_chapter_hook(self):
        self.assertTrue(
            "抒情" in self.text
            and "钩子" in self.text
            and re.search(r"静态|不(?:算|计为|作为)", self.text),
            "review 须含「静态抒情不算章末钩子」",
        )

    def test_substantive_padding_is_blocking(self):
        self.assertTrue(
            "注水" in self.text
            and re.search(r"阻塞|一级|必须修改|不通过|🔴", self.text),
            "review 须把命中实质注水判为阻塞问题（一级）",
        )


# ===========================================================================
# 契约 8：polish 删除环境补字策略、容量不足退回、不强制机械配额
# ===========================================================================
class TestPolishRemovesPaddingStrategy(unittest.TestCase):
    def setUp(self):
        self.text = SKILLS["novel-polish"]

    def test_removes_environment_detail_padding(self):
        # 旧策略「扩写…环境细节」补字必须删除
        self.assertIsNone(
            re.search(r"扩写[^\n]{0,20}环境", self.text),
            "polish 不得保留「扩写环境细节」补字策略",
        )

    def test_capacity_gap_returns_to_plot_skeleton(self):
        # 容量不足应退回 plot/skeleton 补有效回合
        has_return = re.search(r"退回|回到|回退|返回", self.text)
        has_upstream = re.search(r"plot|骨架|skeleton", self.text, re.IGNORECASE)
        self.assertTrue(
            has_return and has_upstream,
            "polish 容量不足须退回 plot/skeleton 补有效回合",
        )

    def test_no_mandatory_body_action_per_turn(self):
        # 不得强制「每轮/连续两句之间必须插入身体语言」
        self.assertIsNone(
            re.search(r"(?:必须|都要|都得|一律)[^\n]{0,30}身体语言", self.text),
            "polish 不得强制每轮插入身体语言",
        )
        self.assertNotIn(
            "两句之间必须插入", self.text,
            "polish 不得保留「两句之间必须插入」硬性配额",
        )

    def test_no_minimum_five_sense_density(self):
        # 不得强制最低五感密度配额
        self.assertNotIn(
            "每个新场景至少", self.text,
            "polish 不得保留「每个新场景至少 X 处」五感密度配额",
        )


# ===========================================================================
# 契约 9：main 串起 容量预审 → DRAFT → 字数+有效密度双门槛
# ===========================================================================
class TestMainPipelineAndDualGate(unittest.TestCase):
    def setUp(self):
        self.text = SKILLS["novel-main"]

    def test_has_capacity_precheck(self):
        self.assertTrue(
            "容量" in self.text
            and re.search(r"预审|门禁|审核|检查", self.text),
            "main 须有「容量预审/门禁」环节",
        )

    def test_draft_has_wordcount_and_effective_density_dual_gate(self):
        self.assertIn("字数", self.text)
        self.assertIn("有效", self.text)
        self.assertIn("密度", self.text)
        self.assertTrue(
            re.search(r"双门槛|两道门槛|字数.{0,12}有效.{0,12}密度|有效.{0,8}密度", self.text),
            "main DRAFT 须设「字数 + 有效密度」双门槛",
        )

    def test_capacity_gap_returns_to_plot_skeleton(self):
        self.assertIn("容量", self.text)
        self.assertTrue(
            re.search(r"(?:不足|不够|未达标)", self.text)
            and re.search(r"plot|骨架|skeleton", self.text, re.IGNORECASE)
            and re.search(r"退回|回到|回退|返回|不得进入|回 ?PLOT", self.text),
            "main 容量不足须回 plot/skeleton",
        )

    def test_cannot_rely_on_polish_to_pad_environment(self):
        self.assertIn("POLISH", self.text.upper())
        self.assertIn("环境", self.text)
        self.assertTrue(
            re.search(r"(?:不能|不得|禁止|不可)", self.text),
            "main 须明确「不能靠 POLISH 补环境」",
        )


if __name__ == "__main__":
    unittest.main()
