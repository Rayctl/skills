# Git Latest Code Check

在规划或修改代码前，只读检查开发目标是否有效、本地是否包含远端最新提交；每次实际推送前独立复核实际推送目标。目标分支必须已存在，不自动创建或恢复分支。干净工作区确认落后时自动尝试一次安全快进更新。

## 工作方式

开发前对每个任务、仓库、分支和目标检查一次，推送前复核则每次执行：

```text
任务开始
  -> 仅在代码规划、修改或实际推送任务中检查是否有关联仓库或明确路径
  -> 没有候选目录：静默跳过，不运行 Git 命令或加载 Skill
  -> 仅从当前工作目录或用户明确给出的路径确定候选目录
  -> git rev-parse 预检
  -> 非 Git：静默跳过，不加载 Skill
  -> 已确认 Git worktree：调用 Skill
  -> 无论工作区是否有改动，都只读检查远端
  -> 干净 + CURRENT / AHEAD：继续规划或编码
  -> 干净 + BEHIND：先提示将执行一次安全快进，再自动更新
  -> 干净 + 远端不同或无法确认：停止并提示
  -> 脏 + CURRENT / AHEAD：提示脏状态，继续相关工作
  -> 无论干净或脏，分支缺失、无目标、Git 操作未完成、detached 或本地 Git 错误：停止
  -> 脏 + 提交新鲜度差异或暂时远端访问失败：警告，仅继续已有相关工作
  -> 脏 + 本次任务与已有改动无关：停止，要求使用干净工作区
  -> 仅干净 + BEHIND 可自动尝试一次更新
  -> 可快进：更新后刷新完整 local 基线，重新读取代码
  -> 每次实际推送前：verify-push 并报告，失败时停止推送
```

“最新”表示本地 `HEAD` 等于远端 tip，或者本地历史已包含远端 tip。`AHEAD` 必须同时报告本地与远端提交及额外提交，并检查提交是否属于当前任务；工作区干净不代表提交归属正确。脏工作区不会跳过远端观察，仅提交新鲜度差异和暂时访问失败可降为警告，开发目标失效不能豁免。

upstream 配置仍存在时，即使本地 tracking ref 已被 prune，也查询配置指向的远端分支，并保留自定义 fetch refspec 的目标映射。用户指定开发目标与 upstream 不一致时，先报告两者并询问选择；会话已确认的选择无需重复询问。CLI 将显式参数视为调用方已确认的选择，不自动修改 upstream。

## 基线交接

`CURRENT`、`AHEAD` 或 `UPDATED` 成功结果中的完整 `local` 是观察到的本地基线，携带 `remoteFreshness: confirmed`。更新成功后用新的完整 `local` 替换旧基线。下游语言或质量 Skill 可复用，无需重复访问远端。允许继续的脏工作区新鲜度警告携带 `remoteFreshness: unconfirmed`，可用于已有相关工作，但不能刷新 Java `.codex/project-guidance.md` 等元数据基线。阻断状态不能作为继续工作的授权；推送复核不替代开发基线。

基线交接只复用已经观察到的提交号，不提高下游提示的权威级别，也不保证任务期间工作区或远端不变。仓库、分支或开发目标改变、用户要求或更新成功时重新检查；每次实际推送前独立复核。

## 对话可见反馈

脚本会将状态和字段写入标准输出，但工具输出不代表已经通知用户。因此，每次执行 `check`、`update` 或 `verify-push` 后，Codex 必须先在对话中主动报告，再继续工作或停止：

- `CURRENT`、`AHEAD`、`UPDATED`：简洁说明仓库、当前分支、目标、状态和短提交号；`AHEAD` 同时报告本地和远端提交、额外提交及其归属；工作区为脏时额外提醒
- 脏工作区的提交新鲜度差异或暂时远端访问失败：说明状态、可获得的仓库与提交信息、脏状态和原因，并明确远端新鲜度未确认、只允许继续已有改动相关的工作、禁止执行 `update`
- 其他状态或命令异常：说明状态（没有状态时使用 `ERROR`）、可获得的目标与提交信息、脏状态（不可获得时说明未知）、原因、下一步及所需用户选择；分支缺失明确停止并询问正确的已有目标
- 每次更新前报告真实观察状态、仓库/分支/目标、提交号、干净前提及单次安全更新动作。不能把 `REMOTE_DIFFERS` 宣称为 `BEHIND`
- 更新失败可能发生在 HEAD 已快进后，报告最新已知本地提交，不得未经验证声称本地未变。更新失败后停止，不重试

不能把隐藏的命令或工具输出视为已经通知用户

## 安装

将整个目录复制到 Codex 用户 Skill 目录：

```powershell
Copy-Item -Recurse -Force ".\git-latest-code-check" "$env:USERPROFILE\.codex\skills"
```

