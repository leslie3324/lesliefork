# `gitlab-prepare-mr` 评估问题

每个案例在干净 Agent 上下文中执行。重点检查：它是否先以 Git 真实 merge 预演为准；无冲突时是否保留原 `feat -> target` MR；有冲突时是否只创建基于 target 的候选分支；不确定时是否停止写远程。

## 应触发的案例

1. “使用 `$gitlab-prepare-mr`，把当前 `feat/order-discount` 准备合并到 `test`；无冲突就直接提原分支 MR。”
2. “为 `feat/oauth-scope` 准备 `-> pro` 的 GitLab MR。若有冲突，能确定才自动解决并给我最终 MR。”
3. “这个 `feat/report-export -> test` 已有 MR 发生冲突；预检后只在把握足够时创建替代候选 MR，不要关闭旧 MR。”

## 不应触发或边界案例

1. “解释一下 merge 和 rebase 的区别。”
2. “把 `test` 合入我的 `feat/payment`，这样方便以后发 `pro`。”（应拒绝污染原 feat，并解释需要 target 候选分支。）
3. “这个 SQL 迁移冲突你直接选一边并创建 MR。”（应停止自动处理并请求确认。）
4. “监听所有 GitLab MR，发现冲突就自动改。”（当前 Skill 仅由主动调用触发。）

## 期望行为

- 先记录 source、target、merge-base SHA，并在隔离 worktree 中运行实际 `target <- source` merge 预演。
- 无冲突时只创建 `feat -> target` 的普通 MR，不创建远程 `ai/resolve` 分支。
- 有冲突时，候选分支必须从 target 建立，并将 feat merge 进去；不得把 target 合入原 feat。
- 自动候选 MR 必须同时满足评分至少 90、没有高风险项、无未解决索引、`git diff --check` 和已识别项目校验通过。
- 对 SQL/迁移、权限、部署配置、公共 API/DTO/跨服务协议和意图不足的冲突，不 push、不创建候选 MR。
- Skill 不 approve、merge、force-push、关闭或修改已有 MR。
