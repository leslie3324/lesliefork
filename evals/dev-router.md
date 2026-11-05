# dev-router 行为评估

评估日期：2026-11-05

## 目标

验证 `dev-router` 是否做到三件事：

1. `auto` 能识别当前阶段和下一步，但不读取或执行后续阶段 Skill。
2. `stage:<阶段>` 只连接一个阶段；`end-to-end` 只在确认门禁内推进。
3. typo、小改和单点任务不启动完整开发流程。

这是文本行为评估，不是业务系统 E2E。Eval 在临时 `HOME`、`CODEX_HOME` 和 workspace 中只读运行，不验证真实仓库实现。

## 用例

`cases-router.jsonl` 包含 5 个真实形态输入，每项重复 3 次：

- `stage:plan` 只进入 plan。
- 开发完成但 Review 和 E2E 未做时，当前阶段为 `review-diff`，下一步为 `e2e-verify`。
- Review 完成但本地 E2E 未完成时，不能提交。
- README typo 不进入完整流程。
- `end-to-end` 遇到 E2E 证据缺口时停止，不自动提交。

`read` / `avoid_read` 从实际命令执行事件和输出内容核对，不接受提示词中出现的路径；`behavior_expect` 单独检查语义阶段和门禁，避免只因为 Markdown 或措辞不同而误判行为。

## A/B 结果

同一批输入、同一模型和推理级别，比较使用 `dev-router` 与不提供任何 Skill 路径的自动发现基线：

| 指标 | 使用 `dev-router` | 自动发现基线 |
|---|---:|---:|
| 严格通过（契约 + Skill 读取） | 15/15（100%） | 0/15（0%） |
| 行为语义 | 15/15（100%） | 13/15（87%） |
| 翻转用例 | 0 | `router-auto-e2e-gate` |
| 输入 token | 319,507 | 249,827 |
| 单次平均输入 token | 21,300 | 16,655 |

严格通过不能解释为“基线完全不会规划”；基线的 15 次运行都没有提供并实际读取目标 `SKILL.md`，因此严格检查为 0。行为语义才是能力对比：基线在 `router-auto-e2e-gate` 的 3 次中有 2 次明确表示可以先提交、再补完整 E2E，只有 1 次正确拒绝；`dev-router` 3 次都要求先完成本地 E2E 再进入 `prepare-commit`。

自动发现基线未读取任何阶段 Skill；`auto` 的 9 次运行只读取 `dev-router`，没有预读 `review-diff`、`e2e-verify` 或 `prepare-commit`。`stage:plan` 读取 `dev-router`、`plan` 和 `plan` 明确引用的 `e2e-verify`；`end-to-end` 在 E2E 阶段读取 `dev-router`、`e2e-verify`，没有预读 `prepare-commit`，验证了懒加载边界。

## 局限

- 只有 5 个用例、每个 3 次，不能证明所有项目的路由准确率。
- `behavior_expect` 是确定性文本规则，不是人工或 LLM 语义评审。
- 没有在真实业务仓库中验证实现、编译、测试或部署。
- `dev-router` 增加了约 29% 的输入 token；它适合需要明确阶段和门禁的中大型需求，不应用于 typo、小改或单点操作。

## 复现

```bash
python3 evals/run_evals.py --cases evals/cases-router.jsonl --repeat 3 --reasoning low
python3 evals/run_evals.py --cases evals/cases-router.jsonl --repeat 3 --reasoning low --unassisted
```
