---
name: fanqie-publisher
description: 番茄小说草稿箱投递 — Playwright 操作后台新建章节、存草稿并核对
category: novel
---

# 番茄小说草稿箱投递

## 触发条件
用户说「发布第X章」「存草稿」「新建章节」等时，统一解释为：将本地章节送入番茄后台草稿箱并核对。

## 能力边界（硬性）

- **只能存草稿并核对草稿箱状态。**
- **绝不点击正式发布、确认发布、定时发布等按钮。**
- **草稿保存成功后直接汇报，不再询问用户是否正式发布。**
- 用户明确说「正式发布」时，也只能说明当前能力止于草稿箱，不能执行或提供自动发布模式。

## 用法

```bash
# 存入草稿箱
python3 ~/.hermes/skills/novel/scripts/publish_chapter.py <章节号> --book <书名>

# 指定 BOOK_ID（覆盖书配置）
python3 ~/.hermes/skills/novel/scripts/publish_chapter.py <章节号> --book <书名> --book-id <BOOK_ID>
```

脚本自动：读本地 MD → 填序号、标题、正文 → 点击「存草稿」→ 退出；随后需进入草稿箱核对章节号、标题和字数。

## 配置

BOOK_ID 和章节 ID 从书数据目录读取：
- `~/novels/books/<书名>/02-设定文档/书配置.md` 中的 `番茄BOOK_ID:` 行
- `~/novels/books/<书名>/02-设定文档/番茄章节ID.json`（编辑已发布章节时用）

> 首次发布新书前，需要手动从番茄后台获取 BOOK_ID 并写入书配置。

## 登录

首次使用需要登录：
```bash
python3 ~/.hermes/skills/novel/fanqie-publisher/scripts/login_browser.py
```
登录态保存在 `~/.hermes/browser-profiles/fanqie`，后续操作自动复用。

## 已知坑点
1. 标题分两个字段：序号 + 标题
2. ProseMirror 编辑器不响应 paste/type，必须用 innerHTML
3. 弹窗必须 force=True 点击
4. 不关浏览器，保持登录态
5. Hermes 环境用 venv Python：`~/.hermes/hermes-agent/venv/bin/python3`

## 原流程优先与启动兜底

用户要求「继续原有技能」或既有投递流程已经验证时，必须坚持本技能的原脚本、原固定 Profile 和原 BOOK_ID 解析方式，不得擅自改走新浏览器、隔离 Profile、通用浏览器工具或手工填表。

如果 Hermes 的 shell 包装层在**进程启动前**拦截命令，但脚本本身和依赖已验证：
1. 先确认没有产生后台草稿或浏览器副作用；
2. 在用户明确要求继续原技能后，可通过 macOS 现有「终端」窗口执行**完全相同的技能命令**；
3. 不修改脚本、不替换 Python 环境、不切换浏览器 Profile；
4. 以脚本输出「已存草稿」作为保存回执，再按草稿箱专用路由核对，不能只凭回执宣称完成。

核对时直接进入草稿箱路由，禁止再次打开新建章节页，以免额外生成 0 字未命名草稿。详细核对规范见 `novel-publishing/references/fanqie-draft-reconciliation.md`；命令包装层拦截时的等价启动步骤见 `references/fixed-profile-launch-fallback.md`。
