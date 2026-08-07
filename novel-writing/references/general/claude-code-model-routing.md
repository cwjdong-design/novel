# Claude Code 模型路由（pandai 中继）

> 2026-08-04 实测数据。pandai 中继通过 `~/.claude/settings.json` 的 env 映射 Claude Code 模型。

## 模型映射

| Claude Code --model | 实际模型 | 中继标识 |
|---------------------|----------|----------|
| opus | glm-5.2 | ANTHROPIC_DEFAULT_OPUS_MODEL |
| sonnet | deepseek-v4-pro | ANTHROPIC_DEFAULT_SONNET_MODEL |
| haiku | deepseek-v4-flash | ANTHROPIC_DEFAULT_HAIKU_MODEL |

## 长 prompt（3000-4000 字）性能实测

| 模型通道 | 短 prompt（<200字） | 长 prompt（3000-4000字小说骨架） | 结论 |
|----------|---------------------|------------------------------|------|
| opus（glm-5.2） | 7-17 秒正常 | **卡死，零产出，120秒超时** | 不可用于小说 DRAFT/POLISH |
| haiku（v4-flash） | 7 秒正常 | 98秒/超时（不稳定） | 不可靠 |
| sonnet（v4-pro） | 13秒正常 | **38-50 秒稳定出完整稿件** | ✅ 推荐用于小说创作 |

## sonnet/v4-pro 已知缺陷：DRAFT 字数不足

deepseek-v4-pro 处理 3000-4000 字骨架 prompt 时，输出正文稳定在 1550-2100 字（番茄下限 2200）。连续 4 章（Ch34-37）全部触发， shortfall 范围 90-650 字。

根因：模型精简骨架叙述指导，保留对话但压缩环境描写和过渡段。

这不是致命问题——DRAFT 返回后主 Agent 用 2-4 次 patch（每次 30-50 字有效剧情）即可补到 2200+。但不要重试 Claude Code 试图让它一次写够。

## 排查方法论

当 Claude Code `claude -p` 零产出超时时：

1. **先测短 prompt**（`claude -p "说你好" --model <model> --max-turns 1`）→ 排除网络/认证问题
2. **再测同 prompt 不同 model** → 确认是模型问题还是 prompt 问题
3. **检查 settings.json 中的模型映射** → pandai 中继的 opus/sonnet/haiku 映射到不同实际模型
4. **max-turns 无关** → max-turns=1 仍卡死说明问题在输入处理，不在 turn 循环

诊断顺序（本次排查实际路径）：
```
短prompt+opus=正常 → 长prompt+opus+max-turns1=超时 → 不是turn循环问题
长prompt+sonnet=38秒正常 → 确认opus通道的长上下文处理有缺陷
长prompt+haiku=98秒/超时 → haiku也不可靠
结论：只有sonnet/v4-pro能稳定处理长小说prompt
```

## 运行状态判定：总时长不等于停滞

`claude -p` 的非流式 `--output-format json` 只会在进程结束时输出完整结果。若 stdout 被重定向到 `result.json`，运行中保持 0 字节是正常现象，不能据此判断”没有工作”。小说长章也可能在 120 秒后才首次写盘。

### 推荐观测信号

优先使用 `claude_runner.py`（封装在 `scripts/claude_runner.py`）统一管理子进程生命周期，它使用 `--output-format stream-json --verbose` 并同时观测：

1. 最近一次 stdout JSONL 事件时间；
2. 最近一次工具调用/结果时间；
3. 唯一目标文件的 SHA-256、mtime 和大小是否变化；
4. 是否已出现最终 `type=result` 事件；
5. **连续无 stdout 活动时间**（`idle_timeout`），而不是进程累计运行时间。

### claude_runner.py 状态字段

| status | 含义 | 附加字段 |
|--------|------|----------|
| `success` | 收到 `type=result` 且子进程正常退出 0 | `result`（最终事件 dict） |
| `stalled` | 收到最终结果前，连续无 stdout 事件 ≥ `idle_timeout` 秒 | `idle_seconds` |
| `exit_timeout` | 已收到 `type=result`，但子进程在 `exit_timeout` 内未退出 | `result_received=true` |
| `no_result` | 进程退出 0 但未收到 `type=result` | — |
| `error` | 进程非零退出 | `exit_code`, `stderr`（如有） |

