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
| `references/case-studies/读者审查标准.md` | 20年网文读者身份审查：四维框架+7个必答问题、审查时机、执行命令、逻辑检查、结果处理 |
- `references/general/writing-rhythm.md` — 写作节奏分析（含系统退化检测 + 剧情推进速度检测 + 卷长参考 + 格局升级路径）
- `references/general/system-golden-finger-design.md` — 系统金手指设计方法论（删系统测试 + 三层情报等级 + 退化诊断清单 + 渐进进化原则 + 新书系统设计模板）
- `references/general/author-voice-dna.md` — 作者声音DNA定义（句式节奏+标志性用词+比喻意象域+AI味诊断清单+新书模板）
- `references/general/webnovel-style-calibration.md` — 网文风格校准：文学感网文 vs 大白话网文诊断表+10条校准规则+DRAFT注入+REVIEW检查6项
- `references/general/references-version-alignment.md` — references版本对齐方法论：触发条件+执行步骤+坑（不要只看文件名就删、子技能不是死代码）
- `references/general/claude-code-model-routing.md` — Claude Code 模型路由：pandai 中继各通道长 prompt 性能实测、排查方法论、DRAFT/POLISH 失败回退规则
| `references/general/workflow-lock.md` | 流程锁：novel_step.sh 防跳步机制 |
| `references/case-studies/review-methodology.md` | 审查方法论+8步全量一致性审查清单+工具陷阱（每卷完成/设定变更后触发） |
| `references/case-studies/ai-generation-pitfalls.md` | AI生成反模式与幻觉防御：面板游戏化/数字篡改/人物剧情幻觉/地名幻觉/系统功能发明/Claude Code陷阱/子代理陷阱 |
| `references/case-studies/skill-optimization-via-tdd.md` | TDD 应用于技能文件修改：RED-GREEN-REFACTOR 循环、拆分策略避免 Claude Code 超时、独立验证替代交叉审查 |
- `references/case-studies/plot-quality-source.md` | PLOT 是质量源头：状态更新注入戏剧的三问法、3种技法、第33章改造实例 |
| `references/case-studies/mid-story-stagnation-ch43.md` | 中后期节奏崩塌三重诊断：系统退化为计算器+推进速度失控+单章审查跨章盲区。Ch43复盘实例 |

### 完整 references 索引（2026-08-01 重构后）

**通用方法论（`references/general/`）**——按需参考，核心流程已内联到各技能：
- `batch-text-normalization.md` — 批量文本规范化（全角/标点/去重）
- `cross-file-update-checklist.md` — 跨文件同步更新检查清单
- `multi-file-skill-debugging.md` — 多文件技能调试方法
- `script-health-check.md` — 脚本健康检查（引用路径完整性验证）
- `skill-iteration-workflow.md` — 技能迭代工作流
- `skill-maintenance.md` — ⭐ 技能库维护方法论：解耦5步法+架构审查诊断+安全重构协议（git tag备份→调查→分任务commit→回测→独立审查→修复→最终tag）+ 瘦身手法 + 审查必查项 + 开源发布流程
- `writing-rhythm.md` — 写作节奏分析
- `workflow-lock.md` — 流程锁：novel_step.sh 防跳步机制
- `progress-format.md` — 进度 JSON 格式与中断恢复（novel-main 引用）

**特定书复盘（`references/case-studies/`）**——方法论可参考，具体数据（章号/人物/地名/数字）来自特定书籍，不具有普适性：
- `ai-generation-pitfalls.md` — AI幻觉与防御合集（面板游戏化/数字篡改/人物剧情幻觉/地名幻觉/Claude Code陷阱/子代理陷阱）
- `review-methodology.md` — 审查方法论合集（深度审查5步+8步全量清单+工具陷阱）
- `读者审查标准.md` — 读者审查完整方法论（四维框架+7问+逻辑检查+长区间复盘+分批策略）
- `爽点注入方法论.md` — 爽点注入+追回技法（5项检查+8章回修实录+6种微型注入技法+注入SOP）
- `系统面板设计规律.md` — 系统面板设计+数字验证（六大幻觉+维度表+颜色语言+结算公式对照）
- `worldbuilding-lessons.md` — 世界观建设教训（三层城市体系+地名变更记录+审查流程+opus防御）
- `character-arc-case-study.md` — 编辑模式案例
- `bulk-review-workflow.md` — 10-30章级全量批量审查
- `fanqie-publishing.md` / `de-book-specificization.md` — 发布/去书特定化
- 所有 case-studies 文件均带「⚠️ 特定书籍复盘文档」标注，数据不通用

