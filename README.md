# lesliefork
我的ai沉淀 skill

个人 Agent Skill 源代码仓库。

只有 `skills/` 目录下的内容属于运行时 Skill。`notes/` 用来保存个人方案记录，不应安装为 Skill；`evals/` 用来保存测试问题和评估标准，辅助后续改进 Skill 行为。

根目录的 `AGENTS.md` 是我的个人通用 coding-agent 指令，通过配置的软链接供各 Agent 加载，适用于不同项目；放在这里仅作为软链接目标，不是本仓库的项目规范，也不是运行时 Skill。

## 当前 Skill

| Skill | 用途 |
|---|---|
| `start-feature` | 先从最新 pro 创建主 feat worktree，需求澄清后按确认初始化文档 |
| `grill` | 澄清目标、范围、业务规则和可验收结果；由用户选择规模、文档和并行方式 |
| `plan` | 基于已确认需求规划实现方案、验收/E2E和最大可行并行拆分 |
| `prepare-commit` | 检查改动与基线，完成必要编译和相关测试，提供可复用验证证据 |
| `prepare-release` | 复用提交前检查，准备测试/生产 MR、部署步骤和发版纪要 |
| `coding-logging-guidance` | 指导全面、有效、可检索的应用日志代码编写 |
| `api-integration-docs` | 按一次需求范围，独立生成 YApi、Postman 或飞书接口联调产物 |
| `release-checklist` | 独立维护或由 prepare-release 复用测试/生产发版材料 |
| `handoff` | 将当前对话整理为下一会话可接续的交接文档 |

## 校验

为每个 Skill 运行 Skill Creator 校验脚本：

```bash
python3 /Users/leslie/.codex/skills/.system/skill-creator/scripts/quick_validate.py \
  skills/coding-logging-guidance

python3 /Users/leslie/.codex/skills/.system/skill-creator/scripts/quick_validate.py \
  skills/api-integration-docs

python3 /Users/leslie/.codex/skills/.system/skill-creator/scripts/quick_validate.py \
  skills/start-feature

python3 /Users/leslie/.codex/skills/.system/skill-creator/scripts/quick_validate.py \
  skills/grill

python3 /Users/leslie/.codex/skills/.system/skill-creator/scripts/quick_validate.py \
  skills/plan

python3 /Users/leslie/.codex/skills/.system/skill-creator/scripts/quick_validate.py \
  skills/prepare-commit

python3 /Users/leslie/.codex/skills/.system/skill-creator/scripts/quick_validate.py \
  skills/prepare-release

python3 evals/test_start_feature.py -v
```

`prepare-release` 复用 `prepare-commit` 的成功验证证据；内容、基线、范围或运行条件变化后只补受影响验证，不重复跑未失效的编译和测试。

需求工作流先创建主 feat worktree，再运行 `grill` 对齐需求；用户确认推进模式后，由 `plan` 规划实现、验收标准、E2E 和并行任务。并行开发时使用 `module-breakdown.md` 模板；完整文档按需初始化，不为所有任务默认铺设。

## `api-integration-docs` 的调用边界

主动调用时只选择一个目标：`yapi`、`postman` 或 `feishu`。每次只处理当前需求相关的明确文件、模块或 Git 范围，不自动发现全项目接口，不监听文件、不接 Git Hook、不自动写入远程服务。

- YApi：先生成并校验 OpenAPI 导入文件；明确要求推送时，再用 `scripts/push-yapi.sh` dry-run，显式 `--execute` 才远程写入。
- Postman：生成 Collection v2.1 和环境变量示例；Newman 仅作为用户明确要求时的可选测试执行器。
- 飞书：先生成本地 Markdown；上传、创建或修改通过 `lark-cli`，脚本默认 dry-run，显式 `--execute` 才写入。

Git 仓库是唯一源代码。只有在确认要使用时，才将单个 Skill 安装或链接到 Agent 的全局或项目 Skill 目录。
