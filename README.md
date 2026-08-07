# 番茄小说 AI 创作系统

> 基于 Hermes Agent 技能体系的网文创作全流程框架。
> 设计为**通用框架**——不绑定任何特定书籍的设定，每本书独立管理自己的世界观/人物/地名/系统面板。

## 开源信息

- **GitHub 仓库**：https://github.com/cwjdong-design/novel
- **License**：MIT（详见 [LICENSE](LICENSE)）
- **安装方式**：clone 仓库后放入 `~/.hermes/skills/` 即可使用（依赖：Hermes Agent + Claude Code CLI）

## 核心理念

**AI 擅长写散文，不擅长造结构。**

所以这套系统的设计是：
- **人类（或主 Agent）写骨架**：结构、数字、地名、系统面板全部预验证
- **AI（Claude Code opus）填肉**：只写散文，不改骨架里的任何东西

这套"骨架模式"将 LLM 幻觉（数字/地名/面板格式）从每章 3-5 处降至 0-1 处。

## 路径约定

| 用途 | 路径 | 说明 |
|------|------|------|
| **技能文件** | `~/.hermes/skills/novel/` | 通用方法论+流程规范，跨书复用 |
| **模板文件** | `~/.hermes/skills/novel/templates/` | 人物卡/世界观/章节模板 |
| **知识库** | `~/.hermes/skills/novel/knowledge/` | 番茄风格指南、违禁词库等通用知识 |
| **状态文件** | `~/.hermes/skills/novel/_state/` | 进度 JSON、当前活跃书 |
| **书籍数据** | `~/novels/books/<书名>/` | 每本书的正文、设定、大纲、备份 |
| **全局日志** | `~/novels/_shared/logs/` | 巡检日志、违禁词扫描报告 |
| **全局备份** | `~/novels/_shared/backups/` | cron 每日全量备份 |
| **工具脚本** | `~/.hermes/skills/novel/scripts/` | Python/Shell 工具脚本（实体） |

## 目录结构

```
~/.hermes/skills/novel/               # 技能目录（通用）
├── README.md                          # 本文件
├── novel-main/SKILL.md                # 主技能：8步状态机调度
├── novel-prep/SKILL.md                # 子技能1：资料整理
├── novel-plot/SKILL.md                # 子技能2：剧情推演（含容量门禁）
├── novel-draft/SKILL.md               # 子技能3：正文生成
├── novel-review/SKILL.md              # 子技能4：合规审查（含有效内容双门槛）
├── novel-polish/SKILL.md              # 子技能5：打磨
├── novel-track/SKILL.md               # 子技能6：状态追踪
├── novel-backup/SKILL.md              # 子技能7：版本备份
├── novel-cron/SKILL.md                # 自动化：每日巡检
├── novel-new-book/SKILL.md            # 新书初始化
├── novel-skeleton/SKILL.md            # 骨架生成（含容量预审）
├── novel-character/SKILL.md           # 人物塑造方法论
├── novel-platform/SKILL.md            # 番茄平台运营
├── novel-editing-patterns/SKILL.md    # 编辑模式
├── novel-lessons-20260725/SKILL.md    # 经验教训
├── novel-writing/SKILL.md             # 体系总入口
├── novel-publishing/SKILL.md          # 半自动发布
├── templates/                         # 设定模板
├── knowledge/                         # 通用知识库
├── scripts/                           # 核心工具脚本
├── tests/                             # 契约测试（36项）
└── _state/                            # 运行时状态（gitignored）

~/novels/books/<书名>/                  # 每本书独立数据
├── 00-大纲细纲/
│   ├── 主线大纲.md
│   ├── 章节规划.md
│   └── 分卷细纲/
├── 01-正文存稿/
├── 02-设定文档/
│   ├── 书配置.md                      # ⭐ 该书的扫描规则/地名白名单/面板/方言
│   ├── 世界观.md
│   ├── 人物库/
│   ├── 伏笔追踪表.md
│   └── 故事线状态.md
├── 03-版本备份/
└── 04-错误库/
```

### 书配置.md（每本书的核心配置）

每本书在 `02-设定文档/书配置.md` 中定义自己的规则，供技能和脚本读取：

```markdown
# 《书名》配置

## 地名白名单
允许：<架空地名列表>
禁止：任何真实中国地名

## 系统面板规范（系统流适用）
- 格式：【字段：数值】
- 固定字段：<字段1>、<字段2>、<字段3>
- 结算公式：<基数> × <系数> × <比例>

## 方言设置
- 方言类型：粤语/四川话/东北话/无
- 词表：<允许使用的方言词列表>
- 使用规则：每章≤5处，仅限对话内，仅限特定角色

## 作者风格
- 情感风格：直接/含蓄
- 叙述温度：冷/热
- 幽默偏好：冷幽默/无

## 扫描规则（供 review_scan.py 使用）
- 真实地名黑名单：<需要拦截的真实地名>
- 系统违禁术语：<禁止出现的面板措辞>
```

## 技能体系

