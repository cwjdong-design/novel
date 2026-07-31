# 脚本健康检查清单

> 来源：2026-07-27 全量审查——发现 novel-main 引用的 `review_scan.py` 从未被创建，导致系统术语扫描完全失效。
> 触发：每次全量审查时 / 发现脚本调用失败时 / 新增脚本后。

## 反模式：路径断链

```
技能引用了脚本 → 脚本路径写的是正确的 → 但脚本文件不存在
```

症状：REVIEW 步骤正常执行，但 `review_scan.py` 报 "file not found" 被静默吞掉，所有系统违禁术语（投放回收比/宿主等）从未被扫描。

## 检查清单

每次全量审查时执行：

```bash
# 1. novel-main 引用的所有脚本是否真实存在
grep -oP 'python3\s+\K[^\s]+' ~/.hermes/skills/novel/novel-main/SKILL.md | while read p; do
  [ -f "$(eval echo $p)" ] && echo "✅ $p" || echo "❌ 缺失: $p"
done

# 2. novel-cron 引用的所有脚本是否真实存在
grep -oP 'python3\s+\K[^\s]+' ~/.hermes/skills/novel/novel-cron/SKILL.md | while read p; do
  [ -f "$(eval echo $p)" ] && echo "✅ $p" || echo "❌ 缺失: $p"
done

# 3. 所有脚本的 exit code 约定是否与调用方一致
#    review_scan.py → exit 1 = 有问题 → novel-main 应阻塞
#    consistency_check.py → exit 1 = 有🔴问题 → novel-main 应阻塞
```

## 当前脚本清单（2026-07-27 验证通过）

| 脚本 | 路径 | 调用方 | 存在 |
|------|------|--------|:--:|
| review_scan.py | `~/.hermes/skills/novel/scripts/` | novel-main | ✅ |
| consistency_check.py | `~/.hermes/skills/novel/scripts/` | novel-main | ✅ |
| novel_scan.py | `~/.hermes/skills/novel/scripts/` | novel-cron | ✅ |
| foreshadow_check.py | `~/.hermes/skills/novel/scripts/` | novel-cron | ✅ |
| backup_chapter.py | `~/.hermes/skills/novel/scripts/` | novel-main | ✅ |
