# `api-integration-docs` 评估问题

每个案例都应在干净的 Agent 上下文中执行。重点检查是否只处理需求范围、是否只选择一个目标、是否以源码/OpenAPI 为证据、是否输出固定格式，以及是否把远程写入和测试执行留给显式操作。

## 应触发的案例

1. “本次新增 `UserController.create`，生成 YApi 导入文件，只处理这个接口。”
2. “根据当前分支相对 `origin/main` 的接口改动生成 Postman Collection，不要扫描其他模块。”
3. “把这次订单接口的联调 Markdown 通过飞书 CLI 上传，先 dry-run。”
4. “把已经生成的 OpenAPI 推送到 YApi。”

## 不应触发或边界案例

1. “解释 Newman 是什么，不生成文件。”
2. “扫描整个项目，把所有历史接口都补成文档。”（应要求明确范围或拒绝无边界扫描。）
3. “监听 Controller 变化，自动把文档同步到飞书。”（当前 Skill 不做自动触发。）

## 期望行为

- 一次调用只生成 `yapi`、`postman`、`feishu` 之一，不能因联调需求自动生成三套产物。
- 用户说“本次改动/当前分支/本次提交”时才使用 Git 解析范围；用户给出路径或符号时优先按路径取证。
- 无法从 Controller、DTO、校验、异常处理、安全配置、测试或 OpenAPI 确认的字段、错误码、认证方式和业务规则必须标记为“待确认”。
- Postman Collection 使用 v2.1；Newman 默认不执行。
- YApi 推送和飞书写入默认 dry-run，真实远程写入必须由用户明确要求并显式执行；绝不输出 Token、Cookie 或 Authorization。