| 技能 | 类型 | 触发 | 输入 | 输出 |
|------|------|------|------|------|
| novel-writing | 入口 | "写小说" | — | 路由+铁律+体系 |
| novel-main | 主调度 | "写第X章" | 书名+章节号 | 完成报告 |
| novel-prep | 子技能 | 由 main 调用 | 书名+章节号 | 上下文摘要 |
| novel-plot | 子技能 | 由 main 调用 | 大纲+上下文 | 事件+冲突+转折 |
| novel-skeleton | 子技能 | 由 main 调用 | PREP输出 | 预验证骨架 |
| novel-draft | 子技能 | 由 main 调用 | 骨架+人物卡 | 2200—2400字初稿 |
| novel-review | 子技能 | 由 main 调用 | 初稿+设定 | 审查报告 |
| novel-polish | 子技能 | 由 main 调用 | 初稿+审查 | 定稿 |
| novel-track | 子技能 | 由 main 调用 | 定稿 | 更新设定 |
| novel-backup | 子技能 | 由 main 调用 | 定稿 | 备份确认 |
| novel-cron | 自动化 | 每日定时 | — | 巡检报告 |
| novel-new-book | 初始化 | "新开一本书" | 书名 | 目录+模板 |
| novel-character | 方法论 | 按需加载 | — | 人物塑造方法 |
| novel-platform | 运营 | 按需加载 | — | 平台策略 |
| novel-editing-patterns | 方法论 | 按需加载 | — | 编辑修复模式 |
| novel-publishing | 工具 | "发布" | 章节文件 | 平台草稿/发布 |

## 8步创作循环（骨架模式）

```
1. PREP     → 上下文摘要（前文+人物+伏笔）
2. PLOT     → 本章剧情推演（事件+冲突+钩子）
3. DRAFT    → 骨架生成(预审) → Claude Code opus 填肉 → 2200—2400字初稿
4. REVIEW   → 审查报告（自动扫描+字数门禁+有效内容双门槛+爽点检查）
5. POLISH   → 打磨定稿（对话/画面感/节奏/钩子强化）
6. TRACK    → 更新设定（人物状态/伏笔表/章节梗概）
7. MILESTONE → 里程碑审查（每5章触发）
8. BACKUP   → 版本备份（正文+设定快照）
```

REVIEW↔POLISH 最多循环3次。MILESTONE 仅在 5/10/15...章触发。

## 快速开始

1. **安装到 Hermes**：将本目录放到 `~/.hermes/skills/novel/`
2. **初始化新书**：说「新开一本书」，引导式创建目录和模板
3. **填写骨架**：补全大纲、人物卡、世界观
4. **开始写作**：说「写第1章」启动8步流程

## 多书管理

- 每本书独立目录 `books/<书名>/`
- 技能文件跨书复用
- 书配置独立（地名/面板/方言/风格）
- `novel-cron` 全局巡检所有书

## 创建时间

2026-07-21 | 最近更新：2026-08-07（references版本对齐：36→21文件，9组合并消除旧版本 + PLOT三道门控 + 网文风格校准 + 系统金手指设计方法论 + MILESTONE卷末触发 + 番茄风格指南追加网文vs文学感对比）

## 脚本工具

### 核心脚本（`~/.hermes/skills/novel/scripts/`）

| 脚本 | 用途 | 从书配置读取 |
|------|------|:----------:|
| `review_scan.py` | DRAFT后零容忍扫描（字数门禁/地名/系统词/AI词/死水段/重复意象/格式） | ✅ |
| `consistency_check.py` | 7维跨文档一致性校验 | ✅ |
| `backup_chapter.py` | 修改前自动备份 | — |
| `novel_scan.py` | 违禁词全面扫描（从违禁词库.json） | — |
| `foreshadow_check.py` | 伏笔超期检测 | — |
| `ai_score.py` | AI味8维评分 | — |
| `chapter_stats.py` | 章节统计+断更告警 | — |
| `trending_news.py` | 热榜RSS拉取 | — |
| `novel_step.sh` | 流程锁（防跳步+产出物校验） | ✅ |
| `novel_check.sh` | 只读检查模式 | — |

### 发布脚本（`fanqie-publisher/scripts/`）

| 脚本 | 用途 |
|------|------|
| `publish_chapter.py` | 从本地MD发布到番茄后台（存草稿/发布） |
| `login_browser.py` | 首次登录番茄后台 |
| `qr_login.py` | 扫码登录 |
| `update_chapter.py` | 更新已发布章节 |

> 发布脚本依赖 Playwright。首次使用：`pip install playwright && playwright install chromium`

## 安装

```bash
# 1. 克隆到 Hermes 技能目录
cd ~/.hermes/skills/
git clone https://github.com/<user>/novel-writing-system.git novel

# 2. 安装 Python 依赖（可选，按需安装）
pip install -r novel/requirements.txt

# 3. 确保数据目录存在
mkdir -p ~/novels/_shared/{logs,backups,scripts}

# 4. 新建第一本书
# 在 Hermes 中说「新开一本书」，引导式初始化
```

## 可选依赖

- **jieba**：提升 AI味评分准确度
- **feedparser**：热榜RSS拉取（不用热榜功能可不装）
- **playwright**：番茄小说半自动发布
