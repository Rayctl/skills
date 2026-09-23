# Git Latest Code Check

在规划或修改代码前，只读检查当前 Git 分支是否已经包含指定远端分支的最新提交。发现代码基线不确定时先停止并说明，只有得到明确同意后才尝试安全快进更新

## 工作方式

每个任务、每个仓库和分支只检查一次：

```text
任务开始
  -> 仅在代码规划或修改任务中检查是否有关联仓库或明确路径
  -> 没有候选目录：静默跳过，不运行 Git 命令或加载 Skill
  -> 仅从当前工作目录或用户明确给出的路径确定候选目录
  -> git rev-parse 预检
  -> 非 Git：静默跳过，不加载 Skill
  -> 已确认 Git worktree：调用 Skill
  -> 无论工作区是否有改动，都只读检查远端
  -> 干净 + CURRENT / AHEAD：继续规划或编码
  -> 干净 + 远端不同或无法确认：停止并提示
  -> 脏 + CURRENT / AHEAD：提示脏状态，继续相关工作
  -> 脏 + 远端不同或无法确认：警告但不阻断相关工作
  -> 脏 + 本次任务与已有改动无关：停止，要求使用干净工作区
  -> 仅干净工作区可在用户明确同意后尝试更新
  -> 可快进：更新后重新读取代码
```

“最新”表示本地 `HEAD` 等于远端 tip，或者本地历史已经包含远端 tip。本地存在尚未推送的提交不会被误判为过期。脏工作区不会跳过远端观察，只会把远端问题从阻断条件降为警告，因为此时禁止自动更新，也不应打断已在进行的相关本地工作

## 基线交接

`CURRENT` 或 `AHEAD` 成功结果中的完整 `local` 提交号可以作为本次任务的本地代码基线。后续语言或质量 Skill 可以复用它，对比自己的本地提示、构建配置或任务变更，不需要为取得基线再次访问远端。下游同时携带 `remoteFreshness: confirmed`；脏工作区警告、远端不可用、无 upstream 或其他失败结果只能携带 `remoteFreshness: unconfirmed`，可用于读取本地代码，但不能刷新本地元数据基线。

基线交接只复用已经观察到的提交号，不会提高下游提示的权威级别，也不保证任务期间工作区或远端保持不变。只有仓库、分支发生变化，用户明确要求，或获准更新成功时，才重新执行远端检查。

## 对话可见反馈

脚本会将状态和相关字段写入标准输出，但 Codex 的命令或工具输出可能不会直接展示给用户。因此，每次执行 `check` 或 `update` 后，Codex 都必须先在对话中明确报告结果，再继续工作或停止：

- `CURRENT`、`AHEAD`、`UPDATED`：用一句简洁摘要说明仓库、当前分支、远端目标、状态和 7 位短提交号；仅在工作区为脏时额外提醒
- 脏工作区的远端差异或远端读取失败：说明状态、可获得的仓库与提交信息、脏状态和原因，并明确远端新鲜度未确认、只允许继续已有改动相关的工作、禁止执行 `update`
- 其他状态或命令异常：说明状态（没有状态时使用 `ERROR`）、可获得的仓库与提交信息、脏状态、原因和下一步，并遵守原有停止及授权边界

不能把隐藏的命令或工具输出视为已经通知用户

## 安装

将整个目录复制到 Codex 用户 Skill 目录：

```powershell
Copy-Item -Recurse -Force ".\git-latest-code-check" "$env:USERPROFILE\.codex\skills"
```

在用户级 `~/.codex/AGENTS.md` 中加入：

```markdown
## Git Latest Code Check

Apply this section only when the user requests substantive code planning, creation, or modification. If the conversation has no associated repository and the user did not explicitly provide a repository path, stop applying this section without running Git commands and do not load, invoke, or mention `$git-latest-code-check`.

Otherwise, identify a candidate directory only from the current working directory or the explicitly provided repository path. Confirm it with `git -C "<candidate>" rev-parse --is-inside-work-tree`. Do not search unrelated directories for a repository. If the command fails or does not return `true`, do not load, invoke, or mention the skill.

If the command succeeds, explicitly read and follow `~/.codex/skills/git-latest-code-check/SKILL.md` as `$git-latest-code-check` once before relying on or modifying code in that Git worktree. Do not rely on implicit skill discovery for this step. Apply the Skill's clean-versus-dirty worktree policy to decide whether a remote mismatch stops the task or becomes a warning. Apply language- or task-specific skills only after the check passes or the Skill explicitly permits related existing work to continue with a dirty-worktree warning. Explicit user and repository instructions take precedence.
```