### 分卷细纲同步铁律

> **卷号铁律**：分卷结构由该书大纲定义。禁止在任何地方（骨架/章节规划/分卷细纲/口头）混淆卷号与章节号。卷末章号以大纲为准。

> ⚠️ 教训（通用）：分卷细纲与正文不同步、角色身份在细纲中与正文不一致——大纲漂移会导致 DRAFT prompt 注入错误上下文。

- **每次世界观变更后，必须对照正文重写对应卷的分卷细纲**——以正文和人物卡为权威源。
- **每完成 10 章或一卷结束后，触发全量一致性审查**（`references/case-studies/review-methodology.md`），含漂移检测。
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
| 全量审查 | `references/case-studies/review-methodology.md` | 每卷完成/世界观变更后：8关键字搜索+人物卡/大纲对齐 |
| 批量审查 | `references/case-studies/bulk-review-workflow.md` | 10-30章级全量批量审查：自动扫描+字数统计+爽点检查+合规检查 |
| 爽点追回 | `references/case-studies/爽点注入方法论.md` | 深度审查后章间飙爽点：6技法+注入SOP |
| 系统面板合规 | `书配置.md` 中定义的面板规范 | DRAFT后自动扫描 + 人工核对 |

## 8步创作循环（骨架模式·v4.0）

