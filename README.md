# Skills

个人维护的 Codex skills 仓库。每个 skill 使用独立目录，并在目录内提供面向使用者的 README 和面向 Codex 的 `SKILL.md`。Skill 入口保持精简，详细规则按任务触发后从 `references/` 渐进读取

## Skills

| Skill | 用途 |
| --- | --- |
| [git-latest-code-check](git-latest-code-check/README.md) | 检查代码基线；对干净且确认落后的分支尝试一次安全快进，推送前核对指定的已有远端分支 |
| [java-backend-code-quality](java-backend-code-quality/README.md) | 在 Java 后端编码、修改和变更检查阶段应用契约、命名、注释、异常及复杂逻辑质量规则 |

## 推荐流程

对 Git 仓库中的代码任务，先由 `$git-latest-code-check` 确认本地代码基线和远端新鲜度，再按语言加载对应质量 Skill。检查本身只读；工作区干净且结果确认为 `BEHIND` 时，先告知用户，再按 Skill 已授权的策略尝试一次安全快进。无法确定提交关系时，先请求授权；工作区有修改时禁止更新，只按 Skill 的范围规则继续已有相关工作。缺少或删除远端目标、未完成 Git 操作及本地 Git 错误会停止开发。实际推送前还要独立核对指定的已有目标分支。

Java 任务使用 `$java-backend-code-quality`。它默认只检查当前任务涉及的 Java 生产代码和测试代码：复杂行为按需加载事务、异常、远程调用和生命周期规则，简单任务不会扫描无关历史代码。

## 项目提示

Java Skill 可选读取仓库本地的 `.codex/project-guidance.md`。该文件通过 Git 本地排除保存，只记录日志入口、工具库、远程包装方式和验证命令等稳定提示，不记录类清单、调用关系、字段含义或依赖版本。它只是参考信息，当前源码、构建配置、测试、正式文档和用户要求优先。项目提示按章节核实，不能把一次局部核实当成整个文件已更新。

## Java 质量规则

Java Skill 将规则分为两层：

- 质量门禁：调用方可理解的职责、数据和状态语义、异常分类与恢复动作、事务和资源生命周期、第三方诊断信息、关键阶段意图和最终状态验证
- 默认偏好：注释标点、方法间空行、控制语句大括号、集合变量后缀、三元表达式和换行方式

默认偏好服从项目 formatter、`AGENTS.md`、正式文档和用户明确要求，单纯偏好问题最高按 `P3` 处理

## 评测与验证

`java-backend-code-quality/evals/semantic-cases.json` 保存需要语义判断的代表性场景，`forward-evaluation-template.md` 用于在独立会话中记录有 Skill、无 Skill或旧版本的输出、断言证据、Token、耗时和实际加载的引用。JSON 结构通过不代表模型行为已经通过，仍需独立会话或人工评测

两份 Skill 都可以分别运行 `quick_validate.py` 和各自测试。Java Skill 还提供只读检查器，用于检查当前任务 Java 变更的确定性格式问题

## 安装

```bash
git clone git@github.com:Rayctl/skills.git
```

进入目标 skill 目录的 README，按其中说明安装到 `~/.codex/skills`
