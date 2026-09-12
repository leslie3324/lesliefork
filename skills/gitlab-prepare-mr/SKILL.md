---
name: gitlab-prepare-mr
description: 主动准备 GitLab 合并请求时使用：将一个已完成的 feat 分支合并到 test、pro 或指定目标分支，并希望在提 MR 前真实检测 Git 冲突。无冲突时直接创建原 feat 到目标分支的 MR；有冲突时仅在证据和校验充分时创建目标分支上的候选解决 MR，不确定时停止并要求用户确认。
---

# GitLab 冲突预检并提 MR

仅在用户明确调用 `$gitlab-prepare-mr` 或明确要求“准备/创建这次 GitLab MR”时使用。一次调用只处理一个 `source -> target`。

默认将当前已提交的分支作为 `source`；`target` 必须由用户明确给出，通常是 `test` 或 `pro`。用户可显式指定 `--source <branch>`。

## 硬边界

- 不把 `test` 或 `pro` 合入原始 `feat`。原 `feat` 必须保持纯净，避免后续 `feat -> pro` 带入其他测试需求。
- 不自动 approve、merge、关闭已有 MR、force-push，或修改目标分支。
- 只在用户的本次主动调用中创建远程分支或 MR。没有这项明确调用时只做只读分析。
- 不以模型自评作为安全依据。Git 的实际合并结果是文本冲突的唯一判据。
- 不处理工作树中未提交的改动；说明它们未包含在 MR 中，要求先提交、暂存或清理后重试。
- 若已有同一 `source -> target` 的 MR，不重复创建；有冲突时可创建替代候选 MR，但不自动关闭旧 MR。

## 输入与前置检查

1. 确认当前仓库、远程、`source`、`target` 和用户的意图。目标不是 `test`/`pro` 时，回显准确分支名后再继续。
2. 运行 `git branch --show-current` 和 `git status --short --branch`。`source` 必须指向已提交的 SHA，不能把未提交文件悄悄带入。
3. 运行 `git fetch --prune origin`，记录并在报告中保留：`source SHA`、`target SHA`、`merge-base SHA`。
4. 确认 GitLab 项目和 `glab` 身份可用。只在即将创建分支/MR 时才调用写入命令；不要打印 Token、Cookie 或远程凭据。

## 先做真实合并预演

在目标 SHA 的临时 worktree 中预演 `target <- source`，不要在原工作区操作。

```bash
git worktree add --detach <temporary-worktree> <target-sha>
git -C <temporary-worktree> merge --no-commit --no-ff <source-sha>
git -C <temporary-worktree> diff --name-only --diff-filter=U
git -C <temporary-worktree> ls-files -u
```

不要用搜索 `=======` 或 LLM 猜测代替这一步。

### 预演无冲突

- 在临时 worktree 中运行项目能明确识别出的基础校验；校验失败要如实记录，不把它伪装成通过。
- 清理临时 merge/worktree。
- 创建普通 MR：`source -> target`。不要创建 `ai/resolve/...` 分支，不要改写 `source`。
- MR 描述写明源、目标和三项 SHA；没有冲突即是本次直接提原 feat MR 的依据。

### 预演有冲突

1. 收集冲突文件、`git diff --cc`、两侧相关提交、已有 MR 描述、Issue/需求和项目约定。先理解双方意图，再编辑 hunk。
2. 中止并清理仅用于预演的 merge/worktree；从**同一个 target SHA** 建立独立候选 worktree 和本地候选分支，命名为 `ai/resolve/<source>-to-<target>-<target-short-sha>`。
3. 在候选 worktree 执行 `git merge --no-commit --no-ff <source-sha>`，再逐 hunk 解决。尽量保留两侧意图；真正不兼容时，记录选择、放弃的行为和依据。不要引入任一分支都没有的新业务行为，也不要用盲目的 `--ours` 或 `--theirs` 消除标记。
4. 只编辑解决冲突所需文件。若需要扩展改动，先说明原因并重新评估，不要顺手重构。

## 是否允许自动创建候选 MR

对已解决的冲突使用下面四项证据评分；缺失事实不得给分。

| 项目 | 满分 | 得分条件 |
| --- | ---: | --- |
| 意图依据 | 25 | 两侧均能从提交、MR、Issue/需求或明确代码约定说明目的 |
| 改动范围 | 25 | 解决结果仅覆盖冲突 hunk 和必要的编译修复，没有无关文件/行为 |
| 风险边界 | 25 | 不涉及下列高风险区域，且无跨服务语义不确定性 |
| 验证证据 | 25 | 无未解决索引、`git diff --check` 通过，且项目已识别的编译/测试/格式检查通过 |

以下任一条件是硬停止，不评分、不 push、不创建候选 MR：

- SQL/DDL/数据迁移、鉴权/权限、密钥、部署或生产配置、公共 API/DTO/跨服务协议发生冲突；
- 无法追溯一侧的业务意图；
- 仍有未解决冲突、校验失败，或解决结果超出冲突所需范围；
- 目标 SHA 在解决过程中变化，或候选分支已被他人修改。

只有总分 `>= 90` 且没有硬停止项，才允许继续。低于 90 时，输出每个未决 hunk 的上下文、两个可选方案和缺失证据，等待用户确认；不要生成半成品远程分支。

## 创建候选 MR

满足自动条件后：

1. 在 commit 前确认 `git ls-files -u` 为空、`git diff --check` 通过，并运行已识别的项目校验。
2. 完成候选分支的 merge commit。
3. 只 push 新的 `ai/resolve/...` 分支，绝不 force-push。
4. 创建 `ai/resolve/... -> target` 的 GitLab MR。该 MR 是原 `source -> target` 的替代候选，不是将 target 回灌到原 feat。
5. 在 MR 描述中写清：原 source、target、三项 SHA、冲突文件/hunk、每项取舍、评分、实际校验命令和结果、未覆盖的验证边界。
6. 若调用时传入已有 MR，附上旧 MR 链接，但不自动关闭、评论或修改它。

候选处理完成后安全移除临时 worktree。目标分支产生新 SHA 后，旧候选结果失效；再次触发时重新预演，不复用旧结论。

## 输出

- 无冲突：返回原 `feat -> target` MR 链接和预演 SHA。
- 自动解决：返回候选 MR 链接、评分、逐 hunk 决策和校验结果。
- 停止处理：返回明确的阻塞项和用户需要确认的最小决策；不声称已准备好 MR。