```
1. novel-prep    → 上下文摘要
2. novel-plot    → 剧情推演
3. novel-draft   → 正文初稿（2200—2400字，目标2250，骨架模式）
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
| `references/general/skill-maintenance.md` | 技能库维护方法论：解耦5步法+架构审查诊断+安全重构协议+瘦身手法+开源发布流程 |

## 作者档案
- 风格：直接、不煽情、冷幽默、冷感叙述
- 目标平台：番茄小说
- 关键要求：去AI味、网感、故意错别字仅限对话

> ⚠️ **「直接、不煽情」只是温度，不是DNA。** 作者声音需要更具体的定义——句式节奏、标志性用词、比喻意象域、叙事视角距离、对话标记习惯。没有这些锚点，Claude Code 默认用AI通用文学腔。详见 `references/general/author-voice-dna.md`。新书创建时必须在书配置.md中填写「作者声音DNA」区块；已有书可通过正文逆向分析提取DNA。
>
> ⚠️ **网文不是文学。** AI默认产出"文学感网文"——冷、隐晦、克制、留白多。番茄读者要的是"大白话网文"——直接、爽快、情绪到位。详见 `references/general/webnovel-style-calibration.md`（10条校准规则+DRAFT注入+REVIEW检查6项）。DRAFT prompt必须追加网文校准片段，REVIEW必须追加网文校准6项检查。不校准=写着写着变成严肃文学=读者流失。
>
> ⚠️ **技能沉淀优先于当前书的修复。** 用户反馈「这本书崩了就崩了，但技能要沉淀下来」。当发现系统性问题时，先把教训固化到技能（让下一本书不再犯），再考虑当前书的修补。不要只修当前章不改技能——同类错误会在下一本书重复。

## 写作质量铁律

### 章节推进铁律
- **用户未明确说「继续」「写第X章」时，严禁擅自推进到下一章。**
- **用户发起世界观讨论时，停下手上所有修改，先对表。** 不要在设定未对齐时急于修章节——修完又改更费时间。对齐后再一把改完。

### PLOT 是质量的源头（不是 DRAFT）

> 核心教训（2026-08-01）：护栏优化（字数门禁、死水段扫描、禁止环境凑字）拦的是垃圾，但写不出好故事。用户说的原话：「AI就是为来写而写，浪费token」。质量从 PLOT 阶段就决定了——如果骨架只有状态更新没有冲突，DRAFT 再怎么写都是注水。

**章节规划表里写的往往是「状态变化」不是「故事」**：
- 「首次盈利」「签了大单」「修缮完工」「人才入职」——这些没有张力
- 好故事的公式：**好消息 + 但是 = 戏剧**
- 判定方法（三问）：
  1. 有人不高兴吗？——所有人都满意=没有冲突
  2. 主角做了什么艰难的决定？——没有选择=没有戏剧
  3. 下一章的麻烦在这一章种下了吗？——没有钩子=没有追读

**给状态更新注入戏剧的3种方法**：
1. 好消息里藏炸弹：盈利了但利润结构不可持续；签了大单但产能跟不上
2. 让受益者和受害者同时在场：老板赚钱渔民没涨；新人来了挤了老人
3. 用第三方的嘴戳破表面：新人/对手/老人说出大家不敢说的真话——最有效的冲突触发器

**容量预审不只是数回合数**，还要检查每个回合是不是「有效冲突」而非「状态罗列」。4个回合如果是「搬货→算账→打电话→等消息」，那就是4个注水段不是4个有效回合。

### PLOT 跨章门控（2026-08-07 新增，详见 novel-main SKILL.md 步骤2）

> 核心教训：技能有节奏/系统/推进的知识，但只在 MILESTONE（每5章）执行——检测太晚。用户反馈「感觉很无聊」「系统没起作用」时已经写了十几章。PLOT 门控把检测前移到每章。

PLOT 阶段强制执行三道门控（互为并行）：
1. **跨章节奏门控**：最近4章情绪曲线分析，连续≥3章无打脸/无胜利/同情绪/主角被动→本章强制变化
2. **系统退化检测**：连续≥3章面板后MC「收掉」/≥5章无新维度/删系统测试→本章系统必须做不可替代的事
3. **剧情推进速度检测**：同一对手≥30章/无格局升级≥20章/建设章连续≥3章→本章必须格局升级

详见 `novel-main/SKILL.md` 步骤2 + `references/general/writing-rhythm.md` + `references/general/system-golden-finger-design.md`。

### DRAFT 路由规则（骨架模式）

> ⚠️ **骨架模式已取代旧自由模式。** 旧模式（大段铁律注入 + opus自由发挥）每章产生 3-5 处幻觉（数字/地名/人名/面板格式）。骨架模式降至 0-1 处，且错误来源从 opus 转移为骨架作者（可控）。

**骨架模式流程**：
1. **PREP 后生成骨架**：根据章节规划 + 人物状态 + 伏笔表写骨架（含场景顺序 / 核心事件 / 系统面板 / 章末钩子）
2. **骨架自查**：grep 扫描骨架中的地名（只用白名单）/ 数字（校对结算查表）/ 人物（校对人物库）/ 系统面板（格式从 `书配置.md` 读取）。发现非法地名即修。
3. **组装短 prompt**：骨架 + 3 条铁律（地名 / 面板 / 字数），总 1.2KB 以内。不再注入大段铁律全文。
4. **派发 Claude Code**：
   ```bash
   python3 ~/.hermes/skills/novel/scripts/claude_runner.py \
     --prompt-file /tmp/novel_chX_prompt.txt \
     --model sonnet \
     --max-turns 15 \
     --allowed-tools Read,Write,Edit \
     --idle-timeout 120 \
     --exit-timeout 10 \
     --target-file ~/novels/books/<书名>/01-正文存稿/第N章.md \
     --events-file /tmp/novel_chX_events.jsonl \
     --output-file /tmp/novel_chX_result.json
   ```
5. **验证**：`review_scan.py` → 校对骨架是否忠实地执行（场景 / 面板 / 数字 / 章末）

> ⚠️ **模型与运行状态判定**：小说 DRAFT/POLISH 默认用 `--model sonnet`（当前中继映射必须在派发前读实时配置确认）。
>
> **idle_timeout 是连续无 stdout 事件时长**，不是进程总运行时限。产物已落盘（target_file 已修改）不算停滞，不会提前杀进程。只有 `status=stalled` 时才允许**一次**干净重试；连续两次 `stalled` 上报后由主 Agent 接管，不再重试。
>
> **字数统计、违禁词扫描、系统面板验收**由主 Agent 在 Claude Code 进程结束后用确定性脚本执行，不在 DRAFT/POLISH prompt 中要求 Claude 自行调用 Bash——这避免了权限拒绝、无效轮次和超时误判。详见 `references/general/claude-code-model-routing.md`。

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
3. 字数 2200—2400（目标 2250）。对话 ≥40%。方言用量遵从 `书配置.md` 限制（如适用）。**所有对话用「」，禁止双引号""**。冷感叙述。章末无结束标记。**禁止任何Markdown语法**：无`---`分割线、无`**加粗**`、无`` `代码块` ``、无`> 引用`、无`[]链接`。场景之间直接空行衔接，不用分隔线。番茄小说平台不支持Markdown渲染。

### 骨架作者自查清单（派发前必须执行）：
- [ ] grep 扫描骨架确认无真实地名
- [ ] **结算数字与公式匹配**：按 `书配置.md` 中定义的结算公式验证面板数字。数字不对→骨架有误→修正后重新派发。Claude Code输出后再次验证。
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
- **AI味扫描（附加）**：在爽点5项之后执行——①连续5句字数差<5字→打破节奏 ②比喻换到别的书也能用→替换为DNA意象 ③搜索AI禁用词（仿佛/宛如/不禁/竟然/不由得/一股/涌上）→命中即改 ④MC标志性用词本章是否出现→需补。详见 `references/general/author-voice-dna.md`。
- **网文校准检查（附加，与AI味扫描并行）**：详见 `references/general/webnovel-style-calibration.md` → REVIEW阶段附加检查（6项）：
  - [ ] 情绪留白：有没有"脸色变了但读者不知道什么感受"的段落？→ 补围观反应
  - [ ] 打脸完整度：质疑→展示→反应→围观→结果五步是否齐全？→ 缺哪步补哪步
  - [ ] 事件密度：实际推进了几个事件？只有1个→⚠️
  - [ ] 钩子强度：章末让读者"想知道下一章"吗？环境描写收尾→重写钩子
  - [ ] 叙述大白话：随机抽3段，有没有看不懂的文学比喻？→ 改大白话
  - [ ] 对手反应：对手有没有足够反应？消失太久=爽感断裂
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
  5. opus 反模式扫描（见 `references/case-studies/ai-generation-pitfalls.md`）：命中即发回重写
  6. Markdown残留检查：搜索 `---`（分割线）、`**`（加粗）、`` ` ``（代码块）、`> `（引用）→ 命中即patch删除。番茄平台不支持Markdown渲染。

