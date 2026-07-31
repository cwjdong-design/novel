# 小说技能架构重构实现计划

> **面向 AI 代理的工作者：** 必需子技能：使用 subagent-driven-development（推荐）或 executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** 将小说创作技能从「扁平 md + 子目录混用」重构为「统一子目录结构」，并对 6 个超大文件瘦身，去重、收拢脚本，同时保持 SOUL.md 触发链和现有写作流程完全不受影响。

**架构：** 
- 10 个扁平 md → `novel-xxx/SKILL.md` 子目录结构（frontmatter 的 name 不变，skill_view(name) 触发不受影响）
- 6 个超大文件（>15KB）瘦身：删除内嵌代码/历史记录/长示例，核心方法论保留
- 脚本实体收拢到技能目录 `scripts/`，`_shared/scripts/` 保留软链接（不破坏现有引用）
- references 分 `general/`（通用）和 `case-studies/`（特定书复盘）

**技术栈：** bash（mv/mkdir/ln -s）、python3（脚本验证）、git（版本管理）、grep（残留检查）

**当前状态备份：** git tag `arch-before-restructure`（d652aa3），随时可回滚。

---

## 目标目录结构

```
~/.hermes/skills/novel/
├── README.md
├── novel-writing/SKILL.md          # 入口+路由（保留，微调引用）
├── novel-main/SKILL.md             # 调度器（37KB→15KB内）
├── novel-prep/SKILL.md             # 12.8KB 直接迁移
├── novel-plot/SKILL.md             # 25KB→15KB内
├── novel-draft/SKILL.md            # 42KB→20KB内（重点瘦身）
├── novel-review/SKILL.md           # 25KB→18KB内
├── novel-polish/SKILL.md           # 18.5KB 微调
├── novel-track/SKILL.md            # 17.7KB 微调
├── novel-backup/SKILL.md           # 8.5KB 直接迁移
├── novel-new-book/SKILL.md         # 16KB 微调
├── novel-cron/SKILL.md             # 47KB→10KB内（删内嵌代码）
├── novel-character/SKILL.md        # 保留不动
├── novel-platform/SKILL.md         # 保留不动
├── novel-editing-patterns/SKILL.md # 保留，更新脚本引用
├── novel-skeleton/SKILL.md         # 保留，更新脚本引用
├── novel-publishing/SKILL.md       # 保留不动
├── fanqie-publisher/SKILL.md       # 保留，更新脚本引用
├── scripts/                        # 脚本实体（10个+review_scan）
├── knowledge/                      # 保留（读者审查标准去重）
├── templates/                      # 保留
├── references/
│   ├── general/                    # 7个通用方法论
│   └── case-studies/               # 25个特定书复盘
├── LICENSE
├── .gitignore
└── requirements.txt
```

---

## 任务分解

### 任务 1：扁平 md → 子目录结构（10 个）

**文件：**
- 迁移：`novel-main.md` `novel-prep.md` `novel-plot.md` `novel-draft.md` `novel-review.md` `novel-polish.md` `novel-track.md` `novel-backup.md` `novel-new-book.md` `novel-cron.md`

- [ ] **步骤 1：创建目录并移动文件**

```bash
cd ~/.hermes/skills/novel
for name in main prep plot draft review polish track backup new-book cron; do
  mkdir -p "novel-$name"
  mv "novel-$name.md" "novel-$name/SKILL.md"
done
```

- [ ] **步骤 2：验证每个 SKILL.md 的 frontmatter 完整**

```bash
cd ~/.hermes/skills/novel
for d in novel-main novel-prep novel-plot novel-draft novel-review novel-polish novel-track novel-backup novel-new-book novel-cron; do
  echo "→ $d: $(head -1 $d/SKILL.md) | name=$(grep '^name:' $d/SKILL.md | awk '{print $2}')"
done
```
预期：每个都以 `---` 开头，name 与目录名一致。

- [ ] **步骤 3：验证 skill_view 加载**

用 `skill_view(name='novel-main')` 抽查 3 个迁移后的技能，确认能按 name 加载（新会话生效）。

- [ ] **步骤 4：Commit**

