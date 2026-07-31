---
name: novel-writing
description: 番茄小说创作系统入口 — 12技能体系、7步循环、去AI味、平台适配、多书管理
category: novel
---

# 番茄小说创作系统

## 路由
用户提到"写小说""开新书""写第X章"时加载本技能。

## 解耦铁律（v5.0）

> **技能文件只包含通用方法论和流程规范，不含任何特定书的设定。**
> 单本书的世界观/人物/地名/系统面板/方言配置存放在 `~/novels/books/<书名>/02-设定文档/书配置.md`。
>
> 向技能文件中写入任何角色名、地名、数字公式、面板字段名、方言词表之前，先问：这属于方法论还是属于某本书？如果是后者，写入书配置而非技能文件。
>
> 如果发现技能文件中混入了硬编码书数据，按 `references/case-studies/de-book-specificization.md` 的流程清理。

## 书配置机制（v5.0 新增）

每本书在 `~/novels/books/<书名>/02-设定文档/书配置.md` 中维护该书专属规则，供技能和审查工具读取：

| 配置项 | 说明 | 示例 |
|--------|------|------|
| 地名白名单 | 该书允许使用的架空地名列表 | 城A、城B、镇C… |
| 真实地名黑名单 | 该书对标现实区域，需屏蔽的真实地名 | 真实地名1、真实地名2… |
| 系统面板字段 | 该书系统面板的固定字段名及格式 | 字段1、字段2、字段3… |
| 方言词表 | 该书允许使用的方言词汇及用量限制 | 方言类型+词表+可用角色+频率（具体见书配置） |
| 人物库路径 | 人物卡目录位置（相对书目录） | `02-设定文档/人物卡/` |
| 大纲路径 | 大纲/细纲目录位置 | `00-大纲细纲/` |

> 技能文件中的 `review_scan.py`、`consistency_check.py` 等工具均从 `书配置.md` 读取规则。
> 技能文件本身不包含任何单本书的设定——设定由每本书自行维护。

## 技能体系

| 技能 | 用途 | 位置 |
|------|------|------|
| `novel-new-book` | 初始化新书，引导式收集世界观/人物/大纲 | `../novel-new-book/SKILL.md` |
| `novel-main` | 主技能，8步状态机统筹 | `../novel-main/SKILL.md` |
| `novel-prep` | 资料整理，上下文压缩 | `../novel-prep/SKILL.md` |
| `novel-plot` | 剧情推演 | `../novel-plot/SKILL.md` |
| `novel-character` | 人物深度塑造（弧光/Want-Need/缺陷/对话潜台词） | `../novel-character/SKILL.md` |
| `novel-draft` | 正文生成（去AI味、番茄风格） | `../novel-draft/SKILL.md` |
| `novel-review` | 6维审查（OOC/人物一致性/矛盾/违禁/伏笔/质量） | `../novel-review/SKILL.md` |
| `novel-polish` | 内容打磨 | `../novel-polish/SKILL.md` |
| `novel-track` | 状态追踪（人物/伏笔/梗概） | `../novel-track/SKILL.md` |
| `novel-platform` | 番茄平台运营（推荐池/数据指标/更新节奏/广告策略） | `../novel-platform/SKILL.md` |
| `novel-backup` | 版本备份 | `../novel-backup/SKILL.md` |
| `novel-cron` | 每日巡检（备份/违禁词/伏笔/热榜/AI味） | `../novel-cron/SKILL.md` |
| `novel-skeleton` | 章节骨架生成与派发 | `../novel-skeleton/SKILL.md` |
| `novel-editing-patterns` | 网文章节修复与质量提升模式 | `../novel-editing-patterns/SKILL.md` |
| `novel-lessons-20260725` | 写作经验与系统优化教训 | `../novel-lessons-20260725/SKILL.md` |
| `novel-publishing` | 网文平台半自动发布 | `../novel-publishing/SKILL.md` |
| `fanqie-publisher` | 番茄发布专用脚本 | `../fanqie-publisher/SKILL.md` |

