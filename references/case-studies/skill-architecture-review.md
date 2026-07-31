# 技能框架架构审查与重构方法论

> 来源：2026-08-01 小说创作系统架构重构（10 扁平 md + 8 子目录 → 统一子目录结构，6 个超大文件瘦身）。
> 前置：先完成解耦（见 `skill-decoupling-patterns.md`），再谈结构重构。解耦解决"内容绑定实例"，架构重构解决"结构不可维护"。

## 触发场景

- 技能库经过多轮迭代后：文件形态混乱、单个文件过大、内容重复、脚本位置分裂
- 准备开源分享前（结构问题会让别人 clone 后跑不起来）
- 用户说"技能要结构化体系化、要有优秀的架构"

## 诊断维度（动手前先调查，用户铁律：大改动一定要调查清楚）

### 1. 结构统一性：扁平 md vs 子目录 SKILL.md

| 形态 | skill_view 按 name 加载 | skills_list 发现 |
|------|:---:|:---:|
| 子目录 `name/SKILL.md` | ✅ | ✅（出现在可用技能列表） |
| 扁平 `name.md` | ✅（按路径可加载） | ❌（发现层面不可见） |

**核心问题**：扁平技能靠入口技能手动指路，触发链依赖 SOUL.md 硬编码的 `skill_view(name)`。统一为子目录后，`skill_view(name)` 仍有效（按 name 加载不受形态影响），所以迁移是安全的。

### 2. 文件大小（Hermes 建议 8-15KB）

```bash
for f in *.md */SKILL.md; do echo "$(wc -c < "$f") $f"; done | sort -rn | head
```
> 20KB+ = 警告；40KB+ = 必须瘦身（每次 skill_view 加载 40KB ≈ 10k tokens，加载整个流水线要 50k+ tokens）。

### 3. 重复内容（单一事实源违背）

```bash
find . -name '*.md' | xargs -I{} basename {} | sort | uniq -d
```
典型：同一概念两份文档（读者审查标准、workflow-lock），必然漂移。

### 4. 脚本位置分裂

- 技能目录 `scripts/` 只有部分脚本，另一部分在 `_shared/scripts/` → 开源时别人 clone 了技能包却跑不起来
- 检查：`grep -rn '_shared/scripts' --include='*.md' . | wc -l` 看引用量决定迁移方案

### 5. references 分类不清

- 通用方法论（零特定数据）与特定项目复盘混在同一目录 → 按 `references/general/` 与 `references/case-studies/` 分目录
- 判据：`grep -l '特定书籍\|特定项目' references/*.md` 区分两类

## 重构安全协议（用户偏好的工作流）

> 用户原话："大改动一定要调查清楚，好好改，不要乱来，谨慎优化然后做回测做审查。"

### 第1步：备份保护（不可跳过）

```bash
git add -A && git commit -m "chore: 重构前备份 — 当前稳定状态"
git tag arch-before-restructure   # 随时可回滚
```

### 第2步：调查（写计划前必须完成）

- 全部技能的 frontmatter 有效性（`head -1` 是否 `---`、name 是否匹配）
- 技能间引用关系图（`grep -o 'novel-[a-z-]*'` 每个文件 → 谁引用谁）
- 外部引用（SOUL.md、cron jobs）——确认改动影响面
- 脚本引用点计数（决定迁移方案）

### 第3步：写详细实施计划

- 每个任务独立 commit、独立回退
- 明确每个文件的瘦身目标和引用替换清单
- 禁止占位符：每个步骤给出精确命令和预期输出

### 第4步：每任务独立 commit 执行

结构迁移（mv → 子目录）、瘦身、去重、引用更新分任务做，每个任务验证后 commit。

### 第5步：脚本迁移的软链接兼容方案

脚本实体迁移会破坏大量引用（20+ 处）——**用软链接保兼容**：

```bash
# 实体移到技能目录
mv ~/.hermes/skills/novel/scripts/xxx.py ~/.hermes/skills/novel/scripts/
# 旧位置留软链接（现有引用不破坏）
ln -s ~/.hermes/skills/novel/scripts/xxx.py ~/.hermes/skills/novel/scripts/xxx.py
```

> 好处：开源时脚本在技能包内（别人能跑）；本机旧路径引用依然有效（软链接指向新位置）。新代码优先写新路径，README 保留兼容说明。

### 第6步：全量回测（用真实数据，不用样例）

```bash
# 脚本链路（真实书数据）
python3 scripts/review_scan.py <真实章节> --book <真实书名>      # config_loaded=True
python3 scripts/consistency_check.py --book <真实书名>            # 7维全通过
bash scripts/novel_step.sh check <步骤>                           # 流程锁正常
# 软链接兼容
bash ~/.hermes/skills/novel/scripts/novel_step.sh check <步骤>          # 旧路径仍可用
# skill_view 抽查迁移后的技能
```

### 第7步：独立审查（多轮审查闭环）

1. 派 delegate_task 独立审查：结构统一性 / 引用完整性 / 脚本路径一致性 / 瘦身效果 / 硬编码残留 / 配置引用完整性
2. 审查发现的问题立即修复
3. 修复后复检到零；最终 commit + 打 tag

## 常见陷阱

| 陷阱 | 现实 |
|------|------|
| "迁移后 skill_view 会失效" | 不会——按 name 加载不受文件形态影响 |
| "直接改，别调查" | 用户明确反对。调查清楚是重构的前提，不是浪费时间 |
| "脚本直接删 _shared 的" | 会破坏 cron/其他流程引用。用软链接保兼容 |
| "一次性全改完再验证" | 每任务独立 commit，才能单独回退 |
| 信任子任务的"完成"自述 | 主 agent 必须 grep 独立验证到零 |
