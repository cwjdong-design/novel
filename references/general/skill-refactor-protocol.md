# 技能库安全重构协议（大改动必走）

> 来源：2026-08-01 小说创作系统架构重构实战（18 技能统一子目录 + 6 文件瘦身 + 脚本收拢 + references 分类）。
> 用户铁律：大改动必须「调查清楚 → 谨慎优化 → 回测 → 独立审查」，不乱来。
> 前置：先完成解耦（见 `case-studies/skill-decoupling-patterns.md`），再谈结构重构。

## 核心事实：skill_view vs skills_list 发现不对称

- `skill_view(name='novel-xxx')` 按 name 加载**扁平 md 和子目录 SKILL.md 都行**（路径可解析）。
- `skills_list` **只列出 `目录/SKILL.md` 结构** —— 扁平 md 在技能发现层面不可见。
- 结论：技能一律用 `novel-xxx/SKILL.md` 子目录结构，不要创建扁平 `.md`。

## 体积规范（Hermes 最佳实践）

- SKILL.md 目标 8-15KB；>20KB 必须瘦身；巡检/接口类应 <10KB。
- 调度器（如 novel-main）承载全流程信息，30KB 可接受，不必强压。

## 瘦身手法（按性价比排序）

1. **版本历史 → 删除**（历史在 git 里），SKILL.md 加一行「版本历史见 git 提交记录」。
2. **内嵌代码 → 删除**（已外置 .py/.sh 实体），只留「脚本已外置到 scripts/，用法见下」+ 调用接口。
3. **JSON 格式 / 大表格 → 外置到 `references/general/`**，SKILL.md 只留要点 + 指向。
4. **示例压缩** → 每个概念保留 1 个最典型示例，删重复正反例（示例名用通用架空名，如 林夜/苏婉，不用真实书人物）。
5. **引用共享知识** → 重复词表改为指向 `knowledge/xxx.json` 或另一技能章节，不复制。
6. **重复的 Fallback/自动化说明** → 汇总为一张「用户交互策略」表。

## 安全重构协议步骤

1. **git tag 备份**（如 `arch-before-restructure`）→ 随时可回滚。
2. **先调查再动手**：
   - 引用关系图（谁引用谁，`grep -o 'novel-[a-z-]*'`）
   - 文件大小分布（`wc -c`）
   - 重复文件（同名知识在 knowledge/ 和 references/ 各一份）
   - 外部引用（SOUL.md / cron jobs.json / _state）
   - 脚本引用点全清单（每个脚本被引用几次）
3. **写 PLAN 逐任务拆解**，每个任务独立 commit，可单独回退。
4. **兼容性保障**：
   - 路径变更用软链接：实体在技能目录（git 跟踪实体），旧路径 `ln -s` 兼容。
   - 技能间引用用 name（迁移后 name 不变 → 引用链不断）。
5. **全量回测**：真实书数据跑脚本链路 + 软链接兼容（旧路径仍可调用）+ skill_view 加载抽查。
6. **派独立 subagent 审查**（结构统一/引用完整/脚本路径/瘦身质量/硬编码残留/书配置引用）。
7. **修复审查发现 → 打最终 tag**（如 `arch-restructured-v2`）。

## 批量替换要点

- 路径映射批量替换用 python 脚本（old→new dict），排除 PLAN/README（保留历史描述）。
- 替换后 grep 验证残留：核心文件应 0。
- references 分类：通用方法论 → `general/`；含特定书数据的复盘 → `case-studies/`（必须带「特定书籍复盘文档」标注）。

## 审查必查项（subagent 审查清单）

- 根目录扁平 md 残留 = 0（只留 README/PLAN）
- 空目录 = 0（旧 references 目录要 rmdir）
- 所有 `references/xxx` 引用带 `general/` 或 `case-studies/` 前缀
- 所有 SKILL.md < 30KB
- 核心 SKILL.md 特定书数据残留 = 0
- 脚本绝对路径 / BOOK_ID 硬编码 = 0
- 重复文件 = 0（尤其 knowledge/ 与 references/ 同名）
- 引用的每个文件真实存在（如 novel-cron 引用的组合脚本要真创建，不能只写路径）

## 脚本路径演进（2026-08-01）

**最终决策：不保留软链接兼容层。** 软链接有隐患（绝对路径硬编码、换机器即断、双路径语义混乱），且 git 分享时软链接根本不会被跟踪（git 只存实体）。前提是**先清零所有引用点再删**：

1. 确认引用面：SOUL.md / cron / 其他技能零引用（`grep -rn '_shared/scripts'` 全局检查）
2. 确认脚本内部互相引用已用新路径（`grep -rn 'scripts/' scripts/*.py scripts/*.sh`）
3. 更新执行文档中的旧路径描述（novel-new-book/SKILL.md）
4. 删除软链接 + `rmdir scripts`（保留 `_shared/logs` 和 `_shared/backups`）
5. 全链路回测新路径（review_scan/consistency/novel_step/foreshadow/chapter_stats/novel_daily）

**当前状态**：
- 脚本唯一权威位置：`~/.hermes/skills/novel/scripts/`（12 个，含 novel_daily.sh 组合巡检脚本）
- `~/novels/_shared/` 只有 `logs/` 和 `backups/`（日志/备份，无脚本）
- 复盘文档（case-studies/PLAN）中保留历史描述，不代表实际路径
