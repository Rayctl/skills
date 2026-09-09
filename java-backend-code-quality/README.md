# Java Backend Code Quality

面向 Java 后端代码开发、修改和变更检查的 Codex skill。它在编码阶段主动约束命名、注释、异常分支和方法设计，在检查阶段只报告当前任务或明确 Git 基线内的问题

## 适用范围

通用规则适用于当前任务修改的 Java 生产代码和测试代码：

- 方法名应在调用点表达具体对象、动作和结果，通用动词不能只搭配批量、列表、数据等泛化词
- 业务代码不使用 `normalize`、`normalized` 或 `normalizer` 隐藏实际转换规则，必须写出具体动作或结果
- 应用内部集合变量使用 `List`、`Set`、`Map` 后缀；业务对象、状态、来源和 Map 键关系写在后缀前，并显式处理重复键策略
- 所有公共方法，以及承载独立业务动作或处理阶段的自定义方法都需要 JavaDoc，不因方法私有、实现线性或名称清晰而豁免
- 非平凡方法在编码前划分处理阶段，完成后逐阶段检查意图注释覆盖
- 独立数据来源比对、数据过滤或转换、执行顺序、兼容策略和隐藏特殊职责的调用点需要重点说明原因与后果
- 连续调用如果切换了处理器职责、交接中间结果，或具有不同的执行顺序、失败后果和副作用边界，必须按阶段分别添加调用点意图注释；即使接收者相同，也不能用一条注释覆盖准备、执行、持久化或响应阶段
- 当前变更中的私有辅助方法都需要与内联形式比较；一两个调用点、复用或“稳定规则”标签都不能单独证明抽取合理
- 方法入口存在至少 3 个终止型 guard 时，整组需要一条入口意图注释；跨输入、配置、状态、安全或错误分类边界的较小校验簇也要进行语义检查
- Java 注释结尾不使用中文或英文句号，方法声明之间只保留一行空行
- `catch` 改变执行路径时，应在分支内说明失败后会发生什么以及保留或放弃的保证

当代码涉及多阶段协作、事务、补偿、缓存、跨存储、远程调用、异步、重试或资源生命周期时，skill 会加载通用的契约和生命周期附录。简单 getter、setter、无独立语义的私有转调和固定异常构造可以豁免方法 JavaDoc；线性的独立动作方法仍需 JavaDoc，但方法体不会因此被机械增加阶段注释

检查范围默认限于当前变更集。未修改的历史代码、生成代码和第三方代码不作为报告目标，但可以作为调用关系上下文读取

## 方法拆分与内联

对当前变更新增或修改的私有辅助方法，都先把方法体代回调用点比较两种写法。引用次数只是判断输入，不能用“已经复用”直接结束检查

满足以下任一职责，并且抽取后确实让调用点更容易理解时，可以保留：

- 隔离非平凡分支、循环或算法细节
- 独立负责非平凡的事务控制、资源获取与释放、副作用顺序、补偿或失败策略
- 方法签名由框架回调、注解、反射或序列化契约要求

只有一两个显式源码调用点时，以下私有辅助方法必须就地展开，即使因此重复两次；只有方法本身实际承载非平凡机制或其独立身份由框架契约要求时才能例外保留：

- 只有一个 guard，并在分支内执行简单赋值或直接调用
- 只转发参数或包装另一个方法调用
- 只包装一次远程调用或持久化调用，且没有事务、顺序、补偿或失败策略
- 只包含少量线性赋值、对象组装或局部转换
- 只增加常规空值判断或构造固定异常，没有独立策略
- 参数主要来自调用方局部变量，抽取后只是把局部上下文搬进形参
- 读者必须跳转后才能理解主流程的基本行为
- 抽取目的只是缩短方法、降低表面行数或用方法名代替必要的阶段注释

复用同一规则两次或给方法加上“稳定策略”“处理阶段”等名称，不能覆盖上述内联要求。内联后优先使用准确的局部变量和阶段意图注释保持主流程层次。保留的方法仍须满足调用点命名约束，不能靠 JavaDoc 或方法体解释一个含糊名称。检查引用前先排除框架、注解、反射和序列化等隐式调用，禁止仅凭文本搜索结果删除方法

