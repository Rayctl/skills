# Java Backend Code Quality

用于编写、修改或检查 Java 后端代码。默认只检查当前任务改动的代码，并根据代码内容读取命名、代码结构、方法设计、注释、异常和生命周期等详细规则。

## 适用范围

以下规则适用于本次变更中的 Java 生产代码和测试代码：

- 保持调用方观察到的空值、缺失、默认值、状态和异常行为不变
- 方法和变量名称应让人在使用位置看懂具体对象、动作、状态和关键副作用
- 公共方法及承载独立业务动作或处理阶段的方法具有有效 JavaDoc
- 包含多步处理或隐藏规则的方法，按阶段说明原因、前置条件、结果去向、顺序和失败后果
- 对短私有方法和仅为复用而抽出的私有常量或字段，尝试把内容直接写回使用位置，并保留更容易读懂的写法；调用次数和“减少重复”不能单独证明拆分合理
- 改变控制流的 `catch` 在行为发生前说明后续路径和保留或跳过的保证
- 用户异常提示、错误类别和真实恢复动作保持一致
- 第三方调用区分业务拒绝和技术失败，保留可定位的第三方错误信息，并按仓库约定决定日志范围
- Java 注释结尾不使用中文或英文句号，方法声明之间只保留一行空行

检查范围默认限于当前任务的暂存、未暂存和未跟踪 Java 变更，也可以指定文件、行范围、提交或对比分支。不会报告未修改的历史代码、生成代码和第三方代码，但理解当前改动时可以读取它们。

## 按需读取详细规则

`SKILL.md` 只保存每次 Java 任务都要检查的规则。详细说明分别放在下列文件中，只有遇到对应代码时才读取：

| 详细规则文件 | 什么时候读取 |
| --- | --- |
| [method-design.md](references/method-design.md) | 短私有方法、复用常量或字段、方法拆分和包装、延迟执行 |
| [structure-choice.md](references/structure-choice.md) | 编码时出现多个实现、不断增长的类型或状态分支、重复流程或分散的对象创建规则 |
| [comments-and-javadoc.md](references/comments-and-javadoc.md) | 新增或修改类、方法、JavaDoc、注释、入口校验或包含多步处理的方法体 |
| [naming.md](references/naming.md) | 名称过于宽泛、集合和状态命名、枚举查询、`normalize`、使用位置看不出职责 |
| [exception-communication.md](references/exception-communication.md) | 异常抛出或转换、用户可见文案及其常量、错误返回、失败日志、`catch` 或 `finally` |
| [remote-calls.md](references/remote-calls.md) | HTTP、Feign、RPC、外部 SDK、请求响应日志、第三方错误解析或映射 |
| [contracts-and-lifecycles.md](references/contracts-and-lifecycles.md) | 事务、跨存储、异步调用、缓存、重试、补偿、锁和资源生命周期 |
| [control-flow.md](references/control-flow.md) | 三元表达式、`if`/`else`/循环的大括号，以及较长表达式的换行 |
| [checker.md](references/checker.md) | 基线、行范围、排除路径、范围歧义、CLI 错误和规则编号 |

简单字段、协议常量或注解调整不需要读取异常和生命周期规则；用户能看到的异常文案常量属于异常处理的一部分，需要读取对应规则。代码涉及哪些情况，就要读取哪些详细规则，不能为了节省上下文而漏掉。

## 关键规则示例

### 名称在使用位置是否清楚

只看所属对象、方法名、参数和返回值的使用方式，不打开方法实现或 JavaDoc，也应能理解操作对象、结果和关键副作用：

```text
build(config, request)       -> buildOutboundRequestUrl(config, request)
saveBatch(changes)           -> saveApiConfigChanges(changes)
normalizeCodes(codes)        -> trimAndDeduplicateCodes(codes)
convert(source)              -> convertToApiUpdateBO(source)
```

