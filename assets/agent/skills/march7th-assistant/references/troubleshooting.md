# 排查说明

## 先看运行记录

运行 `m7a.exe --status`，在 `runs_dir` 指向的文件夹里可以找到每次运行的文件。

| 文件 | 内容 |
|---|---|
| `<运行编号>.json` | `status`（success / failed / blocked / stopped / interrupted / running）、`reason`、`error`、`exit_code`、`screenshot`、起止时间、发起方 `invoker`、运行锁 `lock`（acquired / forced / busy / unavailable） |
| `<运行编号>.log` | 本次运行的完整输出 |

`.\m7a.exe --follow latest` 会显示最近一次运行的末尾输出与结论。记录显示 running 但进程已经不在时，`--status` / `--follow` 会报告为 aborted：
通常是控制台窗口被关闭或进程被结束，不代表任务完成。

在 `--status` 的 `logs_dir` 中，`<日期>.log` 是当天的完整日志（含图形界面任务），`config_diag.log` 记录配置文件读写。
图形界面闪退时看同目录的 `crash.log`：里面有未捕获异常、原生崩溃和 Qt 致命错误；只有「图形界面启动」没有对应的「图形界面退出」，说明进程被外部结束或发生了无法捕获的崩溃。

## 常见情况

| 现象 | 处理 |
|---|---|
| 退出码 3 / `reason: first_run_required` | 打开 `March7th Launcher.exe`，请用户本人阅读并确认免责声明 |
| 退出码 4 / `reason: busy` | 已有任务在操控游戏（`--status` 的 `active_run`）。等它结束，或询问用户后用 `--control current stop` 停止 |
| 退出码 5 | 看输出里的原因。UAC 被取消或无法弹出：请用户在电脑前点「是」；用户需要远程运行时，说明「免 UAC 运行」及其风险，由用户本人决定是否开启（见 SKILL.md 第 5 节）。免 UAC 运行没能启动任务：请用户在图形界面「设置 → 高级」把开关关掉再打开，仍失败时检查是否被安全软件拦截 |
| 已开启免 UAC 运行，仍然弹出 UAC | 看 `--status` 的 `uac_free`：`other` 表示开关是在另一个安装目录开启的（或移动过安装目录），`disabled` 表示计划任务在任务计划程序中被禁用，`off` 表示没有开启。请用户在当前目录的图形界面中重新打开开关 |
| 日志警告「运行锁不可用」/ `lock: unavailable` | `--status` 给出的 `runs_dir` 无法读写（权限、磁盘已满、杀毒软件拦截等，原因见 `lock_error`）。任务仍会运行，但不会检查是否有其他任务同时在操控游戏：先用 `--status` 确认没有其他运行，再修复目录权限 |
| 找不到游戏 / 启动游戏失败 | 检查 `--status` 的 `game_path_exists`，修正 `game_path`；使用启动器或云游戏时检查对应配置 |
| 提示切换界面失败、识别失败 | 常见原因是滤镜、帧率显示、HDR、非 16:9 分辨率或窗口被遮挡，见 FAQ「开了滤镜、帧率显示…」一节，并查看 `screenshot` |
| 未找到可执行文件、程序被删除 | 杀毒软件误删：请用户把小助手目录加入排除项后重新解压（FAQ 有说明） |
| 中文输出有个别乱码 | PowerShell 先执行 `[Console]::OutputEncoding = [Text.Encoding]::UTF8`，或直接读取 `runs_dir` 下的 `<运行编号>.log`（UTF-8） |
| 任务结束后电脑关机 / 睡眠 | 配置中的 `after_finish` 生效了；Agent 发起的运行请带 `--after-finish None` |

更多问题见 `assets/docs/FAQ.md`。给出结论时把「日志里看到的事实」和「推测」分开说明。

## 安卓设备（ADB）

「设置 → 运行方式」选「安卓设备」时，小助手通过 ADB 操作手机或模拟器。Windows 和 macOS 的设置、行为和报错都相同，只有找 adb 不一样：Windows 上可以在「Android 设备」里点「下载 adb」，也会自动找 MuMu 等模拟器自带的 adb；macOS 上要自己安装 Android Platform-Tools 并加入 PATH，或在「高级设置 → adb 路径」里选择。

