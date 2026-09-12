# 飞书 CLI 文档操作

飞书文档生成和上传是独立目标。默认只生成本地 Markdown，不自动写入飞书。

## 本地输出

```text
docs/api/<feature>/feishu/API-联调文档.md
```

## 上传 Markdown 文件

需要用户明确要求上传时，使用：

```bash
scripts/publish_feishu.sh create-markdown \
  --file docs/api/<feature>/feishu/API-联调文档.md \
  --name API-联调文档.md \
  --dry-run
```

## 创建或更新在线云文档

创建：

```bash
scripts/publish_feishu.sh create-doc \
  --file docs/api/<feature>/feishu/API-联调文档.md \
  --title "接口联调文档" \
  --dry-run
```

更新已有文档：

```bash
scripts/publish_feishu.sh update-doc \
  --doc <doc-url-or-token> \
  --file docs/api/<feature>/feishu/API-联调文档.md \
  --command overwrite \
  --dry-run
```

脚本默认 dry-run；真实写入必须显式增加 `--execute`。执行 docs 命令前遵循当前版本的 `lark-cli skills read lark-doc`、`lark-doc-create` 或 `lark-doc-update` 指导，并按 `lark-shared` 处理认证和最小权限。

不要把 Token、Cookie、Authorization、appSecret 或完整授权 URL 写入产物、日志或 Git。