### CLI 用法

```bash
python3 ~/.hermes/skills/novel/scripts/claude_runner.py \
  --prompt-file /path/to/prompt.txt \
  --model sonnet \
  --max-turns 15 \
  --allowed-tools Read,Write,Edit \
  --idle-timeout 120 \
  --exit-timeout 10 \
  --target-file /path/to/output.md \
  --events-file /path/to/events.jsonl \
  --output-file /path/to/result.json
```

退出码：0 = success，2 = stalled，3 = 其他失败，4 = exit_timeout。stdout 输出 JSON 格式的包装器结构化结果。

### 判定规则

- **仍在工作**：持续有 stdout JSONL 事件，或目标文件刚发生预期变化；继续等待合理收尾时间。
- **产物已落盘但未结束**：先验收磁盘产物，同时继续观察；不要立即杀进程，以免截断模型的回读或最终回复。`idle_timeout` 是连续无 stdout 事件时长，产物落盘不会重置它，但只要仍有 stdout 事件就不会触发 stall。
- **真实上游停滞**：某次工具结果后发起下一轮模型请求，连续较长时间没有新 stdout 事件；保留 stream/debug 证据后终止。此时返回 `status=stalled`，允许**一次**干净重试；连续两次 `stalled` 上报后由主 Agent 接管。
- **退出阶段异常**：已经出现最终 `type=result`，但进程在 `exit_timeout` 内仍不退出；包装器返回 `status=exit_timeout` 并清理子进程，此时再调查 Stop hook、插件、遥测 flush 或子进程句柄。

### 工具权限要与任务契约一致

不要一边只允许 `Read,Write`，一边要求 Claude 自己运行 Bash 统计字数。DRAFT/POLISH 只负责正文读写；字数、违禁词、系统面板和一致性由主 Agent 在进程结束后运行确定性脚本验收。这能减少权限拒绝、无效轮次和误判超时。

### 已验证诊断样例（2026-08-06）

- DRAFT：开始约 124 秒后才 Write 正文，随后又尝试统计和回读；若用固定短时限会误判为卡死。`claude_runner.py` 的 idle_timeout 基于连续无 stdout 事件，Write 操作会伴随工具事件流，因此不会误杀。
- POLISH：Read 在约 5 秒完成，第二轮中继请求约 115 秒无 stdout 事件；属于单次上游流请求停滞，`claude_runner.py` 会正确返回 `status=stalled`。
- 对照：同一机器上 `Read → READ_OK` 工具循环，sonnet 约 7 秒、opus 约 11 秒正常返回并退出；Stop hook 与通用退出路径正常。

## 故障处置

1. 先区分”总时长长””工具验收仍在运行””上游无 stdout 事件””最终 result 后不退出”四类状态。
2. 真停滞时保存 stream-json events 日志和目标文件哈希；`claude_runner.py` 的 `--events-file` 会实时记录所有合法 JSON 事件。
3. 目标正文已落盘时先做本地验收，防止盲目重试覆盖有效产物。
4. 上游单次停滞可做一次干净重试；连续两次 `stalled` 后再由主 Agent 接管。
5. 用户等待期间用简短进度说明报告”正在生成/已写盘待验收/上游无活动”，不要笼统说”卡死”。

## 用户敏感度

用户对无反馈等待敏感。长任务应通过 `claude_runner.py` 后台执行，用 `--events-file` 和 `--target-file` 提供真实进度；idle_timeout 基于连续无 stdout 事件（非总时长），产物落盘不会触发误杀。不要在没有新证据时反复重试。

### Hermes 调用注意事项

- 长任务不要用前台 `terminal(..., timeout=N)` 包裹：这个 `timeout` 仍是累计总时限，会在任务持续有事件时发送终止信号，重新制造误杀。应使用 `terminal(background=true, notify_on_complete=true)`，由 `claude_runner.py` 的 `idle_timeout` / `exit_timeout` 负责监督。
- 若 Claude Code 的测试任务文本包含进程生命周期词，Hermes Gateway 的生命周期扫描器可能在工具调用前误拦。先检查 stream 事件与磁盘产物；确认是扫描误拦后，可在独立 macOS Terminal Shell 执行同一命令，仍由 `claude_runner.py` 记录事件和结果。
