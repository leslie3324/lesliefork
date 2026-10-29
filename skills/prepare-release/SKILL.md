---
name: prepare-release
description: 准备测试或生产发版，需要 MR、部署步骤和发版纪要时使用。
---

# 准备发版

1. 明确本次需求和测试/生产目标，复用 [prepare-commit](../prepare-commit/SKILL.md) 的检查、有效 Review 与验证证据，不重复跑未失效的审查、编译和测试；仅相同内容的暂存/提交不使 AI Review 失效，项目人工批准仍单独核对。
2. 按 [MR 规则](references/gitlab-mr.md) 准备 MR：标题和描述使用中文；若仓库要求 `feat/fix` 等类型前缀，只保留前缀，标题正文写中文变更摘要，不直接照抄英文 commit subject 或分支名。描述中的验证情况、风险与影响、回滚方式和备注也使用中文；分支、SHA、路径、命令、接口/字段名和技术专名保留原文。随后预演合并、分析冲突，关键取舍和写入先确认；冲突候选必须是独立的一次性 worktree，原 feat worktree 始终留在 feat，只在 feat 承载后续业务改动。目标基线、上下文、合并结果或冲突解决影响原结论时，调用 [review-diff](../review-diff/SKILL.md) 补受影响审查和必要验证，不用原 feat 的 pass 冒充当前合并结果通过，不以发布阶段重置复审轮数。
3. 使用 [release-checklist](../release-checklist/SKILL.md) 维护本地部署步骤和发版纪要，沿用其模板与审核流程，不另写一套规则；测试/生产分开，未执行写待执行。
4. 返回 MR 链接、材料路径、Review/验证复用与补跑结果及待确认事项，区分部署前检查和 [e2e-verify](../e2e-verify/SKILL.md) 的实际环境验收。测试尚未部署则注明部署后待验收；生产准备核对计划要求的验收证据，不把待验收当通过。创建 MR、同步飞书、合并 MR、实际部署是不同操作，各按用户明确授权执行；只要求准备，不执行远端写入。
