---
name: novel-publishing
description: 网文平台草稿箱投递与核对：登录、草稿准备、保存、状态核对。覆盖番茄平台已验证流程。
category: novel
---

# 网文平台半自动发布

## 概述

通过固定浏览器 profile 在作者后台完成章节草稿箱投递。核心流程：扫码登录 → 读取本地 MD → 填入后台 → 保存草稿 → 草稿箱核对 → 结束。

参考 `fanqie-author-publish` (owlco001/owlco001) GitHub 技能包的工作流设计。

## 触发条件

- 「发布这章到番茄」「把XX章发到后台」「准备草稿」「检查发布状态」
- 任何涉及到作者后台操作章节的请求

## 能力边界与安全铁律

1. **本能力只负责把本地章节送入后台草稿箱并核对，终点是 `draft_saved_verified`。**
2. **绝不执行正式发布、确认发布、定时发布或任何使章节对读者可见的动作。**
3. **草稿保存成功后直接汇报，不再询问用户是否正式发布。**
4. 用户口语说「发布第 X 章」时，按既定约定解释为「送入草稿箱」；只有用户特别强调正式发布时，明确说明当前能力止于草稿，仍不执行。
5. **遇到验证码/风控/页面结构变化 → 立即停止**，不要盲点按钮。
6. **每步操作后先验证状态**，确认成功再继续。
7. **关键节点截图留痕**（编辑器加载、草稿保存、草稿箱核对）。
8. **不要要求用户提供密码**。用扫码登录。

## 通用工作流

### 1. 登录（Playwright 固定 profile — 番茄已验证）

```python
from playwright.sync_api import sync_playwright
p = sync_playwright().start()
ctx = p.chromium.launch_persistent_context(
    user_data_dir='~/.hermes/browser-profiles/fanqie',
    headless=False,
)
```

登录态持久化：同一 `user_data_dir` 内 cookies 跨会话保持。用户只需在 Playwright Chromium 中手动登录一次（扫码或SMS）。

### 2. 登录后导航

登录成功后，按以下顺序操作：
1. 确认在作家后台首页
2. 定位目标作品 → 进入作品管理页
3. 进入章节管理 → 选择「新建章节」或「编辑草稿」

### 3. prepare_draft（准备草稿）

```
输入：book_name, chapter_title, chapter_body, source_file
输出：草稿已保存 / 失败原因
```

步骤：
1. 确认目标作品、章节标题、正文
2. 在编辑器中填入标题
3. 填入正文（从本地 MD 文件读取）
4. 等待编辑器接收内容后，确认内容正确
5. 点击「保存草稿」
6. 等待成功提示
7. 截图存档

### 4. review（草稿保存前检查）

检查项：
- 作品名称正确
- 章节标题正确
- 正文非空且无截断
- 「存草稿」按钮可用

输出：`ready to save draft` / `not ready` + 阻塞原因

### 5. reconcile（核对草稿状态）

保存草稿后进入草稿箱，核对：
- 作品名正确
- 章节号、标题正确
- 正文非空，后台字数合理
- 草稿数量与本次投递数量一致

核对成功即结束任务。不要进入发布流程，不要询问是否继续正式发布。

### 6. reconcile（本地与草稿箱对账）

对比平台章节列表和本地 MD 文件：
- 哪些章已发布
- 哪些是草稿
- 哪些缺失
- 标题是否一致

## 状态机

```
pending → backend_opened → book_selected → editor_opened
       → draft_loaded → draft_saved → draft_saved_verified → completed
```

失败路径：任何步骤异常 → `failed_needs_review`，报告最后成功步骤和阻塞原因。

## 输入格式

从本地 MD 文件构造：

```json
{
  "book_name": "作品名",
  "chapter_title": "第N章 标题",
  "chapter_body": "正文内容（从MD读取）",
  "action": "prepare_draft|review|reconcile",
  "source_file": "/absolute/path/to/chapter.md",
  "notes": "可选备注，如：发布前检查结尾伏笔"
}
```

## 本地章节 → 后台映射

后台状态 vs 本地 MD 的处理策略：

| 后台状态 | 本地有修改 | 操作 |
|---------|-----------|------|
| 已发布 | 有 | 谨慎：已发布章节不建议覆盖，除非是紧急修文 |
| 定时发布 | 有 | 仅识别并报告状态，不取消定时、不修改、不重新定时 |
| 草稿 | 有 | 直接覆盖草稿内容 |
| 不存在 | — | 新建章节 |

## 平台特定信息

### 番茄小说

> 详细技术细节见 `fanqie-publisher` 技能（BOOK_ID、选择器、弹窗处理、已发布vs待发布分支）。

**当前方案**：Playwright + 固定浏览器 profile（`~/.hermes/browser-profiles/fanqie`），不用 Hermes browser 工具。

核心差异：
- **新建章节/草稿**：有序号+标题两个字段，有「存草稿」按钮
- **编辑草稿**：使用草稿编辑链接，修改后仍只保存草稿
- **已发布章节**：只做状态识别，不进入编辑或重新发布流程
- **正文必用 innerHTML**：ProseMirror 拒绝所有键盘粘贴/输入

### 七猫小说
- 同规格技能骨架存在：`qimao-author-publish`（GitHub 同仓库）
- 页面结构待校准

### 百度作家平台
- 同规格技能骨架存在：`baidu-author-publish`（GitHub 同仓库）
- 页面结构待校准

## 失败处理

任何步骤失败时：
1. 立即停止流程
2. 记录最后成功步骤
3. 能截图就截图
4. 告诉用户具体失败点和需要的手动操作

常见失败：
- **登录失效** → `pkill -f "Google Chrome for Testing"` 后重启，用固定 profile 重新登录
- **ProseMirror 不接收内容** → 必须用 `innerHTML` 直接写 DOM，paste/keyboard 全部无效
- **弹窗挡操作** → 先 Escape 两次，再 force=True 点击按钮
- **".first()" 报错** → Playwright 1.60 不用 `.first()`，直接用 selector
- **草稿保存结果不明确** → 返回草稿箱核对章节号、标题、字数；不要点击其他发布相关按钮
- 验证码/风控 → 停止，让用户手动处理

## 注意事项

- 此技能处理的是**已写好章节的草稿箱投递与核对**，不具备正式发布能力
- 写作流程见 `novel-writing`、`novel-main` 等技能
- 平台运营策略见 `novel-platform`
- 不要试图提取/导出/搬运 Cookie，用固定浏览器 profile 保持登录态