在用户级 `~/.codex/AGENTS.md` 中加入：

```markdown
## Git Latest Code Check

Apply this section when the user requests substantive code planning, creation, modification, or an actual push. If the conversation has no associated repository and the user did not explicitly provide a repository path, stop applying this section without running Git commands and do not load, invoke, or mention `$git-latest-code-check`.

Otherwise, identify a candidate directory only from the current working directory or the explicitly provided repository path. Confirm it with `git -C "<candidate>" rev-parse --is-inside-work-tree`. Do not search unrelated directories for a repository. If the command fails or does not return `true`, do not load, invoke, or mention the skill.

If the command succeeds, explicitly read and follow `~/.codex/skills/git-latest-code-check/SKILL.md` as `$git-latest-code-check` once before relying on or modifying code in that Git worktree. Do not rely on implicit skill discovery for this step. Apply the Skill's clean-versus-dirty worktree policy to decide whether a remote mismatch stops the task or becomes a warning. Apply language- or task-specific skills only after the check passes or the Skill explicitly permits related existing work to continue with a dirty-worktree warning. Explicit user and repository instructions take precedence.

Missing or unknown remote targets, unfinished Git operations, detached HEAD, and local Git errors always stop development, even when dirty. If an explicit development target differs from upstream, report both and ask for a choice unless already confirmed. Preserve the selected target without changing upstream. Before every actual push, run the Skill's read-only `verify-push` with the actual remote and destination branch, then visibly report the result. Only `CURRENT` or `AHEAD` permits an already-authorized push; dirty state never downgrades a push verification failure. Require a single existing destination, preserve repository PR rules, and never automatically create or restore a deleted remote branch.
```

`agents/openai.yaml` 已关闭隐式调用。日常 Git 仓库任务由上面的全局规则在预检通过后从用户 Skill 目录显式读取，也可以在对话中显式输入 `$git-latest-code-check`

## 命令

使用当前分支配置的 upstream：

```powershell
py -3 "$env:USERPROFILE\.codex\skills\git-latest-code-check\scripts\git_latest_code.py" check --repo "D:\path\to\repo"
```

用户明确选择已有目标后（没有 upstream 时必须明确选择）：

```powershell
py -3 "$env:USERPROFILE\.codex\skills\git-latest-code-check\scripts\git_latest_code.py" check --repo "D:\path\to\repo" --remote origin --branch main
```

发现 `BEHIND` 且工作区干净后，先在对话中说明仓库、分支、目标和本地/远端短提交号，再执行一次安全更新：

```powershell
py -3 "$env:USERPROFILE\.codex\skills\git-latest-code-check\scripts\git_latest_code.py" update --repo "D:\path\to\repo"
```

`--remote` 和 `--branch` 必须同时提供，不修改 upstream。检查用了显式参数，更新必须传递相同参数。`REMOTE_DIFFERS` 需要针对当前仓库和目标的单次更新授权，不能自动更新。远端对象不在本地时只读检查不能判为 `BEHIND`。

## 状态与退出码

`check` 的状态必须与 `dirty` 字段一起解释：

| 状态 | 含义 | `dirty: false` | `dirty: true` |
| --- | --- | --- | --- |
| `CURRENT` | 本地与远端提交一致 | 继续 | 提示脏状态，继续相关工作 |
| `AHEAD` | 本地已包含远端最新提交并有额外提交 | 继续 | 提示脏状态，继续相关工作 |
| `REMOTE_DIFFERS` | 远端提交与本地不同，但只读检查无法安全分类 | 停止并请求更新授权 | 警告，继续已有改动相关工作 |
| `BEHIND` | 本地单纯落后 | 先报告动作，再自动尝试一次安全快进 | 警告，继续已有改动相关工作 |
| `DIVERGED` | 本地与远端已经分叉 | 停止并由用户处理 | 警告，继续已有改动相关工作 |
| `NO_UPSTREAM` | 没有明确远端目标 | 停止，要求用户选择已有目标 | 同样停止 |
| `REMOTE_BRANCH_MISSING` | 查询成功但远端分支不存在 | 停止，询问正确的已有目标 | 同样停止 |
| `GIT_OPERATION_IN_PROGRESS` | merge、rebase、cherry-pick、revert 或 sequencer 未完成 | 停止，先处理已有操作 | 同样停止 |
| `REMOTE_UNAVAILABLE` | 网络、凭据、超时或远端响应异常 | 停止并处理访问问题 | 仅暂时访问失败可警告并继续已有相关工作 |
| `ERROR` | 输入、仓库或本地 Git 异常 | 停止 | 同样停止 |
| `DETACHED` | 当前处于 detached HEAD | 停止，不自动切换分支 | 停止，本地分支上下文不可靠 |

