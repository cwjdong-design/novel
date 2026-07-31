# 多文件技能系统调试与迭代教训

从 10+ 轮审查修复小说技能系统的实战中总结。

## 1. 不要在 Skill Markdown 中嵌入可执行代码

嵌入在 ```python``` 代码块中的脚本无法被测试、lint 或版本管理。应提取到独立文件，SKILL.md 只保留引用。

## 2. 双模型并行审查

Claude Code CLI + delegate_task 同时审，视角互补。合并去重后一次性修复。

## 3. 批量修复，不打地鼠

审查发现全部 bug → 一次性传入 Claude Code CLI 修完所有 → 再审确认。不要修一个冒一个。

## 4. delegate_task vs Claude Code CLI

代码修改用 Claude Code CLI（独立进程、可选模型、更稳定）。审查分析用 delegate_task（更便宜）。

## 5. 结构性修复优先

同一类 bug 反复出现 3+ 轮 → 说明有结构问题，需要重构而非继续打补丁。