```bash
git add -A && git commit -m "refactor: 10个扁平技能迁移为子目录结构"
```

---

### 任务 2：瘦身 novel-cron（47KB→10KB内）

**文件：**
- 修改：`novel-cron/SKILL.md`

- [ ] **步骤 1：读取全文，标记可删除区块**

novel-cron 主体是内嵌代码（novel_scan.py / foreshadow_check.py / chapter_stats.py / trending_news.py / ai_score.py 的完整实现），这些代码已在 `~/novels/_shared/scripts/` 有实体。删除所有 `### 代码块` 中的完整脚本实现，只保留：
- 触发说明
- 每个脚本的调用命令
- 备份策略简述
- 与 novel-backup 的协作关系

- [ ] **步骤 2：重写 SKILL.md**

保留：触发条件、Cron 配置建议、备份范围/命令、各脚本的用法接口、日志位置。
删除：全部内嵌 Python/Bash 完整实现（以「脚本已外置到 scripts/，用法见下」替代）。

- [ ] **步骤 3：验证体积**

```bash
wc -c novel-cron/SKILL.md
```
预期：< 10000B

- [ ] **步骤 4：验证引用完整性**

```bash
grep -n 'novel_scan.py\|foreshadow_check.py\|chapter_stats.py\|trending_news.py\|ai_score.py' novel-cron/SKILL.md
```
预期：引用仍在（指向脚本文件），只是不再内嵌代码。

- [ ] **步骤 5：Commit**

```bash
git add -A && git commit -m "refactor: novel-cron 瘦身 47KB→10KB，删除内嵌代码"
```

---

### 任务 3：瘦身 novel-draft（42KB→20KB内）

**文件：**
- 修改：`novel-draft/SKILL.md`

- [ ] **步骤 1：分析内容分布**

novel-draft 含：去AI味铁律（禁用词/句式/抽象表达表）、故意错别字规则、平台红线、对话规范（含方言框架）、段落节奏、钩子模板、章节结构（2500字布局+黄金三章）。

瘦身策略：
- §一 去AI味铁律：禁用词表保留（这是核心），但每个表的「反例/正例」列可以压缩——保留 1-2 个最典型示例，其余删除
- §二 故意错别字规则：压缩示例
- §2.5 平台红线：保留清单，压缩说明
- §3.5 方言框架：保留方法论，压缩词表示例
- §五 钩子模板：保留 5 种类型模板（核心），压缩说明文字
- §六 章节结构：黄金三章保留（核心），常规章节结构压缩

- [ ] **步骤 2：执行压缩**

用 `patch` 逐节压缩，每次压缩后 `wc -c` 检查进度。

- [ ] **步骤 3：验证核心内容不丢失**

```bash
grep -c '禁用词\|禁用句式\|钩子\|黄金三章\|对话占比\|40%' novel-draft/SKILL.md
```
预期：所有核心关键词仍在。

- [ ] **步骤 4：Commit**

```bash
git add -A && git commit -m "refactor: novel-draft 瘦身 42KB→20KB"
```

---

### 任务 4：瘦身 novel-main（37KB→15KB内）

**文件：**
- 修改：`novel-main/SKILL.md`

- [ ] **步骤 1：删除修改记录**

文件开头的 HTML 注释（`<!-- 修改记录 -->`）约 15 行历史记录 → 全部删除（历史在 git 里）。

- [ ] **步骤 2：进度 JSON 格式外置**

「中间状态保存与中断恢复」章节里的完整 JSON 示例（约 40 行）→ 移到 `references/general/progress-format.md`，SKILL.md 保留字段说明和指向。

- [ ] **步骤 3：压缩各步骤的重复说明**

每个步骤的「失败 Fallback」「自动化」重复出现 → 统一为表格，删除重复段落。

- [ ] **步骤 4：Commit**

```bash
git add -A && git commit -m "refactor: novel-main 瘦身 37KB→15KB"
```

---

### 任务 5：瘦身 novel-plot（25KB→15KB内）+ novel-review（25KB→18KB内）

**文件：**
- 修改：`novel-plot/SKILL.md` `novel-review/SKILL.md`

- [ ] **步骤 1：novel-plot 压缩**

