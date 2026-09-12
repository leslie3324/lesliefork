# Postman 和 Newman

## 生成

从当前需求范围的 OpenAPI 生成 Postman Collection v2.1：

```text
docs/api/<feature>/postman/collection.json
docs/api/<feature>/postman/environment.example.json
```

本 Skill 自带确定性转换脚本：

```bash
scripts/generate-postman.sh \
  docs/api/<feature>/yapi/openapi.json \
  docs/api/<feature>/postman/collection.json \
  docs/api/<feature>/postman/environment.example.json
```

优先使用已安装的 `openapi-to-postmanv2` 或组织内转换工具；没有工具时由 Agent 根据已校验的 OpenAPI 生成，并在报告中标记转换方式。

Collection 中可以包含：

- 状态码断言
- OpenAPI schema 对应的字段断言
- 请求间变量传递模板
- 不包含真实 Token 的环境变量

不要根据猜测添加业务断言。

## Newman

Newman 是 Postman Collection 的命令行运行器，不是文档生成器。只有用户明确要求执行测试时才运行：

```bash
npx newman run docs/api/<feature>/postman/collection.json \
  -e docs/api/<feature>/postman/environment.json
```

如果本机没有 Newman 或环境变量不完整，只报告“Collection 已生成，未执行测试”，不要擅自安装依赖或发起真实请求。