- **设备要求**：Android 10 及以上，装好国服《崩坏：星穹铁道》，并且已经在设备上手动登录过一次游戏。
- **自检**：`.\m7a.exe adb_check --after-finish None` 不需要管理员权限。它会连接设备、启动游戏进到主界面、打开手机菜单，最后保存一张遮住 UID 的截图（路径在输出里），可以直接查看。图形界面的「环境检查 → 开始检查」只检查环境，不启动游戏。
- **游戏在哪块屏幕上运行**，由「高级设置 → 设备类型」决定（配置 `adb_device_type`）：

| 设备类型 | 游戏在哪里运行 |
|---|---|
| 自动判断（默认） | Android 14 及以上的模拟器直接用模拟器窗口，模拟器分辨率必须是 1280×720 横屏；手机和 Android 14 以下的模拟器用后台虚拟屏，分辨率不影响 |
| 实体机 | 总是用后台虚拟屏，模拟器也可以选 |
| 模拟器 | 总是用模拟器窗口：Android 14 以下会报不能直接使用模拟器画面，分辨率不是 1280×720 横屏会报分辨率错误 |

- **后台虚拟屏看不见**：任务运行时，手机屏幕或模拟器窗口里看不到游戏，这是正常的，不是没启动。游戏启动时登录界面会短暂回到手机屏幕或模拟器窗口，登录完成后小助手自动把游戏移回虚拟屏。需要手动登录时小助手会停下提示，请用户在手机或模拟器窗口里登录，再重新运行。用户说「看不到界面、没法登录」时，请他们先直接在模拟器里打开游戏、登录好账号，再运行任务。
- **Android 14 以下的模拟器也能用**：报不能直接使用模拟器画面，或者 Android 14 以下的模拟器提示分辨率不对时，把设备类型改回「自动判断」就会改用虚拟屏，不要因此告诉用户这台模拟器不能用。只有用户坚持要在模拟器窗口里看着游戏运行，才需要换 Android 14 及以上、能设成 1280×720 横屏的模拟器。Android 14 及以上的模拟器分辨率不对时，可以改分辨率，也可以把设备类型改成「实体机」用虚拟屏。
- 报错里会写下一步怎么做（例如打开「USB 调试（安全设置）」、把分辨率改成 1280×720），转述时用界面上的叫法。完整步骤见 `assets/docs/Tutorial.md` 的「安卓设备（ADB）」和 `assets/docs/Android.md`。

## 停止与暂停

- `.\m7a.exe --control current pause` / `resume`：在下一次键鼠操作前停住或恢复，不会对游戏做任何额外操作。
- `.\m7a.exe --control current stop`：任务在下一次键鼠操作前结束（退出码 6）；长时间等待中的任务最迟约 60 秒后强制结束。游戏本身保持打开。

## 旧版本（没有 m7a.exe）

旧版本只有 `March7th Assistant.exe`，它在清单里要求管理员权限：普通权限的终端直接运行会报「需要提升」，
提权后又在新窗口中运行，看不到输出，也拿不到退出码。可以这样替代：

```powershell
$dir = 'D:\March7thAssistant'   # 安装目录
$p = Start-Process -FilePath (Join-Path $dir 'March7th Assistant.exe') -ArgumentList 'daily' -WorkingDirectory $dir -Verb RunAs -PassThru -Wait
$p.ExitCode   # 旧版本在未确认免责声明等情况下也可能返回 0，需要结合日志判断
Get-Content (Join-Path $dir ("logs\" + (Get-Date -Format 'yyyy-MM-dd') + '.log')) -Encoding utf8 -Tail 40
```

注意旧版本默认在结束时等待「按回车键关闭窗口」（配置 `pause_after_success` / `exit_after_failure`），没有人按回车时 `-Wait` 会一直等待。
建议用户更新到包含 `m7a.exe` 的新版本。