以下状态属于 `update`，处理方式不受上述脏工作区警告策略影响：

| 状态 | 含义 | 处理方式 |
| --- | --- | --- |
| `UPDATED` | 已完成安全快进并通过远端复查 | 重新读取代码后继续 |
| `DIRTY` | 更新前存在暂存、已修改或未跟踪文件 | 停止，不自动 stash |
| `FETCH_BLOCKED` | 远端获取被拒绝或远端历史发生改写 | 停止，不强制更新 |
| `UPDATE_BLOCKED` | 获取成功，但安全快进或更新后校验无法完成 | 停止，不自动改用其他更新方式 |
| `WORKTREE_CHANGED` | 获取远端期间当前分支或工作区发生变化 | 停止，不继续合并 |
| `REMOTE_MOVED` | 更新期间远端再次变化 | 停止，不自动重试 |

- 退出码 `0`：远端 tip 已在本地历史中，或更新成功
- 退出码 `1`：CLI 检测到通常需要处理的仓库状态；Codex 对脏工作区的 `check` 仍按上表判断是否阻断
- 退出码 `2`：参数、Git、网络或环境错误；仅当 `check` 已确认脏状态且错误只涉及远端读取时，Codex 才按非阻断警告处理

## 安全边界

- `check` 和 `verify-push` 仅执行只读 Git 命令，不改变 HEAD、索引、refs、`FETCH_HEAD`、操作标记、配置或工作区；通过 `GIT_OPTIONAL_LOCKS=0` 禁止可选索引刷新，通过 `GIT_NO_LAZY_FETCH=1` 禁止 partial clone 按需获取对象
- `check` 不因工作区脏而跳过；脏状态不能豁免无目标、远端删除、未完成操作或本地 Git 异常
- 干净工作区的 `BEHIND` 状态只自动尝试一次安全快进；其他状态的直接 `update` 仍需用户针对当前仓库和分支明确授权
- 执行任何 `update` 前必须先在对话中说明将要更新；命令输出不能替代这条提示
- 脏工作区禁止执行 `update`，不得因为远端提示而要求用户授权更新
- 更新要求工作区完全干净，包括未跟踪文件
- 只允许获取指定远端分支和 `git merge --ff-only`
- 不执行 stash、rebase、reset、强制 fetch、强制 push、普通 merge、分支切换或自动设置 upstream
- 更新只尝试一次；远端在执行期间再次变化时立即停止
- 更新前、fetch 失败后的诊断、更新后复查均区分分支缺失与访问失败；通过 `git rev-parse --git-path` 兼容 linked worktree 操作标记，操作检测优先于 detached HEAD 与脏状态
- 更新成功后必须重新读取仓库规则和相关源码，不能沿用旧代码分析

继续脏工作区中的任务前，应确认本次工作与已有改动相关；不相关或无法安全分离时，应使用干净工作区。明确固定到 commit、tag 或 PR 的只读分析不需要更新当前工作树。该检查只能降低任务从旧基线开始的风险，不能阻止远端在任务进行期间产生新提交

## 验证

```powershell
py -3 -B -m unittest discover -s .\git-latest-code-check\tests -v
py -3 "$env:USERPROFILE\.codex\skills\.system\skill-creator\scripts\quick_validate.py" ".\git-latest-code-check"
```

## 推送前只读复核

每次实际推送前，必须明确实际 remote 和目标分支并运行：

```text
py -3 "<skill-directory>\scripts\git_latest_code.py" verify-push --repo "<repository>" --remote origin --branch main
```

仅支持当前 `HEAD` 到单个已有分支，两个目标参数必填。读取 `git remote get-url --push --all`，查询实际推送地址，允许读取地址与推送地址不同。多个地址、复杂 refspec 或多目标推送需要先明确单一目标，不自动选择或修改配置。推送目标可以与开发 upstream 不同，必须明确报告实际目标。

仅 `CURRENT` 和 `AHEAD` 返回 `0` 并允许继续已授权的推送。目标缺失、落后、分叉或无法比较返回 `1`；访问或输入异常返回 `2`。远端对象缺失时报告 `REMOTE_DIFFERS`，要求进一步验证，不自动 fetch。脏状态不禁止推送已提交内容，但任何复核失败都停止推送。改变目标或更新完成后，实际推送前重新复核并报告。不得自动创建或恢复缺失分支。

远端查询后再次检查本地状态；HEAD 或分支并发变化返回 `WORKTREE_CHANGED`，新出现的未完成 Git 操作同样阻断。报告最新本地状态，处理并发工作后重新复核。

复核不证明写权限或保护分支允许直接推送，仍遵守仓库 PR 规则及实际 push 结果。它观察当前时刻，无法保证随后远端不变，不能以强制推送绕过失败。