### 模型反模式扫描
- 搜索模型常见反模式标记词（动态上浮、循环状态、回报周期、预估等）→ 命中即发回重写
- **重写时额外幻觉**：模型在重写（非初稿）时数字幻觉远超初稿——面积夸大、系统指标自创、人名地名自创。详见 `references/case-studies/ai-generation-pitfalls.md`
- 防御：重写 prompt 必须注入铁律查表 + 输出后立即 `review_scan.py` 扫描
- **真实地名黑名单**：`review_scan.py` 从 `书配置.md` 读取该书对标区域的黑名单地名列表。模型在架空地名描述中极易自创真实地名——防御：prompt 注入时明确禁止真实地名 + DRAFT 后扫描器拦截。
- **角色关系反转幻觉**：模型在重写章末段落时可能将敌对角色改写为盟友。防御：DRAFT 后逐段检查对话双方身份关系，若出现敌对角色对主角使用亲密称呼，发回重写。

### sonnet/deepseek-v4-pro DRAFT 字数偏差陷阱（2026-08 实测）

**两种方向都会发生**：

#### A. 字数不足（常见）
deepseek-v4-pro（sonnet 通道）处理 3000-4000 字骨架 prompt 时，输出正文稳定在 1550-2100 字，比 2200 下限低 100-650 字。连续 4 章（Ch34-37）全部触发。

根因：模型倾向精简骨架叙述指导，保留对话但压缩环境描写和过渡段。

