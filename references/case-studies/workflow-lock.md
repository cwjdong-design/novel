# novel_step.sh — 流程锁 + 骨架数字验证

> ⚠️ **特定书籍复盘文档**：以下内容来源于特定书籍的实战经验，其中的章节号、人物名、地名、数字均为该书的设定。方法论部分可通用参考，但具体数据不具有普适性。

> 创建于 2026-07-27。解决连续创作时跳步和数字错误问题。

## 安装

```bash
chmod +x ~/.hermes/skills/novel/scripts/novel_step.sh
```

## 使用

```bash
# 进入步骤前检查
novel_step.sh check DRAFT   # ✅ PASS 或 ⚠️ BLOCKED

# 完成步骤后标记（自动推下一步）
novel_step.sh done DRAFT     # 标记 + 产出物校验 + 骨架数字验证

# 独立验证骨架数字
novel_step.sh validate <书名> [章节]
```

## 防跳步机制

步骤链: PREP → PLOT → DRAFT → REVIEW → POLISH → TRACK → MILESTONE → BACKUP

跳过任何步骤标记done时会被拦截。

## 产出物校验

| done STEP | 检查 |
|-----------|------|
| PLOT | `00-大纲细纲/剧情推演/第N章.md` 存在且>200字节 |
| DRAFT | `00-大纲细纲/章节骨架/第N章_骨架.md` 存在 + 数字验证 |
| REVIEW | `05-审查报告/审查报告_第N章.md` 存在 |
| POLISH | `01-正文存稿/第N章.md` 存在 |

## 骨架数字验证（done DRAFT 自动触发）

| 检查 | 说明 |
|------|------|
| 结算公式 | 面板结算 vs 287341×系数×0.10 |
| 违禁词 | 预估/检测到/建议/任务/预警/解锁/回报周期/动态上浮 |
| 真实地名 | 广州/深圳/湛江/番禺/东莞/佛山等 |
| 面板完整 | 四字段不缺 |

## 文件位置

```
~/.hermes/skills/novel/scripts/novel_step.sh   # 主脚本
~/.hermes/skills/novel/_state/          # 进度JSON
```
