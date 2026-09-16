# 语义评测

`semantic-cases.json` 保存 Java 后端质量规则的代表性决策场景。它用于检查 Agent 是否做出了正确判断，不要求固定措辞，也不替代真实项目中的源码、契约和测试。

每个用例包含：

- `fixture`：提供给 Agent 的最小代码或任务背景
- `expected_decisions`：回答中必须体现的判断
- `disallowed_decisions`：不能出现的错误判断
- `triggers`：该场景应加载的详细规则

建议使用没有继承原讨论结论的新会话或独立评测者，将 Skill、单个 fixture 和“只给出审查或实现决策”的任务交给它。评测者按含义判断是否覆盖所有期望决策，而不是比较原句。发现失败后先修正规则，再重新运行全部受影响用例。

下面的命令只校验评测文件结构，不运行模型，也不能证明语义行为正确：

```powershell
py -3 scripts/validate_semantic_evals.py evals/semantic-cases.json
```
