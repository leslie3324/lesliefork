# Apollo 接入与状态

仅在接入或核对配置状态时读取。本说明不保存环境地址、凭据或配置副本；目标及接入方式以仓库规则、用户指定和实际页面为准。

## 接入

- MVP 只用 computer use 操作用户已授权的 Apollo Portal，不要求 Open API Token，不新建 CLI 或 MCP。需要登录时由用户手动完成；工具不可用或页面权限不足就停止，不换 API 绕过。
- 每次点击、输入后读取最新页面状态，再定位下一步；不复用旧元素编号或固定坐标。页面状态只输出必要控件和脱敏摘要，不整页输出配置值。不能确认按钮作用或保存范围时暂停，不误点发布、删除或批量同步。
- 沿用用户已有页面权限，不创建 Token、提取 Cookie、调用内部接口或申请扩大权限。
- ConfigService 是应用读取配置的服务，不是管理配置的 Portal；不能用项目 JVM 的 `apollo.configService` 地址推断 Portal 地址。
- 不默认 `default`、`application` 或某个环境标签代表目标；从当前页面或已确认接入信息核对 AppId、环境、Cluster、完整 Namespace 名。

## 状态核对

| 状态 | 查看对象 | 结论边界 |
|---|---|---|
| 编辑态 | Portal 当前配置及待发布差异 | 保存成功仍可能未发布 |
| 发布态 | Portal 发布历史中的最新有效发布和配置 | 确认 Release 和本次配置，不代表每个实例已消费 |
| 服务生效 | 已批准的相关接口、日志或运行态证据 | 按实际代码核对热更新或重启需求，不自动重启 |

发布对象是整个 Namespace 的当前编辑内容，不是单个 key；发布前必须查看全部待发布差异，只返回必要脱敏摘要。遇到无关改动、公共 Namespace 或灰度分支，先确认影响，不自行选择发布范围或绕过锁。

YAML/JSON 等文件型 Namespace 核对格式和完整名称，基于编辑器的最新完整内容做最小修改，不能用局部片段覆盖整个文件。

## 参考

- [Apollo 官方文档](https://www.apolloconfig.com/)：参考配置编辑、发布及历史状态语义；当前操作以实际 Portal 页面为准。
- [ApolloConfig 配置 Skill](https://github.com/ysjiang4869/public-llm-skills/blob/01898cfcf845d82a137d1ef111532454fa0d8c47/apollo-config/SKILL.md)：借鉴编辑/发布分离、预览确认、回读验证；不采用其公网 HTTP 接入规则或脚本。
- [apl-cli Skill](https://github.com/aruni-01/apl-cli/blob/c206da9a7d129cde796d309d057c4191a98d30ce/skills/apl-cli/SKILL.md)：借鉴限定 key 和正式只读；不安装 CLI，不采用凭据落文件或命令参数的方式。

2026-10-15 已阅读上述上游及 Apollo 发布实现；这里只借鉴流程，不复制代码。上游存在不等于已验证其适用于 Comein。
