# YApi 两阶段流程

YApi 不是事实源。先生成当前需求范围的 OpenAPI，再选择导入或推送。

## 阶段一：生成导入文件

输出：

```text
docs/api/<feature>/yapi/openapi.json
docs/api/<feature>/yapi/import-guide.md
```

导入前运行：

```bash
scripts/validate-openapi.sh docs/api/<feature>/yapi/openapi.json
```

## 阶段二：主动推送

只有用户明确说“推送到 YApi”时才进入此阶段。YApi 实例可能使用不同的登录、项目和导入接口，不能猜测固定 URL 或认证方式。

标准 YApi Open Import 可先这样预览：

```bash
scripts/push-yapi.sh \
  --openapi docs/api/<feature>/yapi/openapi.json \
  --base-url https://yapi.example.com \
  --token-env YAPI_PROJECT_TOKEN
```

脚本默认使用 `/api/open/import_data?type=swagger_json`，如组织实例提供了不同的导入路径，必须显式传 `--endpoint`。Token 从 `--token-env` 指定的环境变量读取，不能放在命令行参数或文档中。确认实例接口、项目 Token 和导入策略后，再增加 `--execute`；脚本只报告 HTTP 状态，不打印响应体。

执行前必须明确：

- YApi 地址和项目标识
- 导入接口或组织内 CLI 的实际命令
- 新增、合并或覆盖策略
- 使用的认证方式

先输出或执行 dry-run 请求，确认后再执行远程写入。禁止输出 Cookie、Token 或密钥。
