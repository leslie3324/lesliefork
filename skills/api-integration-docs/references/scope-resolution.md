# 需求范围解析

一次生成只处理一次需求，不默认读取项目全部接口。

## 范围选择

1. 用户明确给出文件、模块、Controller、DTO 或符号时，直接使用这些路径。
2. 用户说“本次需求”“当前分支改动”“本次提交”时，使用 Git 解析范围。
3. 用户只给出需求名称时，先定位可能的模块和符号，再展示候选范围；不要无边界扫描。
4. 既没有 Git 范围也没有明确路径时，先请求范围信息。

## Git 模式

先检查：

```bash
git rev-parse --show-toplevel
git status --short
```

再运行：

```bash
python3 scripts/resolve_scope.py git --base <base-ref> --head <head-ref>
```

需要当前工作区未提交改动时：

```bash
python3 scripts/resolve_scope.py git --base <base-ref> --include-working-tree
```

只把 Git 作为范围解析器，不提交、不切换分支、不清理工作区。

## 路径模式

```bash
python3 scripts/resolve_scope.py paths \
  --path src/main/java/example/UserController.java \
  --path src/main/java/example/UserDTO.java
```

输出 JSON 范围清单后，再读取相关源码。范围外的文件只有在解释调用关系确实需要时才读取，并在报告中列出。
