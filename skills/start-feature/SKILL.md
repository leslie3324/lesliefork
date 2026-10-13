---
name: start-feature
description: 开始新需求、创建 feat 分支和独立 worktree 时使用。
---

# 开始新需求

1. 按用户确认的需求执行 [创建脚本](scripts/start_feature.py)：`python3 <脚本路径> <仓库路径> <feat分支名> <worktree路径>`。
2. 中大型需求加 `--docs`，按文档治理初始化 `docs/<分支名>/`：index、overview、design、decisions 和 `_scratch/`；只建草稿骨架，不覆盖已有内容。小改动不建。
3. 返回分支、基线 SHA 和路径；后续开发在新 worktree 中完成，不动原工作区和暂存区。

只从最新 `origin/pro` 创建，绝对禁止使用 test 或将 test 回灌 feat。