> ⚠️ **结构约定（2026-08-01 重构后）**：所有技能统一为 `novel-xxx/SKILL.md` 子目录结构。**不要创建扁平 `.md`**——`skills_list` 只识别子目录技能，扁平技能在技能发现层面不可见（虽然 `skill_view` 按 name 仍可加载）。

## 知识库

| 文件 | 内容 |
|------|------|
| `knowledge/番茄风格指南.md` | 平台特征、写作铁律、去AI味规则 |
| `knowledge/opus铁律.md` | ⚠️ 骨架模式下不再注入DRAFT prompt。保留作 review 参考和最终仲裁文档。约束已固化在章节骨架中 |
| `knowledge/违禁词库.json` | 8分类违禁词(v2.1)，含系统违禁术语+AI禁用词，cron扫描用 |
| `knowledge/作者设定.md` | 作者风格与偏好 |
| `references/case-studies/读者审查标准.md` | 20年网文读者身份审查：7个必答问题、审查时机、执行命令、结果处理 |
| `references/general/writing-rhythm.md` | 写作节奏分析 |
| `references/general/workflow-lock.md` | 流程锁：novel_step.sh 防跳步机制 |
| `references/case-studies/review-checklist.md` | 8步全量一致性审查清单（每卷完成/设定变更后触发） |
| `references/case-studies/opus-hallucination-patterns.md` | opus 重写时数字/人名/地名幻觉模式及防御 |
| `references/case-studies/deep-review-tool-pitfalls.md` | 深度审查工具陷阱：白名单误报、路径、参数、跨文档同步滞后检测 |
| `references/case-studies/layout-period-slop.md` | 布局期爽点衰减检测：连续无打脸/无结算/钩子缺失/字数下降的信号阈值与对策 |

### 分卷细纲同步铁律

> **卷号铁律**：分卷结构由该书大纲定义。禁止在任何地方（骨架/章节规划/分卷细纲/口头）混淆卷号与章节号。卷末章号以大纲为准。

> ⚠️ 教训（通用）：分卷细纲与正文不同步、角色身份在细纲中与正文不一致——大纲漂移会导致 DRAFT prompt 注入错误上下文。

- **每次世界观变更后，必须对照正文重写对应卷的分卷细纲**——以正文和人物卡为权威源。
- **每完成 10 章或一卷结束后，触发全量一致性审查**（`references/case-studies/review-checklist.md`），含漂移检测。
- **章节规划同步**：MILESTONE 每 5 章强制执行维度 6——已完成章回填实际标题/事件，未来章检查占位，分卷细纲对表。章号已超过规划范围时回填优先于重规划。
- **规划漂移警告**：当实际写作路径与章节规划偏离 >2 章时，规划文件变为毒素——DRAFT 注入过时上下文导致产出与前后文脱节。预防：MILESTONE 维度 6 + PREP 时对比规划与实际状态。
- **审查工具链**（路径可配置，见 `书配置.md`）：
  | 工具 | 默认路径 | 扫描项 |
  |------|---------|--------|
  | review_scan.py | `scripts/` | 系统术语/地名白名单/真实地名黑名单/AI禁用词/章末标记/标题格式/对话框式/双引号检测 |
  | novel_scan.py | `~/.hermes/skills/novel/scripts/` | 违禁词库全面扫描 |
  | foreshadow_check.py | `~/.hermes/skills/novel/scripts/` | 伏笔超期检测 |
  | consistency_check.py | `~/.hermes/skills/novel/scripts/` | 跨文档7维校验 |

## 审查体系

> 🔒 **流程锁**：`scripts/novel_step.sh`（路径可配置）— 防跳步+产出物校验。
> 用法：`check <步骤>` 检查前置 / `done <步骤>` 标记完成。
> PLOT 拦截空壳（需 `00-大纲细纲/剧情推演/第N章.md` ≥200字节）。
> REVIEW 拦截无报告（需 `05-审查报告/审查报告_第N章.md`）。
> BACKUP 自动章节号+1，非5的倍数章自动跳过MILESTONE。

