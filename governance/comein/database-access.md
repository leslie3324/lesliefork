# Comein 数据库接入

职责：集中维护 Comein 数据库接入约定；各 Skill 引用本说明，不另维护副本。不保存密码或业务数据。

## 已确认方式

自动化使用已安装的官方 MySQL CLI，不依赖 DBeaver 窗口、焦点或模拟键入。DBeaver 保留给用户手动使用，不提取其保存的密码。

当前用户确认的测试连接为 `comein-test`，主机 `pc-bp18j7s6fj23flh6o.rwlb.rds.aliyuncs.com`，端口 `3306`，目标库 `comeindb`。凭据由用户通过 `mysql_config_editor` 本机交互配置，保存在 login-path 中；不写入 Skill、命令参数或仓库，不输出凭据或完整 defaults 列表。

本机专用配置为 `~/.config/mysql/comein-test.cnf`，不含凭据。用户明确允许该测试端点非 TLS 接入，配置固定 `ssl-mode=DISABLED` 和默认库 `comeindb`；仅调用该文件时生效，不写入全局 `[client]`。这个例外不适用于其他连接；其他端点先验证 TLS 或已批准安全通道，不因连接失败自动降级。

## 客户端调用

`--defaults-file` 必须是第一个参数；只读检查示例：

```bash
/opt/homebrew/opt/mysql-client@8.4/bin/mysql \
  --defaults-file="$HOME/.config/mysql/comein-test.cnf" \
  --login-path=comein-test --connect-timeout=10 --skip-reconnect --batch \
  --execute="START TRANSACTION READ ONLY; SELECT DATABASE(), VERSION(), @@autocommit; SHOW SESSION STATUS LIKE 'Ssl_cipher'; ROLLBACK;"
```

该配置与 `--login-path=comein-test` 一起使用；仅指定 login-path 不会自动加载这份文件。`--defaults-file` 隔离其他普通 option 文件，但仍读取 login-path；凭据和 TLS 设置各在一处维护，不另造 CLI。

- 每次新建本次独立连接，实际查询核对数据库及本次相关结构；不要复用用户已有交互会话。不启动本地 MySQL 服务，不安装缺失工具或自动改配置。
- SQL 用原文文件或进程 stdin 传入，核对完整语句和执行范围；禁止 `--force`，使用 `--skip-reconnect`，检查退出码、错误和查询结果。只读事务内仅运行审阅过的无副作用查询，不用它试执行写入或 DDL。
- 写入前确认自动提交、锁及数据风险和执行顺序；DML 的提交/回滚也须明确批准。一次性进程退出不能保留待提交事务供后续进程提交，不能把未提交结果报成功；分步审核须保留本次专用会话，否则先确认事务结束方案再执行。
- 错误或结果不明停止，用新连接只读核对实际状态，不整批重跑。DDL 可能隐式提交，不能承诺事务回滚；恢复也须单独确认。

## 验收状态

2026-10-15 原生客户端 8.4.11 实际连接 `comeindb`，服务端 8.0.18；专用配置加载后，无需命令行指定 TLS 模式和数据库，三个独立只读事务返回探针 301/302/303，查询及重复性通过。仅验证了元信息读取，未验证写入权限、数据库变更或事务提交。DBeaver 的只读开关不作用于 CLI，不能作为 CLI 安全边界。详细结果见 [验收记录](../../evals/mysql-change.md)。

SQL 遵循 Comein `AGENTS.md` 的 DDL 规范；正式环境本版只准备方案，不执行。执行记录和脱敏证据供发布流程引用，不自动创建或暂存一次性 SQL、数据库导出或发布文档。