**应对（已验证有效）**：
1. DRAFT 返回后立即跑 `review_scan.py` 查字数
2. 不足时主 Agent 直接 `patch` 补有效剧情（不是环境凑字数）：面试/谈判补候选人细节、冲突补反应和群像、技术补操作步骤
3. 每次补 30-50 字的 patch，2-4 次达标。不要一次性大段补
4. 补完重新扫描确认 >= 2200
5. **不要重试 Claude Code 试图让它一次写够**——重试不解决问题，浪费 token 和时间。直接 patch 补字

#### B. 字数超标 + POLISH 过度压缩（Ch43 实测）
DRAFT 返回 3278 字（超上限 37%），POLISH 派发压缩指令后返回 1841 字（低于下限 16%），需要主 Agent 手动 patch 补 400 字才达标。

根因：POLISH prompt 说「压缩到2200-2400」时，模型一刀切删到 1800-1900，不分有效/无效内容。

**应对（已验证有效）**：
1. POLISH prompt **不要只说「压缩到 X 字」**——明确说「目标2250字，当前3278字，需精简约1000字。保留所有对话回合和情节节点，只删重复描写和冗余过渡」
2. 给出保留优先级清单（先删什么、必须保留什么），让模型有判断依据
3. POLISH 返回后立即跑 `review_scan.py` 查字数
4. 如果 POLISH 压过头（< 2200）：主 Agent 直接 `patch` 补有效剧情内容（配角反应、对话回合、动作细节），每次 30-80 字，2-4 次达标
5. **不要重试 POLISH**——重试只会得到不同的随机压缩结果，不解决问题。直接 patch 补字

> 通用教训：**DRAFT 和 POLISH 的字数控制都不可靠**。无论哪个方向偏差，主 Agent 在 `review_scan.py` 出字数后直接 `patch` 修正，比重试 Claude Code 更快更可控。

### POLISH 路由规则
- 🔴 一级问题：Claude Code CLI 修复（通过 `claude_runner.py` 派发：`python3 ~/.hermes/skills/novel/scripts/claude_runner.py --prompt-file /tmp/fix_prompt.txt --model sonnet --allowed-tools Read,Write,Edit --idle-timeout 120 --exit-timeout 10 --target-file ... --output-file ...`）
- 🟡 建议级别（≤3项）：主 Agent 直接 patch 微调，不派 Claude Code。省 token 且更快。
- 🟡 建议但是 >3项 或涉及大段重写：仍走 Claude Code CLI（通过 `claude_runner.py`）

### 章节重写流程

当审查报告或读者反馈指出已有章节需重写时：

1. **备份**：`python3 ~/.hermes/skills/novel/scripts/backup_chapter.py 第X章.md`
2. **锁定改动范围**：确认哪些章需动，哪些章已发布（锁），哪些自由。评估关联影响
3. **准备 prompt**：写到 `/tmp/novel_chX_rewrite.txt`，文件传参避免 shell 转义。prompt 首行必须是「直接输出第X章正文。不要先设计方案。不要问问题。直接写。」+ 注入 opus铁律完整查表
4. **派发 Claude Code CLI**（通过 `claude_runner.py`，含 idle-timeout 保护和事件流）：
   ```bash
   python3 ~/.hermes/skills/novel/scripts/claude_runner.py \
     --prompt-file /tmp/novel_chX_rewrite.txt \
     --model sonnet \
     --max-turns 15 \
     --allowed-tools Read,Write,Edit \
     --idle-timeout 120 \
     --exit-timeout 10 \
     --target-file ~/novels/books/<书名>/01-正文存稿/第N章.md \
     --events-file /tmp/novel_chX_rewrite_events.jsonl \
     --output-file /tmp/novel_chX_rewrite_result.json
   ```
   独立章节可并行派发（background + notify_on_complete）。
5. **验证**：`review_scan.py` → 核对数字/地名/人名 → 修复模型幻觉 → 存盘
6. **对齐关联章**：受影响的下游章节做一致性对齐
7. **全量校验**：`consistency_check.py --book <书名>` 确保 7/7

**重写时的模型幻觉警告**：重写比初稿更容易触发数字幻觉——模型会自创面积、系统指标、人名。每次输出的数字/地名/人名必须人工核对。

### 输出规范
- 用户要第X章 → 只发正文，不夹带统计/总结/分析
- 字数目标：2200—2400，目标 2250。±50 可接受。

### 参数滚排完整性（修改全局标准时必读）