| 层级 | 工具/方法 | 触发时机 |
|------|-----------|---------|
| 自动扫描 | `scripts/review_scan.py`（可配置） | 每章 DRAFT 后自动运行（系统术语/地名白名单/真实地名黑名单/AI禁用词/章末违禁标记/标题格式） |
| 跨文档一致性 | `consistency_check.py`（可配置） | REVIEW 步骤强制执行（7维交叉校验） |
| 爽点注入 | `references/case-studies/爽点注入方法论.md` | REVIEW 步骤强制执行 5 项检查 |
| 读者审查 | `references/case-studies/读者审查标准.md` | 每 3 章 Claude Code opus 读者身份审查（7问模板+执行命令） |
| 广告打断 | `novel-platform` | 每 3 章检查章末钩子强度 |
| 人物弧光 | `novel-character` | PREP 步骤 Want/Need 追踪 |
| 全量审查 | `references/case-studies/review-checklist.md` | 每卷完成/世界观变更后：8关键字搜索+人物卡/大纲对齐 |
| 批量审查 | `references/case-studies/bulk-review-workflow.md` | 10-30章级全量批量审查：自动扫描+字数统计+爽点检查+合规检查 |
| 爽点追回 | `references/case-studies/slop-recovery-techniques.md` | 深度审查后章间飙爽点：6技法+注入SOP |
| 系统面板合规 | `书配置.md` 中定义的面板规范 | DRAFT后自动扫描 + 人工核对 |

## 8步创作循环（骨架模式·v4.0）

```
1. novel-prep    → 上下文摘要
2. novel-plot    → 剧情推演
3. novel-draft   → 正文初稿（~2500字，骨架模式）
4. novel-review  → 审查（通过/不通过）
5. novel-polish  → 打磨定稿
6. novel-track   → 状态更新
7. novel-milestone → 里程碑审查（5的倍数章）
8. novel-backup  → 版本备份
```

REVIEW↔POLISH 最多循环3次。MILESTONE 仅在 5/10/15...章触发，阻塞时标记 milestone_blocked。

## 项目路径

- 技能：`~/.hermes/skills/novel/`
- 书籍数据：`~/novels/books/<书名>/`
- 共享日志/备份：`~/novels/_shared/`
- 书专属配置：`~/novels/books/<书名>/02-设定文档/书配置.md`
- 开源基础设施：`LICENSE`(MIT) / `requirements.txt` / `.gitignore`

### 脚本调用约定（v5.0）

所有需要书特定规则的脚本使用 `--book <书名>` 参数从 `书配置.md` 加载规则：
```bash
python3 scripts/review_scan.py <章节路径> --book <书名>
python3 ~/.hermes/skills/novel/scripts/consistency_check.py --book <书名>
```
> `--config <路径>` 可直接指定书配置.md 的完整路径。书配置缺失时回退到默认规则。
> `novel_step.sh` 的 DRAFT 验证已改为委托 `review_scan.py --book`，不再内嵌硬编码列表。
| `references/general/cross-file-update-checklist.md` | 修改全局标准时必读：跨文件影响排查清单 |
| `references/case-studies/de-book-specificization.md` | 去书特定化审查流程：从技能文件中移除硬编码书数据，替换为配置引用 |
| `references/case-studies/skill-decoupling-patterns.md` | 技能解耦方法论：5步法将实例特定数据从通用技能框架中剥离（配置外置化、批量修改、grep验证）+ 开源发布流程（五类零残留验证、git初始化、回测验证、多轮审查闭环） |
| `references/case-studies/skill-architecture-review.md` | 技能框架架构审查与重构方法论：诊断维度（扁平vs子目录/文件大小/重复/脚本分裂/references分类）、重构安全协议（git tag备份→调查→分任务commit→软链接兼容→真实数据回测→独立审查） |

