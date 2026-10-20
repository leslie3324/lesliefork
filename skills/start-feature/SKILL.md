---
name: start-feature
description: 用户明确要开始代码改动时，用于从最新 origin/pro 创建已确认名称的主功能分支和集成 worktree；需求澄清前默认不创建文档。
---

# 开始新需求

## 分支名确认

- 先取得完整分支名。优先使用用户明确给出的分支名；用户提供飞书需求链接时，读取需求绑定的分支；需求没有绑定分支时，可以根据需求编号和标题提出候选分支名。
- 无论分支名来自用户、飞书需求还是 Agent 候选，执行创建脚本前都必须把完整分支名交给用户确认；未确认不得创建分支或 worktree。
- 分支名不限制 `feat/`、`feature/` 等业务前缀，只需通过 Git 分支名校验。

1. 用户明确要开始代码改动，并确认仓库、完整分支名和 worktree 路径后，执行 [创建脚本](scripts/start_feature.py)：`python3 <脚本路径> <仓库路径> <功能分支名> <worktree路径>`。这是主 Agent 的集成 worktree。
2. 先创建 worktree，不预判需求规模、不默认生成文档；随后在该 worktree 中运行 `grill`。由 Agent 提出规模、文档和并行建议，用户决定。
3. 用户确认需要文档后，在已有 worktree 上追加 `--init-docs`；确认并行开发时再加 `--parallel`。已在创建时确认文档的，可以使用 `--docs`，并行时加 `--parallel`。
4. 返回分支、基线 SHA 和路径；后续分析与集成在主功能分支 worktree 完成，不动原工作区和暂存区。

只从最新 `origin/pro` 创建，绝对禁止使用 test 作为基线或将 test 回灌功能分支。