`Batch`、`List`、`Data`、`Info`、`Context`、`Item` 和 `Result` 只能表达形态，不能替代业务对象。应用内部集合变量使用 `List`、`Set`、`Map` 后缀，并在名称中表达对象、状态、来源、键关系和一对一或一对多基数。索引构建必须明确重复键策略。

### 编码前判断是否需要调整结构

编码生产逻辑前，先看当前需求是否增加了新的实现方式，或者同一种类型、状态、协议和渠道判断是否已经散落在多个位置。这个步骤只是帮助选择结构，不是要求每次都使用设计模式。

- 一个只在当前方法出现的简单 `if`、单一实现或直接枚举映射，保持直接写法
- 多个位置反复按渠道选择不同处理逻辑时，可以建议把各渠道行为放到独立策略中
- 同一类对象的创建规则散落在多个调用方时，可以建议由一个工厂集中选择和创建
- 状态同时决定可执行行为和合法流转时，可以建议让不同状态负责自己的规则
- 多条流程顺序相同但部分步骤不同，或者多个处理器具有明确的执行和停止规则时，再评估组合流程、模板方法或处理链

只有当前代码已经存在变化点、调整后能减少重复修改位置，并且新增接口和类比原有分支更容易理解时，才向用户提出建议。没有明显收益时不输出结论，直接继续编码。只是沿用项目已有扩展点时也正常继续；需要新建接口、增加一组实现类或重组流程时，先说明简单方案与结构化方案的成本和收益，等待用户选择。用户拒绝后按简单方案实现，不记录质量问题。

普通单元测试、Mock 和测试数据准备不执行这项判断；共享测试工具本身出现相同变化点时才检查。纯代码审查也不执行这项建议步骤。

### 短私有方法和复用常量

短方法或复用型私有常量即使使用多次，也先尝试把方法里的代码或常量值直接写回主要使用位置，再比较哪种写法更容易读懂。直接写回后能看到空值规则、字段来源、真正调用的对象或完整异常文案，并且代码仍然紧凑时，就应保留直接写在使用位置的写法：

```java
// 使用位置看不到空值规则和实际比较的字段
if (isCatalogReference(field)) {
    validateReference(field);
}

// 类中的另一个位置
private boolean isCatalogReference(Field field) {
    return field != null
            && FieldCatalog.isReference(field.getCode(), field.getPath());
}
```

改为直接写在判断处，读者不需要跳到其他方法：

```java
if (field != null
        && FieldCatalog.isReference(field.getCode(), field.getPath())) {
    validateReference(field);
}
```

仅为了复用用户可见异常文案而抽出的私有字符串常量通常也应展开：

```java
// 常量名隐藏了需要与当前校验和错误码一起核对的真实提示
throw new BusinessException(
        ErrorCode.STATE_CONFLICT,
        FIELD_DEFINITION_MISMATCH_MESSAGE);

// 在失败分支直接展示错误类别、原因和有效恢复动作
throw new BusinessException(
        ErrorCode.STATE_CONFLICT,
        "字段定义已更新，请刷新页面后重新配置");
```

较复杂的算法、事务边界、资源生命周期、副作用顺序、补偿、需要根据上下文区分失败原因的逻辑，以及框架要求的独立方法都可以保留。协议和持久化标识、框架编译期常量、国际化 key、稳定公共标识、结构化模板及错误码枚举本身有固定含义或外部要求，也可以保留。引用次数、JavaDoc、统一文案、长常量名或方法名清晰不能单独作为保留理由。

### JavaDoc 与阶段注释

方法名说明“做什么”，JavaDoc 说明调用前提、返回结果、异常和副作用等方法名看不出的规则。即使方法逻辑是线性的、方法是私有的或名称已经清晰，只要它负责一个独立业务动作、处理阶段、生命周期时点或副作用，就需要 JavaDoc。

方法 JavaDoc、写在处理阶段开头的注释和分支内注释不能互相替代。准备或转换、远程执行、持久化和响应构造的职责、结果去向或失败处理不同时，应分别说明意图；不要求给显然的赋值、getter 或纯判断机械添加注释。

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