无价值抽取如果隐藏了执行顺序、副作用、异常策略或生命周期责任，按 `P2` 报告；如果只增加局部跳转和阅读成本，按 `P3` 报告

## 方法 JavaDoc

所有公共方法，以及承载独立业务动作或处理阶段的自定义方法，都需要方法级 JavaDoc。是否必须编写不取决于可见性、代码行数、控制流数量、实现是否线性或方法名是否清晰；名称说明“做什么”，JavaDoc 还应说明有价值的执行时点、输入输出、状态或副作用、失败行为和结果用途

例如，记录完成全部处理后的最终请求载荷属于独立生命周期阶段，即使方法只有几行线性代码，也应说明“最终”对应的时点、记录结果供谁使用，以及是否只保存快照而不再修改请求。JavaDoc 不应只把方法名翻译成一句话，也不能代替复杂方法体所需的阶段意图注释

只有不拥有独立动作或契约的私有辅助方法可以豁免，例如自解释的 getter/setter、纯参数转调和固定异常构造；生成方法、第三方签名以及继承契约已经完整且没有新增语义的覆写方法也可以豁免。缺失说明会隐藏生命周期、状态、副作用、失败策略或其他契约时按 `P2` 报告，仅缺少一个清晰独立动作的方法说明时按 `P3` 报告

## 方法命名

方法名需要结合接收者、参数角色和返回值去向进行判断。调用方不查看实现或 JavaDoc，也应能理解操作对象、主要结果以及持久化、远程调用、事务、补偿或降级等关键副作用

`build`、`create`、`convert`、`map`、`query`、`validate`、`save`、`update`、`process`、`handle` 等通用动词默认需要补充具体产物、对象、规则或结果。`Batch`、`List`、`Data`、`Info`、`Context`、`Item` 和 `Result` 只能描述形态，不能单独充当业务对象

自定义方法、类型、字段和变量不使用 `normalize`、`normalized` 或 `normalizer` 表示含糊的“规范化”。应直接说明填充默认值、大小写转换、去重、过滤、排序或格式转换等真实动作和结果，也不能只换成 `standardize`、`canonicalize`、`sanitize`、`adjust` 或 `process`。框架或第三方签名以及 Unicode NFC、URI normalization 等正式标准契约可以保留原术语

典型调整包括：

```text
OutboundRequestUrlBuilder#build(config, request) -> buildOutboundRequestUrl
saveBatch                                      -> saveApiConfigChanges
normalizeSystemContext                         -> 按实际动作命名，例如 fillMissingSystemIdentity
convert                                        -> convertToApiUpdateBO
map                                            -> mapToResponse
```

自定义转换方法使用 Java 常见的 `convertToXxx` 或 `mapToXxx`，目标形态必须明确，不使用数字 `2` 表示方向。布尔判断优先使用 `is`、`has`、`can`、`should`，抛异常的校验方法应写明被校验的对象或契约

字段、参数和局部变量也要让数据、状态、来源、作用域或使用方可辨识，不能只依赖宽泛类型或 `data`、`context` 等泛化载体名称。方法 JavaDoc 说明输入、输出、异常和生命周期契约，不能替代方法体的阶段意图注释

`candidate` 只用于后续还要经过明确规则选出最终结果的数据，并写明候选对象或范围；查询已经得到有效结果、普通循环元素或条件构造器不应使用 `candidate(s)`。应用内部的集合变量使用容器后缀，例如 `requestedAppList`、`requestedAppCodeSet`、`appByCodeMap` 和 `appsByStatusMap`；业务语义必须写在后缀前，`dataList`、`itemSet`、`appMap` 仍然不合格。序列化字段、公共 API 或框架签名不能为了后缀破坏兼容性

