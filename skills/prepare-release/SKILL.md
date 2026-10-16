---
name: prepare-release
description: 准备测试或生产发版，需要 MR、部署步骤和发版纪要时使用。
---

# 准备发版

1. 明确本次需求和测试/生产目标，复用 [prepare-commit](../prepare-commit/SKILL.md) 的检查与验证证据，不重复跑未失效的编译和测试。
2. 按 [MR 规则](references/gitlab-mr.md) 预演合并、分析冲突，关键取舍和写入先确认；解决冲突后只补受影响验证。
3. 使用 [release-checklist](../release-checklist/SKILL.md) 维护本地部署步骤和发版纪要，沿用其模板与审核流程，不另写一套规则；测试/生产分开，未执行写待执行。
4. 返回 MR 链接、材料路径、验证复用/补跑结果及待确认事项。创建 MR、同步飞书、合并 MR、实际部署是不同操作，各按用户明确授权执行；只要求准备，不执行远端写入。
