# lesliefork

个人 Agent Skill 源代码仓库。

只有 `skills/` 目录下的内容属于运行时 Skill。`notes/` 用来保存个人方案记录，不应安装为 Skill；`evals/` 用来保存测试问题和评估标准，辅助后续改进 Skill 行为。

## 当前 Skill

| Skill | 用途 |
|---|---|
| `feature-delivery-workflow` | 按需编排功能规划、编码、日志、接口文档和 GitLab MR 阶段 |
| `coding-logging-guidance` | 指导全面、有效、可检索的应用日志代码编写 |
| `plan-large-feature` | 将中大型功能拆分为模块、优先级、任务、依赖和模块关系 |
| `api-integration-docs` | 按一次需求范围，独立生成 YApi、Postman 或飞书接口联调产物 |
| `gitlab-prepare-mr` | 主动预检 Git 冲突；无冲突直接提原 feat MR，有冲突才创建候选 MR |

## 校验

为每个 Skill 运行 Skill Creator 校验脚本：

```bash
python3 /Users/leslie/.codex/skills/.system/skill-creator/scripts/quick_validate.py \
  skills/coding-logging-guidance

python3 /Users/leslie/.codex/skills/.system/skill-creator/scripts/quick_validate.py \
  skills/plan-large-feature

python3 /Users/leslie/.codex/skills/.system/skill-creator/scripts/quick_validate.py \
  skills/api-integration-docs

python3 /Users/leslie/.codex/skills/.system/skill-creator/scripts/quick_validate.py \
  skills/gitlab-prepare-mr
```

## `api-integration-docs` 的调用边界

主动调用时只选择一个目标：`yapi`、`postman` 或 `feishu`。每次只处理当前需求相关的明确文件、模块或 Git 范围，不自动发现全项目接口，不监听文件、不接 Git Hook、不自动写入远程服务。

- YApi：先生成并校验 OpenAPI 导入文件；明确要求推送时，再用 `scripts/push-yapi.sh` dry-run，显式 `--execute` 才远程写入。
- Postman：生成 Collection v2.1 和环境变量示例；Newman 仅作为用户明确要求时的可选测试执行器。
- 飞书：先生成本地 Markdown；上传、创建或修改通过 `lark-cli`，脚本默认 dry-run，显式 `--execute` 才写入。

Git 仓库是唯一源代码。只有在确认要使用时，才将单个 Skill 安装或链接到 Agent 的全局或项目 Skill 目录。
