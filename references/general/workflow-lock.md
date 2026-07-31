# 流程锁：novel_step.sh

## 来源

2026-07-27 Ch26 复盘。连续两次违反 novel-main 7 步流程（跳 PLOT、缩 REVIEW、跳 TRACK）后创建。

## 问题

7 步流程写在 SKILL.md 里、助理脑子里——但执行时会跳步。连续创作产生的「势头压力」是主因。纸面约束挡不住。

## 解决方案

程序化状态锁：`~/.hermes/skills/novel/scripts/novel_step.sh`

```bash
# 进入每一步前
novel_step.sh check DRAFT    # ✅ PASS 或 ⚠️ BLOCKED（缺前置步骤）

# 完成每一步后
novel_step.sh done DRAFT     # 标记完成，自动推进状态
```

### 流程

```
novel_step.sh check PREP → ✅ → 执行 PREP → novel_step.sh done PREP
novel_step.sh check PLOT → ✅ → 执行 PLOT → novel_step.sh done PLOT
novel_step.sh check DRAFT → ✅ → 写骨架+预审+派发 → novel_step.sh done DRAFT
novel_step.sh check REVIEW → ✅ → 自动扫描+爽点+OOC → novel_step.sh done REVIEW
novel_step.sh check POLISH → ✅ → 打磨 → novel_step.sh done POLISH
novel_step.sh check TRACK → ✅ → 文档更新 → novel_step.sh done TRACK
novel_step.sh check MILESTONE → 5的倍数→审查 / 非5→SKIP
novel_step.sh check BACKUP → ✅ → 备份 → novel_step.sh done BACKUP（章节号自动+1）
```

### 跳步会怎样

```
novel_step.sh check DRAFT    # ⚠️ BLOCKED: 缺少前置步骤 PLOT
novel_step.sh done PLOT      # 🛑 产出物校验失败: 剧情推演/第N章.md 不存在或<200字节
novel_step.sh done REVIEW    # 🛑 产出物校验失败: 审查报告/第N章.md 不存在
```

### 产出物校验（v2 — 2026-07-27）

done 时额外校验产出物文件：

| 步骤 | 校验文件 | 规则 |
|------|---------|------|
| PLOT | `00-大纲细纲/剧情推演/第N章.md` | 存在且 >200 字节 |
| REVIEW | `05-审查报告/审查报告_第N章.md` | 存在 |
| POLISH | `01-正文存稿/第N章.md` | 存在 |

MILESTONE 5的倍数章自动豁免，BACKUP 自动补标记。

### DRAFT 骨架数字验证（v3 — 2026-08-01）

`done DRAFT` 和 `validate` 模式额外执行骨架数字验证：

1. **结算公式校验**：内嵌 Python，检查 `人口×系数×0.10=结算` 是否匹配
2. **违禁词/地名/面板检查**：委托给 `review_scan.py --book <书名>`

> ⚠️ **违禁词/地名列表不能硬编码在 novel_step.sh 里。** 早期版本在脚本内嵌 Python 中硬编码了 `banned_sys` 和 `forbidden` 列表，违反「解耦铁律」——这些列表应从 `书配置.md` 动态读取。已改为调用 `review_scan.py`（从书配置读取规则）。
>
> 如果 `review_scan.py` 不存在，脚本会打印警告但**不阻断**（降级运行）。只有结算公式错误或 `review_scan.py` 返回非零退出码才会阻断 `done DRAFT`。

脚本路径：`~/.hermes/skills/novel/scripts/novel_step.sh`（实际文件在 `~/novels/`，技能目录下的 `scripts/novel_step.sh` 是软链/副本）。

## 相关文件

- 进度 JSON: `~/.hermes/skills/novel/_state/<书名>_progress.json`
- 活跃书: `~/.hermes/skills/novel/_state/current_book.txt`
