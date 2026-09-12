# 个人方案记录

> 本文件只是个人方案记录，不属于正式 Skill 运行内容，不应被安装为 Skill。

日期：2026-08-21

## 目标

通过 Git 仓库积累个人可复用 Skill，同时保持它们能够在 Codex 和其他 Agent 宿主之间迁移。

## 源代码和部署目录边界

- Git 仓库是 `SKILL.md`、参考资料、脚本、评估问题和历史记录的唯一来源。
- Agent 目录只是部署目标，不是规范源代码。
- 当前机器上的 Codex 用户级 Skill 目录是 `/Users/leslie/.codex/skills`。
- 其他 Agent 可能使用不同的全局目录，应通过安装器或软链接/适配层接入。
- Skill 正文保持与宿主无关。只有在确有需要时，才在宿主适配层中放置工具名称映射或启动逻辑。
- 开发阶段优先使用规范 Git 检出目录加软链接；稳定分发时可以使用固定的 tag/commit 和文件复制。

## `AGENTS.md` 和 Skill 的分工

- `AGENTS.md` 用于保存简短、稳定、始终相关的仓库或个人默认规则，例如安全、范围、验证和维护要求。
- Skill 用于保存按任务触发的可复用工作流和领域知识。
- 不要把所有个人知识都堆到一个巨大的 Skill 中。
- 如果某条规则必须每次都执行，应放到 `AGENTS.md` 或机械化 Hook 中；Skill 的触发不是强制执行边界。

## 已查看的 GitHub 项目

- [Anthropic Skills](https://github.com/anthropics/skills)：每个 Skill 独立目录、`SKILL.md`、模板、参考资料和许可证边界。
- [Vercel Agent Skills](https://github.com/vercel-labs/agent-skills)：目录化仓库、清晰的触发描述、可选参考资料/脚本和多 Agent 分发。
- [Vercel Skills CLI](https://github.com/vercel-labs/skills)：项目级/全局级作用域、Agent 指定、推荐软链接、复制模式，以及锁定、Hash 和路径安全测试。
- [Superpowers](https://github.com/obra/superpowers)：与宿主无关的 Skill 正文，加上各宿主的工具映射/启动方式、根目录维护规则、插件测试和行为评估。
- [Creed](https://github.com/gusen1453/creed)：结构紧凑、工作流关联清晰的工程方法论 Skill 集合。

## 采用的仓库实践

- 每个 Skill 使用一个稳定的小写连字符目录名。
- 保持 `SKILL.md` 简洁，把详细变体和参考资料放到 `references/`。
- 将确定性强、需要反复重写的操作放到 `scripts/`。
- 在 `evals/` 下增加正向、反向、边界和回归测试问题。
- 使用 Skill Creator 校验脚本检查 frontmatter 和命名。
- 保留旧 Git 版本；Skill 发生重要变化时不要覆盖历史。
- 不要将 Token、Cookie、原始凭据、私有 Session 数据或无关的完整工作区备份放进仓库。

## 初始 Skill

### `coding-logging-guidance`

指导日志级别、事件命名、结构化字段、关联上下文、脱敏、重复堆栈、性能和日志代码的针对性验证。

### `plan-large-feature`

面向中大型需求：收集事实、定义范围、比较设计方案、拆分模块、排列主次和执行顺序、识别依赖与验证方式，并在最后描述模块之间的关系。
