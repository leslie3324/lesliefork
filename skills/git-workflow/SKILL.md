---
name: git-workflow
description: 涉及 Git 相关操作时使用。
---

# Git 操作

- 遵循目标仓库规则；先分析、给建议，确认后操作，不动无关改动。
- pro 更新时，获取最新状态，对比当前 feat 的提交、冲突和业务影响，建议是否同步及处理方式。
- **绝对禁止 test 回灌 feat，即使用户确认也不执行；其他 Git 操作或中转分支也不能绕过。**
- 准备或创建 MR、处理 MR 冲突时，读取 [MR 规则](references/gitlab-mr.md)。
- 简短说明结果、未解决问题和下一步。