`agents/openai.yaml` 已关闭隐式调用。日常 Git 仓库任务由上面的全局规则在预检通过后从用户 Skill 目录显式读取，也可以在对话中显式输入 `$git-latest-code-check`

## 命令

使用当前分支配置的 upstream：

```powershell
py -3 "$env:USERPROFILE\.codex\skills\git-latest-code-check\scripts\git_latest_code.py" check --repo "D:\path\to\repo"
```

当前分支没有 upstream，但用户已经明确指定远端目标时：

```powershell
py -3 "$env:USERPROFILE\.codex\skills\git-latest-code-check\scripts\git_latest_code.py" check --repo "D:\path\to\repo" --remote origin --branch main
```

发现远端不同并得到用户明确同意后，执行安全更新：

```powershell
py -3 "$env:USERPROFILE\.codex\skills\git-latest-code-check\scripts\git_latest_code.py" update --repo "D:\path\to\repo"
```

`--remote` 和 `--branch` 必须同时提供。显式目标只用于本次调用，不会修改本地 upstream 配置

## 状态与退出码

`check` 的状态必须与 `dirty` 字段一起解释：

| 状态 | 含义 | `dirty: false` | `dirty: true` |
| --- | --- | --- | --- |
| `CURRENT` | 本地与远端提交一致 | 继续 | 提示脏状态，继续相关工作 |
| `AHEAD` | 本地已包含远端最新提交并有额外提交 | 继续 | 提示脏状态，继续相关工作 |
| `REMOTE_DIFFERS` | 远端提交与本地不同，但只读检查无法安全分类 | 停止并请求更新授权 | 警告，继续已有改动相关工作 |
| `BEHIND` | 本地单纯落后 | 停止并请求更新授权 | 警告，继续已有改动相关工作 |
| `DIVERGED` | 本地与远端已经分叉 | 停止并由用户处理 | 警告，继续已有改动相关工作 |
| `NO_UPSTREAM` | 当前分支没有可用远端目标 | 停止并要求明确目标 | 警告，继续已有改动相关工作 |
| `REMOTE_UNAVAILABLE` | 远端无法访问或目标分支不存在 | 停止并处理网络、凭据或分支配置 | 警告，继续已有改动相关工作 |
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

- `check` 只执行只读 Git 命令，通过 `GIT_OPTIONAL_LOCKS=0` 禁止可选索引刷新，并通过 `GIT_NO_LAZY_FETCH=1` 禁止 partial clone 按需获取缺失对象
- `check` 不因工作区脏而跳过；脏状态只改变 Codex 对远端问题的处理方式
- `update` 必须由用户针对当前仓库和分支明确授权
- 脏工作区禁止执行 `update`，不得因为远端提示而要求用户授权更新
- 更新要求工作区完全干净，包括未跟踪文件
- 只允许获取指定远端分支和 `git merge --ff-only`
- 不执行 stash、rebase、reset、强制 fetch、强制 push、普通 merge、分支切换或自动设置 upstream
- 更新只尝试一次；远端在执行期间再次变化时立即停止
- 更新成功后必须重新读取仓库规则和相关源码，不能沿用旧代码分析

继续脏工作区中的任务前，应确认本次工作与已有改动相关；不相关或无法安全分离时，应使用干净工作区。明确固定到 commit、tag 或 PR 的只读分析不需要更新当前工作树。该检查只能降低任务从旧基线开始的风险，不能阻止远端在任务进行期间产生新提交

## 验证

```powershell
py -3 -m unittest discover -s .\git-latest-code-check\tests -v
py -3 "$env:USERPROFILE\.codex\skills\.system\skill-creator\scripts\quick_validate.py" ".\git-latest-code-check"
```
