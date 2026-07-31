# 深度审查工具陷阱

> ⚠️ **特定书籍复盘文档**：以下内容来源于特定书籍的实战经验，其中的章节号、人物名、地名、数字均为该书的设定。方法论部分可通用参考，但具体数据不具有普适性。

> 2026-07-27 深度审查实战记录。纳入 novel-review 执行规范。

## review_scan.py 白名单误报

扫描器按子串匹配，白名单地名在特定上下文中会被误拆分：
- 「斤，穗城」「那片新塘」→ 匹配失败但实际无问题
- 判断标准：「穗城/海安/海康/珠河」→ 人工确认白名单内即通过
- 「X塘」类 → 检查是地点名（报）还是普通名词（跳过）
- Ch22-24 实测：28 命中全部误报，零实际违禁

## consistency_check.py 路径要求

必须传绝对路径，不能用相对路径：
```bash
# 正确
python3 ~/novels/_shared/scripts/consistency_check.py --book "$(pwd)"

# 错误
python3 ~/novels/_shared/scripts/consistency_check.py --book .
```

## novel_scan.py 参数

`--chapters N` 是整数（最近 N 章），不是逗号分隔列表：
```bash
# 正确: 扫描最近3章
python3 ~/novels/_shared/scripts/novel_scan.py --book "书名" --chapters 3

# 错误
python3 ~/novels/_shared/scripts/novel_scan.py --book "书名" --chapters "22,23,24"
```

## 跨文档同步滞后检测

深度审查时必须检查以下四项与最新章号是否匹配：
1. 系统状态.md 标题（如「截至 Ch.20」但最新 Ch.24）
2. 伏笔追踪表（已回收的伏笔是否仍标记为「远期」）
3. 故事线状态.md（最后一章梗概是否覆盖到最新章）
4. 人物总表.md（新出场人物的注册状态）

不匹配 = 一级阻塞，下一章开始前必须解决。