novel-plot 大量示例（跨章冲突升级曲线、连环伏笔 A→B→C 的完整案例）→ 每个保留 1 个典型示例，删除重复展示。

- [ ] **步骤 2：novel-review 压缩**

违禁词库完整清单（§3.1-3.5 约 80 行表格）→ 改为「违禁词见 knowledge/违禁词库.json」，SKILL.md 只保留分类说明和检测流程。

- [ ] **步骤 3：Commit**

```bash
git add -A && git commit -m "refactor: novel-plot/novel-review 瘦身"
```

---

### 任务 6：references 分类

**文件：**
- 移动：`novel-writing/references/*` → `references/general/` 或 `references/case-studies/`
- 移动：`novel-editing-patterns/references/*` → 同上
- 删除：`knowledge/读者审查标准.md`（旧 1719B，与 references 版重复）

- [ ] **步骤 1：创建分类目录**

```bash
cd ~/.hermes/skills/novel
mkdir -p references/general references/case-studies
```

- [ ] **步骤 2：移动通用方法论（7个）**

```bash
cd ~/.hermes/skills/novel/novel-writing/references
mv batch-text-normalization.md cross-file-update-checklist.md multi-file-skill-debugging.md script-health-check.md skill-iteration-workflow.md workflow-lock.md writing-rhythm.md ../../references/general/
```

- [ ] **步骤 3：移动特定书复盘（25个）**

```bash
cd ~/.hermes/skills/novel/novel-writing/references
mv $(ls *.md | grep -v -E 'batch-text-normalization|cross-file-update-checklist|multi-file-skill-debugging|script-health-check|skill-iteration-workflow|workflow-lock|writing-rhythm') ../../references/case-studies/
cd ~/.hermes/skills/novel/novel-editing-patterns/references
mv *.md ../../references/case-studies/ 2>/dev/null || true
```

- [ ] **步骤 4：更新引用**

所有 `references/xxx.md` 的相对引用 → 更新为 `references/general/xxx.md` 或 `references/case-studies/xxx.md`。

- [ ] **步骤 5：删除重复的 knowledge/读者审查标准.md**

```bash
rm ~/.hermes/skills/novel/knowledge/读者审查标准.md
```

- [ ] **步骤 6：Commit**

```bash
git add -A && git commit -m "refactor: references 分类为 general/case-studies + 去重"
```

---

### 任务 7：脚本收拢 + 软链接

**文件：**
- 移动：`~/novels/_shared/scripts/{consistency_check,backup_chapter,novel_scan,foreshadow_check,ai_score,chapter_stats,trending_news,novel_step,novel_check,publish_chapter}.py/.sh` → `~/.hermes/skills/novel/scripts/`
- 创建：`~/novels/_shared/scripts/` 下的软链接指向新位置
- 删除：`novel-writing/scripts/novel_step.sh`（188B 占位符）

- [ ] **步骤 1：移动脚本实体**

```bash
cd ~/novels/_shared/scripts
for f in consistency_check.py backup_chapter.py novel_scan.py foreshadow_check.py ai_score.py chapter_stats.py trending_news.py novel_step.sh novel_check.sh publish_chapter.py; do
  mv "$f" ~/.hermes/skills/novel/scripts/
done
```

- [ ] **步骤 2：创建软链接（保持 _shared 兼容）**

```bash
cd ~/novels/_shared/scripts
for f in consistency_check.py backup_chapter.py novel_scan.py foreshadow_check.py ai_score.py chapter_stats.py trending_news.py novel_step.sh novel_check.sh publish_chapter.py; do
  ln -s ~/.hermes/skills/novel/scripts/$f $f
done
```

- [ ] **步骤 3：删除占位符**

```bash
rm ~/.hermes/skills/novel/novel-writing/scripts/novel_step.sh
```

- [ ] **步骤 4：验证脚本可执行**

```bash
python3 ~/.hermes/skills/novel/scripts/consistency_check.py --book 重生海安人口越多我越有钱 2>&1 | tail -1
bash ~/.hermes/skills/novel/scripts/novel_step.sh check DRAFT 2>&1
```
预期：与新位置路径一致（旧路径软链接也指向这里）。

