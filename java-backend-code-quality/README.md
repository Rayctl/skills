# Java Backend Code Quality

面向 Java 后端代码开发、修改和变更检查的 Codex skill。它在编码阶段主动约束命名、注释、异常分支和方法设计，在检查阶段只报告当前任务或明确 Git 基线内的问题

## 适用范围

通用规则适用于当前任务修改的 Java 生产代码和测试代码：

- 名称应表达具体的数据含义、动作和结果，避免含糊或生硬的抽象词汇
- 公共方法和具有调用方可见契约、生命周期或非显而易见行为的方法需要 JavaDoc
- 非平凡方法在编码前划分处理阶段，完成后逐阶段检查意图注释覆盖
- 独立数据来源比对、数据过滤或转换、执行顺序、兼容策略和隐藏特殊职责的调用点需要重点说明原因与后果
- 方法入口存在至少 3 个终止型 guard 时，整组需要一条入口意图注释；跨输入、配置、状态、安全或错误分类边界的较小校验簇也要进行语义检查
- Java 注释结尾不使用中文或英文句号，方法声明之间只保留一行空行
- `catch` 改变执行路径时，应在分支内说明失败后会发生什么以及保留或放弃的保证

当代码涉及多阶段协作、事务、补偿、缓存、跨存储、远程调用、异步、重试或资源生命周期时，skill 会加载通用的契约和生命周期附录。简单 getter、setter、直接转调、纯判断和显然的赋值不会被要求机械增加注释

检查范围默认限于当前变更集。未修改的历史代码、生成代码和第三方代码不作为报告目标，但可以作为调用关系上下文读取

## 安装

克隆仓库并进入仓库根目录：

```bash
git clone git@github.com:Rayctl/skills.git
cd skills
```

Windows PowerShell：

```powershell
Copy-Item -Recurse -Force ".\java-backend-code-quality" "$env:USERPROFILE\.codex\skills"
```

Git Bash：

```bash
cp -R ./java-backend-code-quality "$HOME/.codex/skills/"
```

安装后的入口文件应位于：

```text
~/.codex/skills/java-backend-code-quality/SKILL.md
```

## 调用方式

`agents/openai.yaml` 允许隐式触发。为了让编码阶段也稳定加载，可在用户级 `~/.codex/AGENTS.md` 中加入：

```markdown
## Java Backend Code Quality

Use `$java-backend-code-quality` whenever creating, modifying, or reviewing Java backend code. Apply common rules to every Java production or test source changed by the current task, and apply deeper contract and lifecycle checks only when the code contains non-trivial behavior. Ignore unrelated historical, generated, and vendored code. Explicit project and user instructions take precedence.
```

也可以显式调用：

```text
Use $java-backend-code-quality to implement or review the Java backend code currently in scope
```

该 skill 不替代正式的 `code-reviewer` 或提交门禁流程，也不会生成它们的批准标记

## 目录结构

```text
java-backend-code-quality/
|-- README.md
|-- SKILL.md
|-- agents/
|   `-- openai.yaml
|-- references/
|   `-- contracts-and-lifecycles.md
|-- scripts/
|   `-- check_java_backend_style.py
`-- tests/
    `-- test_check_java_backend_style.py
```

`SKILL.md` 保存 Codex 执行规则，`references/contracts-and-lifecycles.md` 只在复杂行为出现时加载。本 README 面向安装和使用，不参与 skill 执行

## 样式检查器

检查当前工作区相对 `HEAD` 的暂存、未暂存和未跟踪 Java 变更，并排除已确认的生成代码或第三方目录：

```powershell
py -3 "$env:USERPROFILE\.codex\skills\java-backend-code-quality\scripts\check_java_backend_style.py" --changed --repo "C:\path\to\repo" --exclude "target\generated-sources" --exclude "vendor"
```

指定 Git 基线：

```powershell
py -3 "$env:USERPROFILE\.codex\skills\java-backend-code-quality\scripts\check_java_backend_style.py" --changed --base origin/main --repo "C:\path\to\repo"
```

检查明确行范围或完整文件、目录：

```powershell
py -3 "$env:USERPROFILE\.codex\skills\java-backend-code-quality\scripts\check_java_backend_style.py" --line-range "C:\path\to\Example.java:20-80"
py -3 "$env:USERPROFILE\.codex\skills\java-backend-code-quality\scripts\check_java_backend_style.py" "C:\path\to\Example.java"
```

`--exclude` 可以重复使用，接受文件或目录路径。变更模式中的相对路径基于 `--repo`，完整路径模式中的相对路径基于当前目录。排除优先于包含，路径可以暂时不存在，但不支持 `*` 或 `?` glob，也不能与 `--line-range` 同时使用

检查器不会猜测哪些目录属于生成代码或第三方代码。应先根据构建配置和源码布局确认，再通过 `--exclude` 明确排除

检查器是只读工具，规则编号包括：

- `STYLE-COMMENT-001`：注释以中文或英文句号结尾
- `STYLE-METHOD-001`：相邻方法声明之间不是一行空行
- `STYLE-CATCH-001`：改变行为的 `catch` 路径缺少分支内意图注释
- `STYLE-GUARD-001`：方法入口至少有 3 个终止型 guard，但首个 guard 前缺少整组意图注释
- `STYLE-INTENT-001`：至少有 15 行有效代码和 3 个控制流节点的复杂方法完全缺少顶层阶段意图注释

JavaDoc、日志、catch 内注释和嵌套分支注释不能满足 `STYLE-INTENT-001`。自动检查只保守识别完全漏写，不判断注释内容质量、每个阶段需要几条注释，也不自动覆盖低于数量阈值但跨语义边界的校验簇

退出码为 `0` 表示通过，`1` 表示发现违规，`2` 表示参数、输入或环境错误。重试、吞异常、补偿、降级、阶段覆盖和注释意图仍需要结合源码进行人工语义检查

## 验证

运行检查器测试：

```powershell
py -3 -m unittest discover -s "$env:USERPROFILE\.codex\skills\java-backend-code-quality\tests" -p "test_*.py" -v
```

运行 skill 结构校验：

```powershell
py -3 "$env:USERPROFILE\.codex\skills\.system\skill-creator\scripts\quick_validate.py" "$env:USERPROFILE\.codex\skills\java-backend-code-quality"
```

在未授予 Windows 符号链接权限的环境中，越界符号链接用例会跳过
