# 进度文件格式与中断恢复

> 供 novel-main 引用。完整的中断恢复机制说明。

## 进度文件格式

文件路径：`~/.hermes/skills/novel/_state/<书名>_progress.json`

```json
{
  "book_name": "<书名>",
  "current_chapter": 12,
  "status": "prep_completed",
  "steps_completed": ["prep", "plot"],
  "current_step": "draft",
  "prep_output": "<步骤1 的输出>",
  "plot_output": "<步骤2 的输出>",
  "draft_output": null,
  "milestone_output": null,
  "milestone_blocked": false,
  "last_updated": "2026-07-24 15:30:00",
  "retry_counts": {
    "review_polish_loop": 1
  }
}
```

## 状态枚举

| 状态 | 含义 | 恢复行为 |
|------|------|---------|
| `idle` | 未开始 | 从 PREP 开始 |
| `prep_completed` | 步骤1 完成 | 从 PLOT 开始 |
| `plot_completed` | 步骤2 完成 | 从 DRAFT 开始 |
| `draft_completed` | 步骤3 完成 | 从 REVIEW 开始 |
| `review_completed` | 步骤4 完成 | 从 POLISH 开始 |
| `polish_completed` | 步骤5 完成 | 从 TRACK 开始 |
| `track_completed` | 步骤6 完成 | 检查章节号是5的倍数→MILESTONE，否则→BACKUP |
| `milestone_completed` | 步骤7 完成（仅 5 的倍数章） | 从 BACKUP 开始 |
| `milestone_blocked` | 里程碑审查未通过 | 阻塞状态，不允许新章节；需用户修正后重新触发 |
| `completed` | 全部完成 | 展示统计（不重新执行） |
| `failed` | 某步骤失败 | 从失败步骤重试 |

## 保存时机

每步完成后自动保存进度文件。在以下节点保存：
1. PREP 输出生成后
2. PLOT 输出生成后
3. DRAFT 输出生成后
4. REVIEW 输出生成后（通过或不通过都保存）
5. POLISH 输出生成后——若上轮 REVIEW 判定不通过且循环次数 < 3，则 `current_step` 回退为 `"review"`，`steps_completed` 移除 `"review"` 和 `"polish"`，`retry_counts.review_polish_loop += 1`；否则正常推进至 TRACK
6. TRACK 完成文件写入后——章节号是 5 的倍数 → 自动进入 MILESTONE；否则 → 自动进入 BACKUP
7. MILESTONE 审查完成后（通过或不通过都保存）——通过则 `current_step` 设为 `"milestone_completed"`，进入 BACKUP；不通过则 `current_step` 设为 `"milestone_blocked"`，`status` 设为 `"failed"`，`milestone_blocked` 设为 `true`
8. BACKUP 完成后（标记 completed）

## 恢复流程

1. 用户触发 novel-main → 前置检查阶段读取 `_state/<书名>_progress.json`
2. 如果 `milestone_blocked == true` → 拦截，提示阻塞信息，不允许继续
3. 如果 `status != 'completed'` → 提示：「检测到第 X 章中断在 [步骤名]，是否从中断点继续？(Y/n)」
4. 用户确认 → 从 `current_step` 开始，跳过 `steps_completed` 中的步骤
5. 用户拒绝 → 清除进度文件，从 PREP 重新开始
6. 如果 `status == 'completed'` → 正常开始新章节

## 技能内容缓存（中断恢复优化）

为减少中断恢复时的 token 消耗，进度文件中缓存已加载的子技能内容：

1. **保存时**：每个步骤完成后，将该步骤调用的子技能内容序列化到 `cached_skills` 字段中
2. **恢复时**：先检查 `_state/<书名>_progress.json` 中 `cached_skills` 是否包含 `current_step` 对应子技能的完整内容
3. **命中缓存** → 直接使用缓存内容，不重新 `skill_view`（节省 ~2-5k tokens/步）
4. **缓存未命中** → 降级为 `skill_view(name='novel-xxx')` 重新加载

**缓存结构**（追加到进度 JSON 中）：
```json
{
  "cached_skills": {
    "novel-prep": "<已加载的 SKILL.md 完整内容>",
    "novel-plot": "<已加载的 SKILL.md 完整内容>",
    "novel-draft": null,
    "novel-review": null,
    "novel-polish": null,
    "novel-track": null,
    "novel-backup": null
  }
}
```

> **注意**：在 1M 上下文的模型下，~25k tokens（7 个子技能全量加载）不是瓶颈问题。此优化为大型项目（如多书并行、超长上下文积累）预留。
