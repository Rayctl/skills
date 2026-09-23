# 独立语义评测模板

这份模板用于新会话中的行为评测。它与 `semantic-cases.json` 的结构校验不同，评测者需要真实加载 Skill、最小 fixture 和用户提示，然后记录决策是否符合预期。

## 单个场景

```yaml
id: guidance-baseline-by-section
mode: implementation
prompt: 修改日志字段，并先判断项目提示是否仍然有效
input_files:
  - fixtures/project-guidance.md
expected_decisions:
  - 只核实 Logging 章节
  - 不推进其他章节的 verified_commits
assertions:
  - 输出明确说明读取了哪些证据
  - 输出没有把项目提示当成正式项目规则
disallowed_decisions:
  - 刷新全部章节的提交号
```

## 运行与记录

每个场景至少执行一次 Skill 版本和一次无 Skill或旧版本基线。每次执行使用独立上下文，保存：

- `output.md`：完整回答或审查结果
- `grading.json`：每条断言的 `passed`、证据摘录和失败原因
- `timing.json`：`total_tokens`、`duration_ms`、实际读取的引用文件
- `feedback.md`：人工指出的遗漏、误报和下一轮修正方向

断言只写可观察结果，例如是否暂停询问、是否保留错误原因、是否只加载相关章节。不要用固定措辞作为唯一通过条件。结构校验通过不代表模型行为通过，最终结论必须基于输出证据和人工复核。