- [ ] **步骤 5：Commit**

```bash
git add -A && git commit -m "refactor: 脚本收拢到技能目录 scripts/，_shared 保留软链接"
```

---

### 任务 8：全量引用更新

**文件：**
- 修改：所有引用 `_shared/scripts/xxx` 的 md 文件

- [ ] **步骤 1：列出所有引用点**

```bash
cd ~/.hermes/skills/novel
grep -rln '_shared/scripts' --include='*.md' . | grep -v '.git/'
```

- [ ] **步骤 2：逐个更新路径**

将 `~/novels/_shared/scripts/xxx` → `~/.hermes/skills/novel/scripts/xxx`（因为实体已迁移，软链接虽兼容但新路径更规范）。用 patch 逐个替换。

- [ ] **步骤 3：验证零残留旧路径引用**

```bash
grep -rn '_shared/scripts' --include='*.md' . | grep -v '.git/' | wc -l
```
预期：0（README 中说明除外，README 可保留兼容说明）

---

### 任务 9：全量回测

- [ ] **步骤 1：脚本链路回测**

```bash
python3 ~/.hermes/skills/novel/scripts/review_scan.py ~/novels/books/重生海安人口越多我越有钱/01-正文存稿/第30章.md --book 重生海安人口越多我越有钱 2>&1 | python3 -c "import sys,json;d=json.load(sys.stdin);print(f'配置:{d[\"config_loaded\"]} 白名单:{d[\"place_whitelist_count\"]}')"
python3 ~/.hermes/skills/novel/scripts/consistency_check.py --book 重生海安人口越多我越有钱 2>&1 | grep '所有维度'
python3 ~/.hermes/skills/novel/scripts/backup_chapter.py ~/novels/books/重生海安人口越多我越有钱/01-正文存稿/第30章.md 2>&1
bash ~/.hermes/skills/novel/scripts/novel_step.sh check DRAFT 2>&1
python3 ~/.hermes/skills/novel/scripts/foreshadow_check.py --book 重生海安人口越多我越有钱 2>&1 | tail -2
python3 ~/.hermes/skills/novel/scripts/chapter_stats.py --book 重生海安人口越多我越有钱 2>&1 | head -4
```

- [ ] **步骤 2：软链接兼容验证**

```bash
bash ~/novels/_shared/scripts/novel_step.sh check DRAFT 2>&1
python3 ~/novels/_shared/scripts/consistency_check.py --book 重生海安人口越多我越有钱 2>&1 | grep '所有维度'
```
预期：旧路径仍可用（软链接生效）。

- [ ] **步骤 3：技能加载验证**

`skill_view` 抽查 novel-main / novel-draft / novel-cron / novel-prep，确认迁移后能加载。

- [ ] **步骤 4：残留检查**

```bash
cd ~/.hermes/skills/novel
grep -rln '穗城\|林越\|沈知予\|287,?341' novel-*/SKILL.md knowledge/ README.md 2>/dev/null | wc -l
```
预期：0

---

### 任务 10：最终审查（独立子代理）

- [ ] **步骤 1：派发独立审查 agent**

审查内容：
1. 结构统一性（是否还有扁平 md 残留在根目录）
2. 引用完整性（所有 skill 引用能解析）
3. 脚本路径一致性（所有调用点与新位置匹配）
4. 瘦身效果（所有 SKILL.md < 25KB）
5. 硬编码残留
6. 书配置引用完整性

- [ ] **步骤 2：修复审查发现的问题**

- [ ] **步骤 3：最终 commit + tag**

```bash
git add -A && git commit -m "chore: 架构重构完成，独立审查通过"
git tag arch-restructured-v2
```

---

## 自检

**规格覆盖度：** 覆盖了结构统一（任务1）、瘦身（任务2-5）、去重分类（任务6）、脚本收拢（任务7）、引用更新（任务8）、回测（任务9）、审查（任务10）。✓

**占位符扫描：** 无 TODO/待定。✓

**风险控制：** 
- git tag 备份可回滚
- 软链接保兼容
- 每任务独立 commit，可单独回退
- 回测用真实书数据验证
