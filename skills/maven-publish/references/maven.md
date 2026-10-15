# Maven 发布与验证

按需读取，不保存仓库地址、凭据或某个业务版本的副本。

## 发布

- `package` 是本地产物，`install` 是本机缓存，`deploy` 才写远程仓库。先核对 POM 继承、版本属性、profile、发布插件及跳过配置，不能仅凭 `BUILD SUCCESS` 宣称已上传。
- 用 `distributionManagement` 的实际 snapshot/release 目标，server id 与既有 Maven settings 对应；读取依赖的 group 仓库不是上传目标。mirror、profile 和命令参数可能改变地址，须一起核对，不能只看 POM。
- `-pl ... -am deploy` 可能把父模块及其他依赖模块一起上传；执行前列明真正参与发布的模块。不默认全 reactor 发布，也不为缩小范围生成缺少依赖的空 POM。沿用项目方式；单制品 `deploy-file` 只有在已确认真实 JAR、POM、父 POM 可用及目标后才使用。
- 发布命令可能重走 Maven 生命周期；不能仅为减少重复而跳过未验证的检查。复用证据须匹配实际上传内容；源码、构建参数或产物变化时补相关验证。
- Release 已存在时，明确说明同版本重发会替换远程内容、调用方可能仍使用旧缓存；用户确认后按已有仓库策略执行，不强制递增版本。SNAPSHOT 重发也须确认。仓库拒绝重发就停止，不删除制品或改策略绕过；远程查询无权限、超时或失败不是“版本不存在”。

## 拉取与调用方

- 在独立临时目录，用 `-Dmaven.repo.local=<临时缓存>` 拉取，避免本机 `install` 或旧缓存造成假成功。远程拉取验证不清用户原缓存；保留原 settings，临时 HTTPS/mirror 配置不能扩大授权或把凭据写入仓库。
- 可用 `maven-dependency-plugin:get` 限定本次 GAV；初查 `transitive=false` 只证明单个制品可下载，不能证明传递依赖或调用方编译。插件版本按项目或已验证工具选择。
- `dependency:get` 可能访问默认 Central；需要固定来源时核对 mirror 和实际下载记录。SNAPSHOT 核对解析到的时间戳版本/摘要，不能只看 `-SNAPSHOT` 标签。
- 记录实际上传 JAR/POM 的 SHA-256，与独立缓存下载结果比对，并查看本次相关类及 POM 坐标、父 POM、依赖。不用重新打包的 JAR 代替上传对象；同版本号不代表同内容，摘要不同或无法核对时调查，不报发布验证通过。
- 调用方核对有效依赖版本、scope、实际来源及所用 JAR 摘要，再执行本次相关模块必要编译/测试。旧缓存与远程不一致时按 [prepare-commit](../../prepare-commit/SKILL.md) 的授权及精确版本缓存规则处理，重拉后核对内容并重跑相关检查；不清整个 `.m2` 或无关版本，不靠 `-U` 保证已有 Release 刷新。调用方或命令未明确就列待确认，不编造通过。
- 复用验证前核对本次相关远程依赖摘要；源码、版本号没变但远程同版本内容已变化时，补做受影响检查。缺少可核对摘要不能仅凭版本号复用。

## 参考

- [Apache Maven Deploy Plugin](https://maven.apache.org/plugins/maven-deploy-plugin/usage.html)：远程发布、server id 和真实 POM；使用原生 Maven，不另造 Nexus 客户端。
- [Maven Dependency Plugin get](https://maven.apache.org/plugins/maven-dependency-plugin/get-mojo.html)：单制品拉取、传递依赖开关及默认 Central 注意事项。
- [Plinth Maven Best Practices](https://github.com/jabrena/plinth/blob/d6bf5487fa7871dbbe3e0c02807c9a10959c7345/skills/110-java-maven-best-practices/SKILL.md)：仅借鉴按白名单提取 POM 元数据，不采用全项目治理流程或复制代码。

2026-10-15 已搜索现有 Nexus/Maven Skill；找到的通用 POM/依赖及 Maven Central 发布场景不等于私有 Nexus 发布，未发现经核实可直接采用的同场景成品。以官方 Maven 流程做最小封装。
