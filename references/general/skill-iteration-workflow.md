# 技能迭代方法论：审查 → 修复 → 收敛

> 记录 2026-07-24 小说技能体系（10 个 skill）从骨架到生产级的迭代过程。

## 流程

```
双审并行（Claude Code + delegate_task）→ 合并发现 → Claude Code 修 → 再审 → 到零阻断
```

## 关键原则

### 1. 修复用 Claude Code，不用 delegate_task
- `delegate_task`：余额限制、模型锁死在当前 provider、上下文继承
- `claude -p '任务' --model sonnet --dangerously-skip-permissions`：独立进程、无限制
- 铁律：改代码 = `claude -p`，审查可混用两者

### 2. 审查至少两个视角并行
- Claude Code（独立模型） + delegate_task（Hermes 内置）
- 互补视角，经常发现对方漏掉的问题

### 3. 不等结果，流水线
- 修完立刻开下一轮审查
- 节奏：修 → 审 → 修 → 审 → 到零阻断

### 4. P0 阻断优先
- 只修让流程中断的 bug
- 收敛标准：两轮连续零阻断 + 两个审查方都确认

## 实际迭代记录

| 轮次 | 阻断数 | 典型问题 |
|------|--------|---------|
| 1 | ~10 | 参数不匹配、文件缺失、规则矛盾 |
| 2 | 5 | 边界未处理、接口不一致 |
| 3 | 4 | 状态机循环断裂、模板空 |
| 4 | 3 | 3章vs5章、脚本bug |
| 5 | 进行中 | — |

## 常见问题类型

| 类型 | 示例 | 为什么容易漏 |
|------|------|------------|
| 参数名不一致 | main 传 `book_name`，子技能用 `书名` | 技能独立维护 |
| 数字不同步 | 3章 vs 5章、19条 vs 9条 | 多处引用 |
| 文件缺失 | 引用 `作者设定.md` 但未创建 | 设计时有、写入时漏 |
| 脚本 bug | `split('\n')` 被换行截断 | 嵌入 MD 的代码难测试 |

## Claude Code 常用参数

```bash
# 审查
claude -p "审查 ~/.hermes/skills/novel/ 全部。🔴阻断bug。" --model sonnet --max-turns 10

# 修复
claude -p "修复问题描述" --model sonnet --max-turns 20 --dangerously-skip-permissions
```
