<div align="center">
  <h1>🐳 March7thAssistant Docker-Enhance</h1>
  <p>专为每日日常任务自动化、多账号云游戏托管、Docker 容器化部署与远程 Web 管理设计的 <b>三月七小助手</b> 增强重构版</p>

  <a href="https://github.com/staredge-studio/March7thAssistant-Docker-Enhance/issues"><img alt="GitHub issues" src="https://img.shields.io/github/issues/staredge-studio/March7thAssistant-Docker-Enhance"></a>
  <a href="https://github.com/staredge-studio/March7thAssistant-Docker-Enhance/pulls"><img alt="GitHub pull requests" src="https://img.shields.io/github/issues-pr/staredge-studio/March7thAssistant-Docker-Enhance"></a>
  <img alt="License" src="https://img.shields.io/badge/License-GPL%20v3-blue.svg">
</div>

<br/>

> [!CAUTION]
> **重构版镜像名称变更提示**：本项目已完成全面底层重构，移除了旧版的全局配置覆盖机制并调整了数据存储结构。为防止开启了每日自动更新镜像（如 Watchtower）的旧版用户拉取后导致容器运行失败，**重构版已改用全新的镜像名称 `ghcr.io/staredge-studio/march7thassistant-docker-enhance-v2`**。旧镜像 `ghcr.io/staredge-studio/march7thassistant-docker-enhance` 不再更新，请及时迁移至新镜像。由此带来的不便，敬请谅解。

