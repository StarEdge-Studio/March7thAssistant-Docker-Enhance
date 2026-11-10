<div align="center">
  <h1 align="center">
    <img src="./assets/screenshot/March7th.png" width="200">
    <br/>
    March7thAssistant (Docker 多账号增强版)
  </h1>
</div>

## 🚀 Docker 多账号增强版核心特性

本项目基于上游 [moesnow/March7thAssistant](https://github.com/moesnow/March7thAssistant) 构建，针对云·星穹铁道 Docker 部署进行了全面重构：

1. **轻量级现代 WebUI（移动端与桌面端自适应）**
   - 移除繁重的 UI 组件库，全量打包体积压缩 **95%+**（Gzip 后仅 ~70KB），大幅降低网页内存与 CPU 占用。
   - 完美适配手机端触控操作（底部导航栏 + 可视化配置表单），同时在桌面端保留带行号与语法校验的 **YAML 高级源码编辑器**。
   - **增量式实时日志终端**：按字节偏移增量拉取日志，支持阶段横幅高亮、日志级别筛选、关键字检索、自动滚动锁定与日志下载。
2. **单账号完全独立配置**
   - 移除旧版全局配置覆盖逻辑，每个游戏账号拥有独立的 YAML 配置文件（`webui/data/configs/<id>.yaml`）与浏览器数据目录（`webui/data/profiles/<id>`）。
   - 运行时自动与上游 `assets/config/config.example.yaml` 合并补全，并在任务结束后将冷却时间戳（`*_timestamp`）、体力计划进度（`power_plan`）、已使用兑换码等状态自动回写至账号配置。
3. **双轨身份认证系统（Token 密钥 / OIDC PKCE）**
   - **OIDC 模式（推荐多用户场景）**：当环境变量配置了 `OIDC_ENDPOINT`、`OIDC_CLIENT_ID`、`OIDC_CLIENT_SECRET`（及可选 `OIDC_BRAND`）时全面启用 OIDC (OAuth 2.1 PKCE `S256`) 登录。
     - 管理员用户名通过环境变量 `OIDC_ADMIN_USERNAME` 指定（支持逗号分隔多个管理员）。
     - 普通用户的 `username` 由管理员在 WebUI「账号管理」后台绑定；未绑定的其他 OIDC 用户登录后展示无权限提示页。
   - **Token 模式（默认）**：未配置 OIDC 时启用。管理员使用 `WEBUI_TOKEN` 登录；普通用户使用管理员分发的单账号专属密钥（`Secret Key`）登录。
4. **浏览器生命周期与进程隔离修复**
   - 修复 Chrome 关闭时被强制 `SIGKILL` 导致 `Preferences` / `Local State` 损坏及下次启动报 `cannot parse internal JSON template: EOF while parsing a value at line 1 column 0` 的问题。
   - 内置进程组清理、Profile 级实例隔离、运行锁清理与僵尸进程（`<defunct>`）自动回收，杜绝前序账号异常影响后续账号运行。

### 快速部署 (`docker-compose.yml`)

```yaml
services:
  march7thassistant:
    container_name: m7a-enhance
    image: ghcr.io/shingyu/march7thassistant-docker-enhance:latest
    ports:
      - "8080:8080"
    volumes:
      - ./data:/m7a/webui/data
      - ./logs:/m7a/logs
    environment:
      - TZ=Asia/Shanghai
      # --- 模式一：Token 认证（未配置 OIDC 时生效） ---
      - WEBUI_TOKEN=12345678
      # --- 模式二：OIDC 认证（配置以下三项后全面启用 OIDC PKCE） ---
      # - OIDC_ENDPOINT=https://auth.example.com/application/o/m7a/
      # - OIDC_CLIENT_ID=your_client_id
      # - OIDC_CLIENT_SECRET=your_client_secret
      # - OIDC_BRAND=SSO
      # - OIDC_ADMIN_USERNAME=admin
    shm_size: 2g
    init: true
    restart: unless-stopped
```

---


<br/>

<div align="center">
🌟 点一下右上角的 Star，GitHub 主页就能收到软件更新通知了哦~
</div>

<div align="center">
    <img src="assets/screenshot/star.gif" alt="Star" width="186" height="60">
</div>

<br/>

<div align="center">

**简体中文** | [繁體中文](./README_TW.md) | [English](./README_EN.md) | [日本語](./README_JA.md) | [한국어](./README_KR.md)

快速上手，请访问：[使用教程](https://m7a.top/docs/#/assets/docs/Tutorial)

遇到问题，请在提问前查看：[FAQ](https://m7a.top/docs/#/assets/docs/FAQ)

</div>

## 功能简介

- **日常**：清体力、每日实训、领取奖励、委托、锄大地
- **周常**：历战余响、模拟宇宙、差分宇宙、货币战争、混沌回忆、虚构叙事、末日幻影
- **云·星穹铁道**：支持后台运行、无窗口运行和 [Docker](https://m7a.top/docs/#/assets/docs/Docker) 运行
- **抽卡记录导出**：支持 [UIGF](https://uigf.org/zh/standards/uigf.html)/[SRGF](https://uigf.org/zh/standards/srgf.html) 标准
- **工具箱**：自动对话、解锁帧率、兑换码、触屏模式
- 每日实训等任务的完成情况支持**消息推送**
- 任务刷新或体力恢复到指定值后**自动启动**
- 任务完成后**声音提示、自动关闭游戏或关机等**

详情见图形界面设置或 [配置文件](assets/config/config.example.yaml)｜QQ群 [点击跳转](https://qm.qq.com/q/C3IryUWCQw)｜TG群 [点击跳转](https://t.me/+ZgH5zpvFS8o0NGI1)｜哔哩哔哩 [点击跳转](https://space.bilibili.com/3706960664857075)

## 界面展示

![README](assets/screenshot/README.png)

## 注意事项

- 遇到错误请在 [Issue](https://github.com/moesnow/March7thAssistant/issues) 反馈，提问讨论可以在 [Discussions](https://github.com/moesnow/March7thAssistant/discussions) ，群聊随缘看
- 欢迎 [PR](https://github.com/moesnow/March7thAssistant/pulls)，提交前请先阅读 [贡献指南](CONTRIBUTING.md)

## 下载安装

前往 [Releases](https://github.com/moesnow/March7thAssistant/releases/latest) 下载后解压双击三月七图标的 `March7th Launcher.exe` 打开图形界面

## 使用 AI 助手操作

DeepSeek Harness、Codex、Claude Code 等能执行命令的 AI 助手都可以直接操作三月七小助手：安装、运行任务、修改设置、查看日志和排查问题。

- 已经安装：在「设置 → 关于 → AI 助手」点击「复制提示词」，粘贴给你的 AI 助手即可
- 还没安装：对 AI 助手说「帮我安装三月七小助手，说明见 https://m7a.top/assets/agent/skills/march7th-assistant/SKILL.md 」

AI 助手使用的是不需要管理员权限的命令行入口 `m7a.exe`（运行任务时默认弹出一次 UAC，人不在电脑前时可在设置中开启「免 UAC 运行」），说明文件随程序一起发布在 [`assets/agent/`](assets/agent/skills/march7th-assistant/SKILL.md)，同样适用于其他支持 Skill 的 AI 助手。详见 [AI 助手文档](https://m7a.top/docs/#/assets/docs/Agent)。

## 源码运行

如果你是完全不懂的小白，请通过上面的方式下载安装，可以不用往下看了。

需要 Python 3.12 或更高版本。

Windows 下如果通过终端启动，建议使用管理员模式打开 PowerShell、Windows Terminal 或 CMD；Windows 11 24H2 及以上也可以按 [Sudo for Windows](https://learn.microsoft.com/zh-cn/windows/advanced-settings/sudo/) 的方式执行。

```cmd
# 安装（推荐使用虚拟环境）
git clone --recurse-submodules https://github.com/moesnow/March7thAssistant
cd March7thAssistant
pip install -r requirements.txt

# 启动图形界面
python app.py

# 执行完整运行（查看全部子命令：python main.py -h）
python main.py

# 更新
git pull
git submodule update --init --recursive
```

如果使用 `uv`，推荐直接使用项目自带的 `pyproject.toml` 工作流：

```cmd
# 安装（使用 uv）
git clone --recurse-submodules https://github.com/moesnow/March7thAssistant
cd March7thAssistant
uv sync

# 启动图形界面
uv run python app.py

# 查看命令行帮助
uv run python main.py -h

# 执行完整运行
uv run python main.py

# 执行每日实训
uv run python main.py daily
```

<details>
<summary>开发相关</summary>

获取 crop 参数表示的裁剪坐标，可以通过小助手工具箱内「游戏截图」卡片的「捕获」功能

</details>

---

如果喜欢本项目，可以微信赞赏送作者一杯咖啡☕

您的支持就是作者开发和维护项目的动力🚀

![sponsor](assets/app/images/sponsor.jpg)

---

## 相关项目

March7thAssistant 离不开以下开源项目和运行时依赖的帮助，感谢所有维护者与贡献者：

- 模拟宇宙自动化 [https://github.com/CHNZYX/Auto_Simulated_Universe](https://github.com/CHNZYX/Auto_Simulated_Universe) ：提供模拟宇宙相关能力
- 锄大地自动化 [https://github.com/linruowuyin/Fhoe-Rail](https://github.com/linruowuyin/Fhoe-Rail) ：提供锄大地相关能力
- OCR 文字识别 [https://github.com/RapidAI/RapidOCR](https://github.com/RapidAI/RapidOCR) ：提供游戏内文字识别能力
- 图形界面组件库 [https://github.com/zhiyiYo/PyQt-Fluent-Widgets](https://github.com/zhiyiYo/PyQt-Fluent-Widgets) ：提供主要界面组件与交互体验
- Mirror酱 [https://github.com/MirrorChyan/docs](https://github.com/MirrorChyan/docs) ：提供更新检查与下载分发以及 CDN 加速相关能力
- 图像处理与自动化相关依赖 `OpenCV`、`PyAutoGUI` 等：提供截图采集、图像处理与基础自动化能力
- 推理加速相关依赖 `ONNX Runtime`、`OpenVINO` ：为 OCR 和模型推理提供 CPU / GPU 加速支持

此外，`requirements.txt` 中还包含大量底层依赖，在这里不一一列出；同样感谢这些项目对本项目的支持。


## Contributors
<a href="https://github.com/moesnow/March7thAssistant/graphs/contributors">

  <img src="https://contrib.rocks/image?repo=moesnow/March7thAssistant" />

</a>

## Stargazers over time

<a href="https://star-history.dera.page/#moesnow/March7thAssistant">
 <picture>
   <source media="(prefers-color-scheme: dark)" srcset="https://star-history.dera.page/svg?repos=moesnow/March7thAssistant&theme=dark" />
   <source media="(prefers-color-scheme: light)" srcset="https://star-history.dera.page/svg?repos=moesnow/March7thAssistant" />
   <img alt="Star History Chart" src="https://star-history.dera.page/svg?repos=moesnow/March7thAssistant" />
 </picture>
</a>
