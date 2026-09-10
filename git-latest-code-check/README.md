# Git Latest Code Check

在规划或修改代码前，只读检查当前 Git 分支是否已经包含指定远端分支的最新提交。发现代码基线不确定时先停止并说明，只有得到明确同意后才尝试安全快进更新

## 工作方式

每个任务、每个仓库和分支只检查一次：

```text
任务开始
  -> 只读检查远端
  -> CURRENT / AHEAD：继续规划或编码
  -> 远端不同或无法确认：停止并提示
  -> 用户明确同意更新
  -> 干净且可快进：更新后重新读取代码
  -> 脏目录或分支分叉：停止，不自动整理
```

“最新”表示本地 `HEAD` 等于远端 tip，或者本地历史已经包含远端 tip。本地存在尚未推送的提交不会被误判为过期

## 安装

将整个目录复制到 Codex 用户 Skill 目录：

```powershell
Copy-Item -Recurse -Force ".\git-latest-code-check" "$env:USERPROFILE\.codex\skills"
```

在用户级 `~/.codex/AGENTS.md` 中加入：

```markdown
## Git Latest Code Check

Use `$git-latest-code-check` once before substantive planning, creating, or modifying code in a Git repository. Run its read-only check before relying on repository code. If the selected remote branch differs or cannot be verified, stop and explain the state before requesting approval for any update. Apply language- or task-specific skills only after this check passes. Explicit user and repository instructions take precedence.
```

`agents/openai.yaml` 已启用隐式调用，也可以显式输入 `$git-latest-code-check`

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

| 状态 | 含义 | 是否继续 |
| --- | --- | --- |
| `CURRENT` | 本地与远端提交一致 | 继续 |
| `AHEAD` | 本地已包含远端最新提交并有额外提交 | 继续 |
| `UPDATED` | 已完成安全快进并通过远端复查 | 重新读取代码后继续 |
| `REMOTE_DIFFERS` | 远端提交与本地不同，但只读检查无法安全分类 | 停止并请求更新授权 |
| `BEHIND` | 本地单纯落后，得到授权后可以尝试更新 | 停止并请求更新授权 |
| `DIVERGED` | 本地与远端已经分叉 | 停止并由用户处理 |
| `DIRTY` | 更新前存在暂存、已修改或未跟踪文件 | 停止，不自动 stash |
| `NO_UPSTREAM` | 当前分支没有可用远端目标 | 停止并要求明确目标 |
| `DETACHED` | 当前处于 detached HEAD | 停止，不自动切换分支 |
| `REMOTE_UNAVAILABLE` | 远端无法访问或目标分支不存在 | 停止并处理网络、凭据或分支配置 |
| `FETCH_BLOCKED` | 远端获取被拒绝或远端历史发生改写 | 停止，不强制更新 |
| `WORKTREE_CHANGED` | 获取远端期间当前分支或工作区发生变化 | 停止，不继续合并 |
| `REMOTE_MOVED` | 更新期间远端再次变化 | 停止，不自动重试 |

- 退出码 `0`：可以继续或更新成功
- 退出码 `1`：需要用户处理或授权
- 退出码 `2`：参数、Git、网络或环境错误

## 安全边界

- `check` 只执行只读 Git 命令，并通过 `GIT_OPTIONAL_LOCKS=0` 禁止可选索引刷新
- `update` 必须由用户针对当前仓库和分支明确授权
- 更新要求工作区完全干净，包括未跟踪文件
- 只允许获取指定远端分支和 `git merge --ff-only`
- 不执行 stash、rebase、reset、强制 fetch、强制 push、普通 merge、分支切换或自动设置 upstream
- 更新只尝试一次；远端在执行期间再次变化时立即停止
- 更新成功后必须重新读取仓库规则和相关源码，不能沿用旧代码分析

明确固定到 commit、tag 或 PR 的只读分析不需要更新当前工作树。该检查只能降低任务从旧基线开始的风险，不能阻止远端在任务进行期间产生新提交

## 验证

```powershell
py -3 -m unittest discover -s .\git-latest-code-check\tests -v
py -3 "$env:USERPROFILE\.codex\skills\.system\skill-creator\scripts\quick_validate.py" ".\git-latest-code-check"
```
