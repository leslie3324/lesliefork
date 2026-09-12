---
name: api-integration-docs
description: 按一次需求的明确范围生成一个指定目标的接口联调产物：YApi 导入或推送、Postman Collection，或飞书 Markdown 文档。只在用户主动调用时使用；支持按 Git 改动、明确文件或模块范围取证，不默认扫描整个项目，也不自动写入飞书。
---

# 接口联调文档生成

一次调用只选择一个目标：`yapi`、`postman` 或 `feishu`。不要因为生成一个目标而自动生成另外两个目标。

## 执行顺序

1. 解析需求范围。优先使用用户指定的文件、模块或符号；用户提到“本次改动/分支/提交”时，使用 Git 范围；没有明确范围时先询问，不扫描全项目。
2. 运行 `scripts/resolve_scope.py` 生成范围清单。Git 只用于确定本次需求的变更范围，不用于自动触发。
3. 只读取范围内的 Controller、DTO、校验注解、异常处理、安全配置、测试和已有 OpenAPI；必要时沿调用关系读取少量相关文件。
4. 按 `references/evidence-policy.md` 区分已确认、源码确认和待确认内容。没有证据的字段、错误码、认证方式和业务规则不得编造。
5. 生成用户指定的单一产物，并写入需求独立目录，例如 `docs/api/<feature>/yapi/`。
6. 执行对应校验，报告范围、证据、产物路径、未确认项和验证边界。

脚本位于本 Skill 的 `scripts/` 目录，默认从仓库根目录调用。脚本不会替 Agent 判断接口业务含义。

## 目标选择

### YApi

- `生成 YApi 导入文件`：输出 OpenAPI 3.x JSON/YAML 和导入说明。
- `推送到 YApi`：先生成并校验 OpenAPI，再用 `scripts/push-yapi.sh` 做 dry-run。只有用户明确要求并显式增加 `--execute` 时才远程写入；实例地址可配置，项目 Token 只从环境变量读取。
- 使用 `scripts/validate-openapi.sh` 校验规范。

### Postman

- 输出 Postman Collection v2.1 和环境变量模板。
- 可用 `scripts/generate-postman.sh` 从已校验的 OpenAPI 确定性生成 Collection。
- 测试断言只能依据 OpenAPI schema、源码校验规则或用户提供的业务要求生成。
- 默认只生成，不执行请求；用户明确要求时再运行 Newman。
- 生成和运行规则见 `references/postman.md`。

### 飞书

- 输出适合飞书的本地 Markdown 文件。
- 用户明确要求上传、创建或修改飞书资源时，才使用 `scripts/publish_feishu.sh` 调用 `lark-cli`；支持 Markdown 文件上传和在线云文档创建、覆盖、追加。
- 默认先执行 `--dry-run`；不自动登录、不自动上传、不监听文件变化。
- 使用 `references/feishu-cli.md`，并遵守 `lark-cli` 的认证、权限和写入确认规则。
- 飞书 Markdown 和 YApi 导入说明必须套用 `references/output-template.md` 的固定章节和字段表。

## 证据规则

优先级：已生成的运行时 OpenAPI/测试结果 > Controller、DTO、校验和安全配置 > 项目已有文档 > AI 推断。

输出中的每个接口和关键字段都要能说明来源。把无法确认的内容放入“待确认项”，不要用合理猜测替代事实。

## 输出边界

- 不修改后端源码、测试、Git 状态或远程服务，除非用户明确提出并确认了该动作。
- 不默认执行 Newman、YApi 推送或飞书写入。
- 不输出 Token、Cookie、Authorization、appSecret、YApi 密钥或飞书凭据。
- 生成完成后报告“静态取证”“OpenAPI 校验”“Postman/Newman 执行”“远程写入”之间的区别。

## 参考资料

- 范围解析：`references/scope-resolution.md`
- 证据与不确定项：`references/evidence-policy.md`
- YApi：`references/yapi.md`
- Postman/Newman：`references/postman.md`
- 飞书 CLI：`references/feishu-cli.md`
- 固定输出模板：`references/output-template.md`
