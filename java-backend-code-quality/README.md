# Java Backend Code Quality

面向 Java 后端代码创建、修改和变更检查的 Codex Skill。它只报告当前任务范围内的问题，并根据代码特征按需加载命名、方法设计、注释、异常和生命周期细则。

## 适用范围

核心门禁适用于本次变更中的 Java 生产代码和测试代码：

- 保持调用方可见的空值、缺失、默认值、状态和异常语义
- 方法和变量名称在调用点表达具体对象、动作、状态和关键副作用
- 公共方法及承载独立业务动作或处理阶段的方法具有有效 JavaDoc
- 非平凡方法按阶段说明原因、前置条件、结果去向、顺序和失败后果
- 私有辅助方法通过内联替换测试，调用次数和 DRY 不能单独证明抽取合理
- 改变控制流的 `catch` 在行为发生前说明后续路径和保留或跳过的保证
- 用户异常提示、错误类别和真实恢复动作保持一致
- Java 注释结尾不使用中文或英文句号，方法声明之间只保留一行空行

检查范围默认限于当前任务的暂存、未暂存和未跟踪 Java 变更，也可以使用明确文件、行范围、提交或分支基线。未修改的历史代码、生成代码和第三方代码不作为报告目标，但可以作为调用关系上下文读取。

该 Skill 不替代正式的 `code-reviewer` 或提交门禁流程，也不会生成对应的批准标记。

## 渐进加载

`SKILL.md` 只保存每次 Java 任务都不能遗漏的核心门禁。细节以引用文件为权威来源，只有代码命中触发条件时才加载：

| 引用 | 触发场景 |
| --- | --- |
| [method-design.md](references/method-design.md) | 私有辅助方法、方法抽取或包装、复用、延迟执行、方法粒度 |
| [comments-and-javadoc.md](references/comments-and-javadoc.md) | 新增或修改类、方法、JavaDoc、注释、guard 或非平凡方法体 |
| [naming.md](references/naming.md) | 泛化或状态词、集合、枚举查询、重命名、`normalize`、调用点职责不清 |
| [exception-communication.md](references/exception-communication.md) | 异常抛出或转换、错误返回、失败日志、`catch` 或 `finally` |
| [contracts-and-lifecycles.md](references/contracts-and-lifecycles.md) | 事务、跨存储、远程或异步调用、缓存、重试、补偿、锁和资源生命周期 |
| [checker.md](references/checker.md) | 基线、行范围、排除路径、范围歧义、CLI 错误和规则编号 |

简单字段、常量或注解调整不需要加载异常和生命周期引用。复杂任务可以同时加载多份相关引用，不能为了节省上下文跳过已命中的契约。

## 关键规则示例

### 调用点命名

调用方不进入实现或 JavaDoc，也应能理解操作对象、结果和关键副作用：

```text
build(config, request)       -> buildOutboundRequestUrl(config, request)
saveBatch(changes)           -> saveApiConfigChanges(changes)
normalizeCodes(codes)        -> trimAndDeduplicateCodes(codes)
convert(source)              -> convertToApiUpdateBO(source)
```

`Batch`、`List`、`Data`、`Info`、`Context`、`Item` 和 `Result` 只能表达形态，不能替代业务对象。应用内部集合变量使用 `List`、`Set`、`Map` 后缀，并在名称中表达对象、状态、来源、键关系和一对一或一对多基数。索引构建必须明确重复键策略。

### 私有方法与调用点可读性

短方法即使复用多次，也先把方法体代回主要调用点比较。内联能直接展示空值规则、字段来源、真实委托对象或固定异常内容，并且仍然紧凑时，应优先内联：

```java
private boolean isCatalogReference(Field field) {
    return field != null
            && FieldCatalog.isReference(field.getCode(), field.getPath());
}
```

非平凡算法、事务边界、资源生命周期、副作用顺序、补偿、动态失败分类或框架要求的独立方法身份可以保留。引用次数、JavaDoc、统一文案或方法名清晰不能单独构成保留依据。

### JavaDoc 与阶段注释

方法名说明“做什么”，JavaDoc 说明有价值的契约。即使方法线性、私有或名称清晰，只要它拥有独立业务动作、处理阶段、生命周期时点或副作用，就需要 JavaDoc。

方法 JavaDoc、顶层阶段注释和分支注释不能互相替代。准备或转换、远程执行、持久化和响应构造具有不同职责、结果交接或失败边界时，应分别说明意图；不要求给显然的赋值、getter 或纯判断机械添加注释。

### 异常原因与恢复动作

同一提示必须对所有到达路径的失败条件都真实。不同原因具有不同错误类别或恢复动作时，不能只润色一个合并提示：