## 作者档案
- 风格：直接、不煽情、冷幽默、冷感叙述
- 目标平台：番茄小说
- 关键要求：去AI味、网感、故意错别字仅限对话

## 写作质量铁律

### 章节推进铁律
- **用户未明确说「继续」「写第X章」时，严禁擅自推进到下一章。**
- **用户发起世界观讨论时，停下手上所有修改，先对表。** 不要在设定未对齐时急于修章节——修完又改更费时间。对齐后再一把改完。

### DRAFT 路由规则（骨架模式）

> ⚠️ **骨架模式已取代旧自由模式。** 旧模式（大段铁律注入 + opus自由发挥）每章产生 3-5 处幻觉（数字/地名/人名/面板格式）。骨架模式降至 0-1 处，且错误来源从 opus 转移为骨架作者（可控）。

**骨架模式流程**：
1. **PREP 后生成骨架**：根据章节规划 + 人物状态 + 伏笔表写骨架（含场景顺序 / 核心事件 / 系统面板 / 章末钩子）
2. **骨架自查**：grep 扫描骨架中的地名（只用白名单）/ 数字（校对结算查表）/ 人物（校对人物库）/ 系统面板（格式从 `书配置.md` 读取）。发现非法地名即修。
3. **组装短 prompt**：骨架 + 3 条铁律（地名 / 面板 / 字数），总 1.2KB 以内。不再注入大段铁律全文。
4. **派发 opus**：`claude -p "$(cat /tmp/prompt.txt)" --model opus --max-turns 15`
5. **验证**：`review_scan.py` → 校对骨架是否忠实地执行（场景 / 面板 / 数字 / 章末）

**骨架格式**：
```markdown
## 第X章 标题

[场景1: 地点] 关键事件。人物+动作。
[场景2: 地点] 关键事件。人物+动作。

[系统面板]
【面板字段1：数值】
【面板字段2：数值】
【面板字段3：数值】
[可选附加行，≤2行]

[章末] 钩子/情绪/悬念
```

> 系统面板的具体字段名、格式规则由该书的 `书配置.md` 定义。骨架作者必须严格按 `书配置.md` 中的面板规范填写。

**铁律（只3条，注入 prompt）**：
1. 地名只用 `书配置.md` 中的白名单。禁止任何真实中国地名。
2. 系统面板原封不动。不加减行。不修改数字。
3. 字数 2000-3000。对话 ≥40%。方言用量遵从 `书配置.md` 限制（如适用）。**所有对话用「」，禁止双引号""**。冷感叙述。章末无结束标记。**禁止任何Markdown语法**：无`---`分割线、无`**加粗**`、无`` `代码块` ``、无`> 引用`、无`[]链接`。场景之间直接空行衔接，不用分隔线。番茄小说平台不支持Markdown渲染。

### 骨架作者自查清单（派发前必须执行）：
- [ ] grep 扫描骨架确认无真实地名
- [ ] **结算数字与公式匹配**：按 `书配置.md` 中定义的结算公式验证面板数字。数字不对→骨架有误→修正后重新派发。opus输出后再次验证。
- [ ] 面板格式符合 `书配置.md` 规范
- [ ] 所有人物在人物库已注册
- [ ] 场景数量 2-4 个

### 爽点铁律
- 每章 5 项：钱落地、震惊反应、打脸节奏、系统神秘化、收入对比。
- 系统是武器不是存款——钱必须花出去/被看见/被对比。
- 模板见 `references/case-studies/爽点注入方法论.md`。

### 审查前置
- DRAFT 后先跑 `review_scan.py` 扫描地名/禁用词/系统违规，零问题再人工 REVIEW。
- **扫描误报**：`review_scan.py` 可能将白名单内地名误报。人工确认白名单内即为通过。
- REVIEW **7 项清单**：时间线/存活/字数/禁用词/注册/**地名白名单**/**系统面板合规**。
- 未输出审查报告前禁止进入 POLISH/TRACK/BACKUP 及下一章。

