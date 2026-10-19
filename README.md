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
| `e2e-verify` | 按之前已确认标准验收本次真实业务链路，核对最终结果并保留证据 |
| `prepare-commit` | 检查改动与基线，完成必要编译和相关测试，提供可复用验证证据 |
| `prepare-release` | 复用提交前检查，准备测试/生产 MR、部署步骤和发版纪要 |
| `troubleshoot` | 按问题选择已授权日志源，通过浏览器只读查询并给出证据与判断 |
| `mysql-change` | 检查本次 SQL，确认后执行测试数据库变更并查询验证结果 |
| `apollo-config` | 用 computer use 检查配置差异，分别确认测试环境修改和发布并回读验证 |
| `maven-publish` | 核对本次模块、版本和仓库，确认后发布并独立验证远程拉取及调用方依赖 |
| `coding-logging-guidance` | 指导全面、有效、可检索的应用日志代码编写 |
| `api-integration-docs` | 按一次需求范围，独立生成 YApi、Postman 或飞书接口联调产物 |
| `release-checklist` | 本地维护测试/生产发版材料，审核后按授权只同步 ywy 飞书条目 |
| `handoff` | 将当前对话整理为下一会话可接续的交接文档 |
| `agent-reach` | 第三方互联网访问能力路由；通过同步脚本维护到各 Agent 的统一软链接 |

## `agent-reach` 同步

`skills/agent-reach` 是 Agent Reach 上游 Skill 的版本化镜像，由以下脚本从 pipx 安装目录同步 `SKILL.md` 和 `references/`，并恢复各 Agent 的软链接：

```bash
./scripts/sync-agent-reach-skill.sh
```

脚本当前维护：

- `~/.agents/skills/agent-reach`：Codex 和通用 Agent Skill 目录
- `~/.claude/skills/agent-reach`：Claude Code
- `~/.config/opencode/skills/agent-reach`：OpenCode
- `~/.openclaw/skills/agent-reach`：仅在 OpenClaw Skill 目录已存在时维护

`agent-reach install` 更新包时会把软链接替换为真实目录，因此每次更新 Agent Reach 后都要重新运行同步脚本。

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
  skills/e2e-verify

python3 /Users/leslie/.codex/skills/.system/skill-creator/scripts/quick_validate.py \
  skills/prepare-commit

python3 /Users/leslie/.codex/skills/.system/skill-creator/scripts/quick_validate.py \
  skills/prepare-release

python3 /Users/leslie/.codex/skills/.system/skill-creator/scripts/quick_validate.py \
  skills/troubleshoot

python3 /Users/leslie/.codex/skills/.system/skill-creator/scripts/quick_validate.py \
  skills/mysql-change

python3 /Users/leslie/.codex/skills/.system/skill-creator/scripts/quick_validate.py \
  skills/apollo-config

python3 /Users/leslie/.codex/skills/.system/skill-creator/scripts/quick_validate.py \
  skills/maven-publish

python3 evals/test_start_feature.py -v
```

`prepare-release` 复用 `prepare-commit` 的成功验证证据；内容、基线、范围或运行条件变化后只补受影响验证，不重复跑未失效的编译和测试。

两个发版 Skill 分工：`prepare-release` 负责验证与 MR 准备，`release-checklist` 负责本地材料、多轮审核及明确授权后的飞书同步。Comein 格式只维护在 `governance/comein/templates/release-checklist.md`，同步边界见 `governance/comein/release-minutes.md`；仅增改本需求 ywy 条目，不覆盖共享表或他人内容。独立测试文档已验证局部写入、插行、重复核对及非目标内容保护；多人共编无并发锁，同步需确认目标区域无人编辑。本周参考文档不修改。

需求工作流先创建主 feat worktree，再运行 `grill` 对齐需求；用户确认推进模式后，由 `plan` 规划实现、验收标准、E2E 和并行任务。并行开发时使用 `module-breakdown.md` 模板；完整文档按需初始化，不为所有任务默认铺设。

`e2e-verify` 只执行此前已确认的本次需求验收，不重新制定或降低标准，不强制维护长期回归测试。复用现有 API、项目测试、MySQL 和已授权浏览器能力，不依赖 tester-army/e2e；Skill 本身不提供工具或权限。真实部署未就绪就报告待验收/阻塞，发布流程引用当前部署对应的证据，不自动修复或部署。

Comein 日志来源统一维护在 `governance/comein/log-sources.md`，由 Comein `AGENTS.md` 引用；`troubleshoot` 不硬编码业务平台。需要运行环境提供 computer use 和已授权浏览器会话，Skill 本身不提供浏览器工具或访问权限。

Comein 数据库接入统一维护在 `governance/comein/database-access.md`，由 Comein `AGENTS.md` 引用；`mysql-change` 使用已配置的原生 MySQL 客户端和独立连接，不用桌面自动执行 SQL。凭据留在本机，连接专用配置不影响其他连接；正式环境本版只提供方案，Skill 本身不提供工具或数据库权限。

`apollo-config` 通过 computer use 操作已授权 Portal 会话，不要求 Open API Token，不新建 CLI/MCP。修改、发布分别确认，只执行测试写入；保存、发布与服务生效分开验证。需要登录由用户手动完成，实际页面操作权限仍须核对。

`maven-publish` 沿用项目 Maven 和已有 settings，不新建 Nexus 客户端；同版本重发需明确确认，不强制改版本或调整仓库策略。发布后用独立缓存核对远程包的实际内容，再检查调用方是否使用了新包及相关编译、测试；相关远程依赖同版本内容变化后，旧验证不能直接复用。

## `api-integration-docs` 的调用边界

主动调用时只选择一个目标：`yapi`、`postman` 或 `feishu`。每次只处理当前需求相关的明确文件、模块或 Git 范围，不自动发现全项目接口，不监听文件、不接 Git Hook、不自动写入远程服务。

- YApi：先生成并校验 OpenAPI 导入文件；明确要求推送时，再用 `scripts/push-yapi.sh` dry-run，显式 `--execute` 才远程写入。
- Postman：生成 Collection v2.1 和环境变量示例；Newman 仅作为用户明确要求时的可选测试执行器。
- 飞书：先生成本地 Markdown；上传、创建或修改通过 `lark-cli`，脚本默认 dry-run，显式 `--execute` 才写入。

Git 仓库是唯一源代码。只有在确认要使用时，才将单个 Skill 安装或链接到 Agent 的全局或项目 Skill 目录。
