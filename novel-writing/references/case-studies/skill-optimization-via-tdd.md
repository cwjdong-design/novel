# 技能优化 TDD 方法论

> 2026-08-02 小说技能链优化实战复盘。适用场景：系统性修改多个 SKILL.md + 脚本，需要验证修改有效且不破坏现有行为。

## 核心方法：TDD 应用于技能文件

将 TDD 的 RED-GREEN-REFACTOR 循环适配到技能文档修改：

| TDD 概念 | 技能修改 |
|----------|---------|
| 测试用例 | pytest 测试 + 契约正则 |
| 生产代码 | SKILL.md 文档 + Python 脚本 |
| RED | 旧技能下测试因新契约缺失而失败 |
| GREEN | 修改技能使测试通过 |
| REFACTOR | 清理残留旧口径 |

## 关键步骤

### 1. RED 阶段 — 写测试先于改技能
- 创建 `tests/test_skill_contracts.py`：用正则验证 SKILL.md 中的口径（字数范围、禁止规则、门禁存在性）
- 创建 `tests/test_review_scan.py`：用 subprocess 调用脚本，验证 JSON 输出结构
- 运行测试确认全部失败，且失败原因是"新功能缺失"而非语法错误

### 2. 备份 + 哈希基线
```bash
# 技能备份
cp -r novel-plot/ novel-skeleton/ ... /backup/path/
# 正文哈希（证明未修改正文）
sha256sum ~/novels/books/<书名>/01-正文存稿/*.md > /tmp/novel_chapters_before.sha256
```

### 3. GREEN 阶段 — 主 Agent 直接实现
- **不要把整个 GREEN 委托给 Claude Code** — 多文件修改任务容易耗尽 max-turns
- 主 Agent 用 `patch` 工具逐文件修改，每个 patch 只改一处
- 先改脚本（review_scan.py），运行测试确认扫描器 GREEN
- 再改 SKILL.md（批量 patch），运行全量测试

### 4. 拆分策略（避免 Claude Code 超时）
如果必须委托 Claude Code：
- 按"关注层"拆分：一次只改一类文件
- 例如：第一调改 scripts/，第二调改 SKILL.md A-C，第三调改 SKILL.md D-F
- 每调限制 max-turns 15-20，prompt 写到 /tmp 文件用 `$(cat)` 传参

### 5. 独立验证（替代交叉模型审查）
当 Claude Code 审查任务也超时时，用 `execute_code` 跑独立验证脚本：
- 检查所有文件是否还残留旧口径字符串
- 检查正文/进度文件哈希是否匹配
- 运行 pytest + py_compile
- 检查 git diff 是否触碰了不该碰的文件

## 三大遗漏（用户发现，TDD 没覆盖）

> 这些是测试通过了但用户仍然不满意的问题。TDD 只验证了"规则是否写入了"，没验证"内容是否一致了"。

### 遗漏1：只改规则行不改示例文字（参数滚排不完整）

改了"2200—2400"的规则声明，但以下位置仍引用旧值：
- 章节结构模板：开场350/推进1600/高潮450/钩子100 = 2500（应为2250）
- prompt 铁律行：仍写"2000-3000字"
- 审查清单自检项：仍写"每200字微钩子"
- frontmatter 描述：仍写"约2500字"
- 五感密度自检："是否有至少2种感官"仍是配额思维

**修复方法**：`grep -r '旧值' skills/` 全局搜索残留。验证每处模板的字数加总。

### 遗漏2：没更新 README 和版本号

- 目录结构仍引用旧扁平 .md 格式（应改为 SKILL.md 子目录）
- 技能列表仍写 ~2500字
- 创建时间没更新
- 一次性 PLAN-restructure.md 留在了公开仓库

**修复方法**：README 全量同步 + git rm 一次性文件 + .gitignore 加规则。

### 遗漏3：护栏 vs 内容（质量观修正）

护栏（字数门禁、死水段扫描）拦的是垃圾，但写不出好故事。
用户原话："AI就是为来写而写，浪费token。"

**修复方法**：在 PLOT 阶段注入戏剧冲突——
- 三问法：有人不高兴吗？主角做了什么艰难决定？下一章的麻烦种下了吗？
- 好消息+但是=戏剧：盈利了但利润结构不可持续
- 让受益者和受害者同时在场
- 用第三方的嘴戳破表面

护栏是必要的但不充分的。PLOT 才是质量源头。

## GitHub 发布卫生清单

推送到公开仓库前：
1. 脱敏扫描（token/密钥/手机号/邮箱/IP）
2. 排除非本次变更（用户原有改动不纳入提交）
3. 移除一次性文件（PLAN/debug/临时计划）+ .gitignore 规则
4. 更新 README（目录/列表/版本/脚本描述）
5. 确认 _state/ 等敏感目录被 gitignore

## 常见陷阱

| 陷阱 | 对策 |
|------|------|
| 测试写得太宽泛（任意匹配旧口径） | 用精确正则 + normalized 文本匹配 |
| 修改 SKILL.md 时"扩写环境细节"出现在禁止声明中 | 改用不含被禁词的措辞（如"不得用环境补字"） |
| 死水段检测中"结果"一词太宽泛 | 从 DYNAMIC_SIGNALS 中移除独立的"结果"词 |
| Claude Code 耗尽 max-turns 不等于完成 | 检查磁盘文件是否存在，不存在则主 Agent 接管 |
| 禁止声明中的措辞恰好匹配正则（"禁止每200字"匹配了"每200字"） | 验证脚本排除禁止语境中的匹配 |
| 测试通过但示例文字没更新 | TDD 只验证规则存在，不验证全文一致——需要额外的人工/grep 扫描 |

## 文件清单（本次实战）

- tests/test_review_scan.py — 11 项（字数边界、重复意象、死水段、机械提示不阻塞）
- tests/test_skill_contracts.py — 25 项（六技能口径、容量门禁、禁机械规则、双门槛、退回路径、main 接线）
- scripts/review_scan.py — 新增 count_fanqie_words / detect_repetition_imagery / detect_dead_water
- 6 个 SKILL.md — 统一 2200—2400、目标 2250；加容量门禁、禁机械规则、双门槛、退回路径
- README.md — 目录结构/技能列表/8步循环/脚本描述/版本时间全量同步
- .gitignore — 新增 .pytest_cache/ 和 PLAN-*.md 规则