### 第三方调用日志和错误

接入第三方接口前，先查看仓库是否已有客户端拦截器、统一 Wrapper、日志切面、脱敏工具和错误映射。不能只因为控制台能看到 HTTP DEBUG 日志，就认为生产环境已经具有安全且完整的调用日志。

下面的处理同时丢失了第三方正常业务响应中的具体原因：

```java
if (response.isError()) {
    Loggers.BIZ.warn("carrier.order,errorCategory:{}", "BUSINESS_REJECTED");
    throw new BusinessException("承运商下单失败");
}
```

第三方业务错误至少要在调用方错误或内部诊断中的一处保留错误码、错误信息、请求 ID 等可定位内容。是否返回原始第三方文案，或者映射为本地错误，只能根据仓库已有 Wrapper 或映射表、本地接口契约、第三方明确错误码语义、调用方测试或用户确认来决定，不能根据文案相似度临时猜测。

完整 URL、请求响应体、文件和鉴权信息也不做统一禁止或统一要求。先检查仓库日志规范、脱敏和访问控制、运行环境、报文大小以及实际排障收益；规则不明确时，说明具体字段和风险，给出关键字段、脱敏完整报文、原始完整报文或仅失败记录等方案，等待用户选择。应优先建议不记录凭据和可重放信息原值，但不能把建议冒充成仓库规则。

业务拒绝、HTTP 非成功、响应无法解析和网络异常需要分别处理。技术异常包装时保留 `cause`，或由唯一负责诊断的层记录一次完整异常，避免每层都记录后再抛出。

### 三元表达式、控制流与换行

三元表达式只保留简单的纯值选择，例如：

```java
String statusText = enabled ? "启用" : "停用";
```

如果一行同时包含赋值、比较、空值判断和方法调用，拆成带大括号的 `if` 更容易看懂：

```java
String userName = null;
if (user != null) {
    userName = user.getName();
}
```

所有 `if`、`else`、`for`、`while` 和 `do while` 都使用大括号，即使分支只有一条语句。三元表达式是否影响业务理解由 Skill 结合语义判断，检查器只自动检查缺少大括号。

换行先遵循项目 formatter 或明确的最大行宽。没有项目约定时，能在当前 IDE 常见视口内完整展示且结构清楚的短调用保持一行；超过行宽、参数边界不清或一行包含多个独立动作时再换行。不要因为变量名或方法名较长就机械拆开，也不要为了避免换行而保留难以扫描的长表达式。

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
|   |-- control-flow.md
|   |-- exception-communication.md
|   |-- method-design.md
|   |-- naming.md
|   |-- remote-calls.md
|   `-- structure-choice.md
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
- `STYLE-CATCH-001`：改变行为的 `catch` 缺少说明后续处理的注释
- `STYLE-GUARD-001`：至少三个用于提前退出的入口判断前，没有说明整组校验目的的注释
- `STYLE-INTENT-001`：明显复杂的方法中，主要处理阶段前完全没有意图注释
- `STYLE-BRACE-001`：`if`、`else`、`for`、`while` 或 `do while` 的执行体缺少大括号

检查器不会判断自然语言是否清楚、处理阶段是否说明完整、三元表达式是否应该改写、私有方法或复用型异常文案常量是否应该写回使用位置、当前变化是否值得采用设计模式、错误原因是否应拆分、恢复动作是否有效、错误码是否匹配或是否泄露敏感信息。第三方调用的日志覆盖、完整报文策略、失败分类、错误映射依据和诊断信息保留也由 Skill 结合代码含义检查。

## 验证

```powershell
py -3 -m unittest discover -s "$env:USERPROFILE\.codex\skills\java-backend-code-quality\tests" -p "test_*.py" -v
py -3 "$env:USERPROFILE\.codex\skills\.system\skill-creator\scripts\quick_validate.py" "$env:USERPROFILE\.codex\skills\java-backend-code-quality"
```

在未授予 Windows 符号链接权限的环境中，越界符号链接用例会跳过。