### delegate_task 禁用
- 文字创作（DRAFT/POLISH/爽点注入）禁用 delegate_task。子代理不遵循铁律。
- 会自创地名、数字、系统功能、面板格式。
- 唯一例外：REVIEW 扫描脚本可用 delegate_task 派发（非创作类任务）。

### Claude Code 输出必须审查
- 生成正文由主 Agent 逐段审查后再展示给用户。**不得直接转发。**
- 重点：
  1. 时间线一致性（"荒了X年/月" vs 前章具体日期）→ 冲突即一级问题
  2. 人物存活状态（活人不能被写成"XX活着的时候"）
  3. 角色名一致性（grep 校验所有输出中的名字是否在人物库存在）
  4. 方言用量检查：遵从 `书配置.md` 中的方言限制。主角/叙述视角角色不应使用方言。方言只能用于配角自然腔调的点缀。
  5. opus 反模式扫描（见 `references/case-studies/opus-anti-patterns.md`）：命中即发回重写
  6. Markdown残留检查：搜索 `---`（分割线）、`**`（加粗）、`` ` ``（代码块）、`> `（引用）→ 命中即patch删除。番茄平台不支持Markdown渲染。

### opus 反模式扫描
- 搜索 opus 常见反模式标记词（动态上浮、循环状态、回报周期、预估等）→ 命中即发回重写
- **重写时额外幻觉**：opus 在重写（非初稿）时数字幻觉远超初稿——面积夸大、系统指标自创、人名地名自创。详见 `references/case-studies/opus-hallucination-patterns.md`
- 防御：重写 prompt 必须注入铁律查表 + 输出后立即 `review_scan.py` 扫描
- **真实地名黑名单**：`review_scan.py` 从 `书配置.md` 读取该书对标区域的黑名单地名列表。opus 在架空地名描述中极易自创真实地名——防御：prompt 注入时明确禁止真实地名 + DRAFT 后扫描器拦截。
- **角色关系反转幻觉**：opus 在重写章末段落时可能将敌对角色改写为盟友。防御：DRAFT 后逐段检查对话双方身份关系，若出现敌对角色对主角使用亲密称呼，发回重写。

### POLISH 路由规则
- 🔴 一级问题：Claude Code CLI 修复（`claude -p "修复prompt" --model opus`）
- 🟡 建议级别（≤3项）：主 Agent 直接 patch 微调，不派 opus。省 token 且更快。
- 🟡 建议但是 >3项 或涉及大段重写：仍走 Claude Code CLI

### 章节重写流程

当审查报告或读者反馈指出已有章节需重写时：

1. **备份**：`python3 ~/.hermes/skills/novel/scripts/backup_chapter.py 第X章.md`
2. **锁定改动范围**：确认哪些章需动，哪些章已发布（锁），哪些自由。评估关联影响
3. **准备 prompt**：写到 `/tmp/novel_chX_rewrite.txt`，文件传参避免 shell 转义。prompt 首行必须是「直接输出第X章正文。不要先设计方案。不要问问题。直接写。」+ 注入 opus铁律完整查表
4. **派发 Claude Code CLI**：独立章节可并行派发（background + notify_on_complete）
5. **验证**：`review_scan.py` → 核对数字/地名/人名 → 修复 opus 幻觉 → 存盘
6. **对齐关联章**：受影响的下游章节做一致性对齐
7. **全量校验**：`consistency_check.py --book <书名>` 确保 7/7

**重写时的 opus 幻觉警告**：重写比初稿更容易触发数字幻觉——opus 会自创面积、系统指标、人名。每次输出的数字/地名/人名必须人工核对。

### 输出规范
- 用户要第X章 → 只发正文，不夹带统计/总结/分析
- 字数目标：2000-3000，目标 2500。±300 可接受。

## 铁律

### 修改必备份
> **任何对 `01-正文存稿/第X章.md` 的修改操作，必须先执行：**
> ```bash
> python3 ~/.hermes/skills/novel/scripts/backup_chapter.py ~/novels/books/<书名>/01-正文存稿/第X章.md
> ```
> 备份到 `03-版本备份/正文历史/第X章_YYYYMMDD_HHMMSS.md`。没有备份就没有修改历史。

### delegate_task 禁用规则
- **文字创作任务（DRAFT/POLISH/爽点注入）禁止使用 delegate_task。**
- 子代理会自创地名、自创数字、自创系统功能、自创面板格式。
- 唯一例外：REVIEW 步骤的数据扫描脚本可以用 delegate_task 派发（非创作类任务）。

### 代理协作安全规则
> ⚠️ 子代理极易擅自改名或改身份。详见 `references/case-studies/delegate-pitfalls.md`。
> - 派发前必须在 context 中写：「所有角色名和身份以人物库人物卡为准，禁止自行改名或改身份」
> - 子代理返回后 grep 校验所有输出文件中的角色名是否在人物库中存在

### 骨架不全绝不开始写作
`novel-new-book` 阶段 3.5 强制执行 4 项骨架检查：主角人物卡、核心配角人物卡（≥3张）、主线大纲、第一卷细纲。任何一项未通过则不允许进入「写第 1 章」。确保项目有一个雏形骨架作为创作基准，后续边写边细化。

### 脚本与技能分离
`novel-cron` 的所有 Python 脚本已从 Markdown 内嵌代码中提取到 `~/.hermes/skills/novel/scripts/` 独立 .py 文件。修复 bug 应改 .py 文件，不改 novel-cron.md。该文件中的内嵌代码仅供文档参考。

### 审查流程
三步审查链：自动扫描(zero-tolerance) → 爽点注入(5项全过) → 读者审查(每3章，想弃则重写)。

### 深度审查后修复流程

> ⚠️ **铁律：不是你修复，是派发任务修复。** 主 Agent 的角色是审查 + 派发 + 验证，不是亲自动手修。

**分工规则**：

| 任务类型 | 派发方式 | 说明 |
|---------|---------|------|
| 文档更新（伏笔表/系统状态/人物总表/大纲） | `delegate_task` | 结构化数据更新，非创作类 |
| 文字创作（补字数/写新章/重写/爽点注入） | **Claude Code CLI (opus)** | 绝对不走 delegate_task |
| 扫描验证 | `terminal()` 直接执行 | 不等子代理 |

**执行纪律**：
1. **逐一修复，不批量**。每项独立派发，等结果回来验证通过后再派下一项。
2. **独立文档任务可并行**（如伏笔表 + 系统状态 + 人物总表三项目录独立）。
3. **每项派发包含明确的 success criteria**（字数目标、字段修改清单、验证命令）。
4. **子代理返回后必须验证**：字数达标？违禁地名=0？系统面板完整？consistency_check 通过？
5. **创作类派发遵循骨架模式**：先备份 → 准备 prompt 文件（避免 shell 中文引号炸）→ `claude --model opus --max-turns 15` → `review_scan.py` 验证 → 存盘。

**标准修复 pipeline**：
```
审查报告 → 任务图 → fix1(伏笔表·doc)    → delegate_task ─┐
                    fix2(系统状态·doc)  → delegate_task ─┤ 并行
                    fix3(人物总表·doc)  → delegate_task ─┘
                                                        ↓ 全部验证
                    fix4(ChN补字·创作)  → ClaudeCodeCLI ─┐ 逐章
                    fix5(ChM补字·创作)  → ClaudeCodeCLI ─┘
                                                        ↓ 全量验证
                                                      完成
```

## 质量保障铁律
- 去AI味：draft 生成时避让 → review 检测 → polish 兜底 → cron 巡检
- 违禁词：三层防线（draft预防 → review拦截 → cron扫描）
- 人物一致性：draft 阶段参照人物库创作 → review 阶段逐角色对照人物库检测未注册角色 → 阻塞未注册核心角色
- 变更流程：排查 → Claude Code CLI 修改 → 审查验收
- 多轮审查：双审并行 → 合并问题 → 一把修 → 再审，直到零阻断
