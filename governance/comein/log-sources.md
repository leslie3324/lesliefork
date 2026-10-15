# Comein 日志入口

职责：集中维护 Comein 日志来源、环境和接入约定；各 Skill 引用本说明，不另维护副本。不存放凭据或业务日志。

## 已确认来源

以下环境和服务映射由用户于 2026-10-14 确认，不代表访问权限或查询链路已验证。

| 来源 | 环境 | 用途 | 入口 |
|---|---|---|---|
| 测试应用日志 | 测试 | 对应服务的应用日志 | [测试日志](http://log-test.io.comein.cn/) |
| 正式应用日志 | 正式 | 对应服务的应用日志 | [正式日志](http://log.io.comein.cn/) |
| SLS `apig-access-log` | 正式 | 网关访问日志 | [SLS 网关日志](https://sls.console.aliyun.com/lognext/project/aliyun-product-data-1920682787925292-cn-hangzhou/logsearch/apig-access-log?slsRegion=cn-hangzhou) |
| SLS `sandbox` | 正式 | OpenCode 日志 | [SLS OpenCode 日志](https://sls.console.aliyun.com/lognext/project/k8s-log-ce7a7bcfa2db44fe4a84ce237b118dbe7/logsearch/sandbox?hideTopbar=true) |

`apig-access-log` 的地域为 `cn-hangzhou`；`sandbox` 的地域待确认，以控制台实际项目为准。服务名和可检索字段从当前页面核对，不猜测或在这里维护第二份字段清单。

## 浏览器接入

- MVP 使用 computer use 和用户已授权的浏览器会话，不依赖新 CLI、插件或 MCP；工具不可用、需要登录或权限不足时暂停，由用户处理。
- HTTP 地址仅为已知入口，不直接用已登录会话访问未验证的 HTTP 页面；先确认 HTTPS 入口或用户批准的安全通道。不读取、提取或传递浏览器凭据。
- 查询前核对项目、Logstore、环境和服务，只查看本次问题范围内的结果；不因测试日志不足而自动查询两个正式 SLS。
- 仅调整临时查询、检索和展开结果；不点击保存、发布、配置修改、授权或探针创建。截图和日志输出遵循 `troubleshoot` 的脱敏限制。