```java
// 两类失败被压成一句无法执行的提示
if (!Objects.equals(request.getDefinitionVersion(), currentDefinitionVersion)
        || field.isGroup() && field.hasValueRule()) {
    throw new BusinessException(
            ErrorCode.INVALID_ARGUMENT,
            "字段配置不正确，请刷新后重试");
}
```

应保留可以区分的失败原因：

```java
if (!Objects.equals(request.getDefinitionVersion(), currentDefinitionVersion)) {
    throw new BusinessException(
            ErrorCode.STATE_CONFLICT,
            "字段定义已更新，请刷新页面后重新配置");
}

if (field.isGroup() && field.hasValueRule()) {
    throw new BusinessException(
            ErrorCode.INVALID_ARGUMENT,
            "字段分组不可配置取值规则，请删除该规则后重新保存");
}
```

只有当刷新、重试、重新保存或重新配置确实能解决当前原因时，才能给出对应建议。无法区分原因时使用真实的组合描述，不提供只适用于部分路径的动作，并在内部保留可诊断信息。用户提示优先使用业务名称；技术标识只在目标受众能据此定位时作为辅助锚点。

## 安装

克隆仓库并进入根目录：

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

安装后的入口为：

```text
~/.codex/skills/java-backend-code-quality/SKILL.md
```

## 调用方式

`agents/openai.yaml` 已允许隐式触发。为了在编码阶段稳定加载，可以在用户级 `~/.codex/AGENTS.md` 中加入：

```markdown
## Java Backend Code Quality

Use `$java-backend-code-quality` whenever creating, modifying, or reviewing Java backend code. Apply common rules to every Java production or test source changed by the current task, and apply deeper contract and lifecycle checks only when the code contains non-trivial behavior. Ignore unrelated historical, generated, and vendored code. Explicit project and user instructions take precedence.
```

也可以显式调用：

```text
Use $java-backend-code-quality to implement or review the Java backend code currently in scope
```

## 目录结构

```text
java-backend-code-quality/
|-- README.md
|-- SKILL.md
|-- agents/
|   `-- openai.yaml
|-- references/
|   |-- checker.md
|   |-- comments-and-javadoc.md
|   |-- contracts-and-lifecycles.md
|   |-- exception-communication.md
|   |-- method-design.md
|   `-- naming.md
|-- scripts/
|   `-- check_java_backend_style.py
`-- tests/
    `-- test_check_java_backend_style.py
```

README 面向安装和快速理解，引用文件保存完整规则，Python 脚本负责可确定的自动检查。

## 样式检查器

检查当前工作区相对 `HEAD` 的暂存、未暂存和未跟踪 Java 变更：

```powershell
py -3 "$env:USERPROFILE\.codex\skills\java-backend-code-quality\scripts\check_java_backend_style.py" --changed --repo "C:\path\to\repo"
```

常用范围参数：

```powershell
py -3 "$env:USERPROFILE\.codex\skills\java-backend-code-quality\scripts\check_java_backend_style.py" --changed --base origin/main --repo "C:\path\to\repo"
py -3 "$env:USERPROFILE\.codex\skills\java-backend-code-quality\scripts\check_java_backend_style.py" --line-range "C:\path\to\Example.java:20-80"
py -3 "$env:USERPROFILE\.codex\skills\java-backend-code-quality\scripts\check_java_backend_style.py" "C:\path\to\Example.java"
```

检查器保持只读，退出码为 `0` 表示通过、`1` 表示发现违规、`2` 表示参数、输入或环境错误。规则编号包括：

- `STYLE-COMMENT-001`：注释以中文或英文句号结尾
- `STYLE-METHOD-001`：相邻方法声明之间不是一行空行
- `STYLE-CATCH-001`：改变行为的 `catch` 缺少分支内意图注释
- `STYLE-GUARD-001`：至少三个入口 guard 缺少整组意图注释
- `STYLE-INTENT-001`：明显复杂的方法完全缺少顶层阶段注释

检查器不会判断自然语言质量、阶段是否拆分完整、私有方法是否应该内联、错误原因是否应拆分、恢复动作是否有效、错误码是否匹配或是否泄露敏感信息。这些问题由 Skill 进行语义检查。

## 验证

```powershell
py -3 -m unittest discover -s "$env:USERPROFILE\.codex\skills\java-backend-code-quality\tests" -p "test_*.py" -v
py -3 "$env:USERPROFILE\.codex\skills\.system\skill-creator\scripts\quick_validate.py" "$env:USERPROFILE\.codex\skills\java-backend-code-quality"
```

在未授予 Windows 符号链接权限的环境中，越界符号链接用例会跳过。