> 核心教训（2026-08-02）：改了规则行但没改示例文字、prompt 模板、章节结构字数分配、审查清单——读技能的人看到的是自相矛盾的内容。

改全局参数（如字数口径、质量标准）时，必须同步以下所有位置，不能只改规则声明行：

| 位置 | 检查内容 | 典型遗漏 |
|------|---------|---------|
| 章节结构模板 | 开场/推进/高潮/钩子的字数加总是否等于新目标 | 只改了标题没改段内分配 |
| prompt 铁律行 | 派发给 Claude Code 的字数指令 | 骨架模板改了但 main 的铁律没改 |
| 审查清单 | 自检项中的旧数字 | 清单仍写"2000-3000" |
| 技能描述行 | frontmatter description 中的旧数字 | 描述仍写"约2500字" |
| README | 目录结构、技能列表、8步循环描述 | README 仍引用旧扁平 .md 格式 |
| 旧机械规则的自检项 | "每200字微钩子"等旧配额的自检行 | 加了禁止声明但旧自检行没删 |

**验证方法**：改完后用 `grep -r '旧数字' skills/` 全局搜索残留，不要只看改过的文件。

### GitHub 发布卫生

推送到 GitHub 前必须执行：

1. 脱敏扫描：检查所有暂存文件中的 token/密钥/手机号/邮箱/IP/凭据
2. 排除非本次变更：用户原有未提交改动（`novel-editing-patterns` 等）不纳入提交
3. 移除一次性文件：`PLAN-*.md`、临时计划、调试日志——加 `.gitignore` 规则防止再混入
4. 更新文档：README 目录结构/技能列表/版本时间/脚本描述与实际代码一致
5. 版本号：README 创建时间更新到本次变更日期，注明改了什么

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
> ⚠️ 子代理极易擅自改名或改身份。详见 `references/case-studies/ai-generation-pitfalls.md`。
> - 派发前必须在 context 中写：「所有角色名和身份以人物库人物卡为准，禁止自行改名或改身份」
> - 子代理返回后 grep 校验所有输出文件中的角色名是否在人物库中存在

### 骨架不全绝不开始写作
`novel-new-book` 阶段 3.5 强制执行 4 项骨架检查：主角人物卡、核心配角人物卡（≥3张）、主线大纲、第一卷细纲。任何一项未通过则不允许进入「写第 1 章」。确保项目有一个雏形骨架作为创作基准，后续边写边细化。

### 脚本与技能分离
`novel-cron` 的所有 Python 脚本已从 Markdown 内嵌代码中提取到 `~/.hermes/skills/novel/scripts/` 独立 .py 文件。修复 bug 应改 .py 文件，不改 novel-cron/SKILL.md。该文件中的内嵌代码仅供文档参考。

### 审查流程
三步审查链：自动扫描(zero-tolerance) → 爽点注入(5项全过) → 读者审查(每3章，想弃则重写)。

### 深度审查后修复流程

> ⚠️ **铁律：不是你修复，是派发任务修复。** 主 Agent 的角色是审查 + 派发 + 验证，不是亲自动手修。

**分工规则**：

| 任务类型 | 派发方式 | 说明 |
|---------|---------|------|
| 文档更新（伏笔表/系统状态/人物总表/大纲） | `delegate_task` | 结构化数据更新，非创作类 |
| 文字创作（补字数/写新章/重写/爽点注入） | **Claude Code CLI (sonnet)** | 绝对不走 delegate_task |
| 扫描验证 | `terminal()` 直接执行 | 不等子代理 |

**执行纪律**：
1. **逐一修复，不批量**。每项独立派发，等结果回来验证通过后再派下一项。
2. **独立文档任务可并行**（如伏笔表 + 系统状态 + 人物总表三项目录独立）。
3. **每项派发包含明确的 success criteria**（字数目标、字段修改清单、验证命令）。
4. **子代理返回后必须验证**：字数达标？违禁地名=0？系统面板完整？consistency_check 通过？
5. **创作类派发遵循骨架模式**：先备份 → 准备 prompt 文件（避免 shell 中文引号炸）→ `claude --model sonnet --max-turns 15` → `review_scan.py` 验证 → 存盘。

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