> [!IMPORTANT]
> **适用人群说明**：本项目专为有多账号云游戏托管、服务器 Docker 容器化运行与远程 Web 集中管理需求的进阶用户设计。**普通单账号用户或本地电脑运行用户强烈推荐直接使用原版项目 [moesnow/March7thAssistant](https://github.com/moesnow/March7thAssistant)**，原版桌面端拥有最完善的功能支持与开箱即用的图形界面体验。

> [!WARNING]
> **功能限制说明**：本增强版专注于**每日实训、清体力、培养目标、历战余响、奖励领取等日常自动化**及轻量级远程管理。在无头浏览器（Headless）云游戏容器环境下，**差分宇宙、货币战争、模拟宇宙、锄大地等高阶复杂交互功能可能出现异常或无法正常工作**。如需稳定使用上述功能，请使用原版桌面端。

---

## ✨ 核心特性

* 🎨 **响应式双主题 Web 控制台（M3E / Simple）**
  * **M3E 主题（默认）**：基于 Google **Material 3 Expressive** 规范打造，提供现代化的动态色彩容器、卡片式分组布局与流畅交互动效。
  * **Simple 主题**：极简轻量的经典管理界面，可通过环境变量 `WEBUI_THEME=simple` 切换。
  * **全端响应式适配**：同时适配移动端触控操作与桌面端大屏管理，移动端提供专属顶栏与底部胶囊导航，桌面端提供更宽敞的多栏视图与源码编辑体验。
* 👥 **多用户与双轨权限认证（Token 密钥 / OIDC）**
  * **OIDC 统一身份认证**：配置 `OIDC_ENDPOINT`、`OIDC_CLIENT_ID`、`OIDC_CLIENT_SECRET` 后即可启用 **OAuth 2.1 PKCE (`S256`)** 标准登录，支持同步用户头像与显示名称。
    * 管理员可通过环境变量 `OIDC_ADMIN_USERNAME` 指定（支持逗号分隔多个管理员），拥有全局管理权限。
    * 普通用户由管理员在后台绑定至对应游戏账号（支持同一用户绑定多个账号），登录后仅可查看与操作已授权的账号。
  * **Token 密钥认证（默认）**：未配置 OIDC 时启用。管理员使用 `WEBUI_TOKEN` 登录管理全局；普通用户使用**账号专属密钥（Secret Key）**登录，仅管理对应单账号。
  * **邀请链接自助接入**：管理员可为账号生成有效期 7 天的邀请链接，用户打开链接后即可自助完成身份绑定（OIDC 登录或保存专属密钥）与游戏扫码登录；管理员可统一查看链接状态、刷新链接（生成有效期 7 天的新链接）或删除链接。
* ⚙️ **多账号托管与双模式独立配置**
  * **单账号完全隔离**：支持添加与托管任意数量的云游戏账号，每个账号均拥有独立的 YAML 配置文件（`webui/data/configs/<id>.yaml`）与独立的浏览器数据目录（`webui/data/profiles/<id>`），支持自定义执行顺序与启用状态。
  * **可视化 + 源码双模式编辑**：提供直观的**简洁可视化模式**（支持培养目标快捷设置、按副本类型动态展示配置项）与支持行号、搜索、保留完整注释的**高级 YAML 源码编辑模式**。
  * **状态自动持久化**：任务运行期间产生的冷却时间戳、体力计划进度、已使用兑换码等动态数据会自动保存回对应账号配置。
* 📱 **Web 端扫码登录与定时任务调度**
  * **内置云游戏扫码器**：直接在网页端启动无头浏览器获取「云·星穹铁道」登录二维码，使用手机米游社 App 扫码即可完成账号登录授权，二维码过期支持自动刷新。
  * **多时间点定时调度与进程守护**：支持设置每日多个定时启动时间点及外网连通性预检；内置浏览器 Profile 状态自检、进程隔离清理与运行锁管理，保障多账号长周期稳定运行。
* 🖥️ **实时日志终端与多渠道消息通知**
  * **实时日志终端**：支持任务运行日志实时流式查看、阶段横幅高亮、日志级别筛选、关键词检索、自动滚动锁定与日志文件下载。
  * **多渠道通知推送**：支持原版全部通知方式（Server酱、Bark、Telegram、企业微信、飞书、钉钉、Gotify、Webhook、邮件等），并内置 **[PushChan QQ](https://github.com/shing-yu/pushchan-qq-bot)** 消息与截图推送（支持自定义 API 地址及私聊/群聊切换）。


---

## 🚀 快速部署 (Docker Compose)

### 1. 创建部署目录与配置文件

```bash
mkdir m7a-docker && cd m7a-docker
vim docker-compose.yml
```

### 2. 编写 `docker-compose.yml`

```yaml
services:
  march7thassistant:
    container_name: m7a-enhance
    image: ghcr.io/staredge-studio/march7thassistant-docker-enhance-v2:latest
    ports:
      - "18080:8080"  # [宿主机端口]:[容器内端口]，可按需修改左侧宿主机端口
    volumes:
      - ./data:/m7a/webui/data
      - ./logs:/m7a/logs
    environment:
      - TZ=Asia/Shanghai
      - MARCH7TH_LOG_LEVEL=INFO
      # 前端界面风格：m3e (默认 Material 3 Expressive) 或 simple (轻量简洁版)
      - WEBUI_THEME=m3e
      # ==========================================================
      # 认证模式一：Token 密钥认证（默认启用，未配置 OIDC 时生效）
      # ==========================================================
      - WEBUI_TOKEN=your_strong_admin_token_here
      # ==========================================================
      # 认证模式二：OIDC 统一身份认证（配置以下三项后自动切换为 OIDC 模式）
      # ==========================================================
      # - OIDC_ENDPOINT=https://auth.example.com/application/o/m7a/
      # - OIDC_CLIENT_ID=your_client_id
      # - OIDC_CLIENT_SECRET=your_client_secret
      # - OIDC_BRAND=SSO
      # - OIDC_ADMIN_USERNAME=admin
    network_mode: "bridge"
    shm_size: 2g
    init: true
    restart: unless-stopped
```

### 3. 启动容器

```bash
docker compose up -d
```

启动完成后，浏览器访问 `http://<服务器IP>:18080` 即可进入控制台。

---

## 🔧 环境变量说明

| 环境变量 | 默认值 | 说明 |
| :--- | :--- | :--- |
| `WEBUI_THEME` | `m3e` | 前端主题风格：`m3e`（Material 3 Expressive）或 `simple`（简洁版） |
| `WEBUI_TOKEN` | `12345678` | Token 模式下的管理员登录密码（生产环境请务必修改） |
| `OIDC_ENDPOINT` | 空 | OIDC Issuer 地址或 `.well-known/openid-configuration` 地址 |
| `OIDC_CLIENT_ID` | 空 | OIDC 客户端 ID |
| `OIDC_CLIENT_SECRET` | 空 | OIDC 客户端密钥（当 Endpoint / ID / Secret 均非空时全面启用 OIDC） |
| `OIDC_BRAND` | `OIDC` | 登录页按钮展示的认证品牌名称（例如 `Pocket ID`、`Authelia`、`Casdoor`） |
| `OIDC_ADMIN_USERNAME` | 空 | OIDC 管理员用户名，支持用英文逗号分隔多个管理员 |
| `OIDC_SCOPES` | `openid profile email` | OIDC 请求的权限范围 |
| `MARCH7TH_LOG_LEVEL` | `INFO` | 小助手运行日志级别（`INFO` / `DEBUG` / `WARNING` / `ERROR`） |

> **OIDC 回调地址配置提示**：在您的 OIDC 服务端（如 Authelia / Authentik / Casdoor / Pocket ID）中，请将 Redirect URI（回调地址）配置为前端根路径：`http(s)://<您的访问域名或IP:端口>/`。

---

## 📖 使用指南

1. **添加账号**：管理员登录 WebUI 后，进入「账号配置」页面，点击右上角「新增游戏账号」，填写账号备注名（OIDC 模式下可同时填写授权用户的 `username`）。
   * **邀请用户自助接入（可选）**：在新增弹窗底部开启「生成邀请链接」，点击「保存并复制」即可得到一条 7 天有效的邀请链接。用户打开链接点击「登录并绑定」后：OIDC 模式下跳转统一身份登录并自动绑定 `username`；Token 模式下需保存页面展示的专属密钥。随后用户扫码登录游戏账号，完成后自动跳转至任务配置页。
   * **管理邀请链接**：点击「新增游戏账号」左侧的「邀请链接」按钮，可查看每条链接的状态（待使用 / 已使用 / 已过期），复制链接、刷新链接或删除，也可为已有账号生成新的邀请链接。
2. **扫码登录**：在账号卡片上点击「扫码登录」，使用手机**米游社 App** 扫描弹出的二维码并在手机端点击确认登录，等待状态变为「已登录」。
3. **配置任务**：
   * 进入「任务配置」页面，在顶部选择需要编辑的账号。
   * **简洁模式**：可视化配置「体力与副本」（培养目标优先级高于下方普通副本）、「周积分线奖励」、「支援角色」、「消息推送」等常用项。
   * **高级模式**（桌面端）：直接编辑带完整注释的独立 YAML 配置文件。
4. **启动与定时运行**：
   * 在「全局设置」中可配置每日定时触发时间（支持多个 `HH:MM` 时间点）及外网连通性预检。
   * 在「运行与日志」页面可随时点击「全部执行」或单账号立即执行，并实时查看高亮运行日志。

---

## 💻 系统配置要求

| 硬件/环境 | 最低要求 | 推荐配置 | 说明 |
| :--- | :--- | :--- | :--- |
| **操作系统** | Linux (`amd64` / `arm64`) | Ubuntu / Debian 纯净环境 | 需安装 Docker 与 Docker Compose |
| **共享内存 (`shm_size`)** | `1g` | **`2g`** | 防止无头 Chrome 渲染云游戏画面时因 `/dev/shm` 不足崩溃 |
| **内存 (RAM)** | **4 GB** | 6 GB 或以上 | 保障浏览器 WebGL 渲染与 RapidOCR 文字识别稳定运行 |
| **处理器 (CPU)** | 2 核 | 4 核或以上 | 影响云游戏帧率与图像识别速度 |

---

## 📄 许可证

本项目采用与上游一致的开源许可证（[GPL-3.0](LICENSE)），仅供个人学习、技术研究与自动化测试使用。

---

> [!TIP]
> **以下为原项目 README 内容：**

---

<div align="center">
  <h1 align="center">
    <img src="./assets/screenshot/March7th.png" width="200">
    <br/>
    March7thAssistant
  </h1>
</div>

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