同一查询结果随后按同一稳定业务键查找两次及以上，并且业务契约是一键一值时，优先一次构建 Map，而不是重复扫描 List 或抽取平凡查找方法。只有一次查找、需要保序、允许重复或本来就只遍历一次时继续保留集合。Map 一对一索引使用单数值名，例如 `activeSchemaByCodeMap`；一对多分组使用复数值名，例如 `schemasByCodeMap`。构建索引时还要确认重复键是被约束、拒绝、分组，还是按稳定规则选择，不能让普通索引名称隐藏任意的首条或末条优先；规则不强制使用 Stream

### 调用边界与阶段注释

同一方法内的连续调用要按真实职责划分阶段，而不是按接收者是否相同划分。以下情况应在每个阶段的首个调用或结果赋值前分别写意图注释：

- 从校验、准备或映射切换到远程调用、持久化、发布或响应构造
- 前一个调用的结果成为后一个调用的输入
- 两个调用由不同处理器负责，或拥有不同的顺序约束、失败后果、补偿范围或副作用

注释说明本阶段为什么执行、依赖什么前置条件、结果交给谁，以及为什么必须在当前顺序执行。一个注释只能覆盖目的、前置条件、结果消费者和失败语义都一致的紧凑调用组；共享一个 `executor`、`service` 或其他接收者不能作为合并注释的理由。准备下游请求和执行下游调用即使由同一个处理器对象提供，也应分别说明

### 枚举查询命名

新增枚举查询方法前，先检查当前仓库和相邻枚举的既有约定。方法名需要同时表达返回内容和查询字段，不能只写裸 `find`、`get` 或 `of`

```text
SignerTypeEnum#find(code)       -> getByCode
OrderTypeEnum#getDescByCode     -> 保留，返回内容和查询字段均明确
find(code)                      -> findByCode，仅当仓库使用 find 表达可缺失查询
```

返回枚举本身时可以遵循仓库已有的 `getByCode`，返回枚举属性时使用 `getDescByCode`、`getNameByCode` 等“返回内容 + By + 查询字段”结构。多个字段共同定位时应在名称中表达关键字段，或使用仓库中已有且调用点可理解的身份概念

查不到时返回 `null`、返回 `Optional` 或抛出异常，均以当前仓库契约为准，并通过返回类型、空值注解、JavaDoc 或异常契约明确。Skill 不会为了统一命名而机械改变缺失语义。`valueOf` 默认保留给 Java 按枚举常量名解析，业务编码查询应使用 `ByCode` 或同等明确的本地约定

以下约定方法可以保留简短名称：

- 接口覆写和框架强制回调，例如 `run`、`handle`、`execute`
- 专用单一产物、调用前已累积状态且不接收业务入参的标准 `Builder#build()`
- `Repository`、`Mapper`、`DAO` 上执行常规单库存储的 `create`、`save`、`update`、`delete`
- Java、JDK 和第三方约定的 `toString`、`toBuilder`、`toInstant`

带业务参数并执行完整流程的 `XxxBuilder#build(...)` 不属于标准 Builder 豁免。持久层方法如果还协调跨库写入、补偿或特殊生命周期，也必须在名称中暴露该职责

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
|   |-- naming.md
|   |-- checker.md
|   `-- contracts-and-lifecycles.md
|-- scripts/
|   `-- check_java_backend_style.py
`-- tests/
    `-- test_check_java_backend_style.py
```

`SKILL.md` 保存常驻的核心执行规则。只有出现泛化命名、枚举查询、重命名或调用点职责不清时才加载命名细则；事务、缓存、远程调用、补偿、并发、异步或资源所有权等复杂行为才加载生命周期附录；默认工作区和明确路径检查直接运行脚本，使用基线、行范围、排除项、处理范围歧义或排查 CLI 问题时才加载检查器说明。本 README 面向安装和使用，不参与 skill 执行

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

JavaDoc、日志、catch 内注释和嵌套分支注释不能满足 `STYLE-INTENT-001`。自动检查只保守识别完全漏写，不判断注释内容质量、独立动作方法是否缺少 JavaDoc、每个阶段需要几条注释、相邻调用是否属于不同阶段，也不会判断一两个调用点的私有辅助方法是否应该内联

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
