---
name: start-feature
description: 用户明确要开始代码改动时，用于从最新 origin/pro 创建主 feat 分支和集成 worktree；需求澄清前默认不创建文档。
---

# 开始新需求

1. 用户明确要开始代码改动后，按确认的仓库、分支名和路径执行 [创建脚本](scripts/start_feature.py)：`python3 <脚本路径> <仓库路径> <feat分支名> <worktree路径>`。这是主 Agent 的集成 worktree。
2. 先创建 worktree，不预判需求规模、不默认生成文档；随后在该 worktree 中运行 `grill`。由 Agent 提出规模、文档和并行建议，用户决定。
3. 用户确认需要文档后，在已有 worktree 上追加 `--init-docs`；确认并行开发时再加 `--parallel`。已在创建时确认文档的，可以使用 `--docs`，并行时加 `--parallel`。
4. 返回分支、基线 SHA 和路径；后续分析与集成在主 feat worktree 完成，不动原工作区和暂存区。

只从最新 `origin/pro` 创建，绝对禁止使用 test 或将 test 回灌 feat。
