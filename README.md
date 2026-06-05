# DeepSeek Balance Monitor Bot

[![Python](https://img.shields.io/badge/Python-3.8+-blue?logo=python&logoColor=white)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![DeepSeek](https://img.shields.io/badge/DeepSeek-Platform-4F46E5)](https://platform.deepseek.com/)
[![Telegram](https://img.shields.io/badge/Telegram-Bot-26A5E4?logo=telegram&logoColor=white)](https://t.me/botfather)

定时查询 [DeepSeek 开放平台](https://platform.deepseek.com/) 账户余额，并通过 Telegram Bot 推送并置顶消息。同时支持系统运行时间显示以及自定义 systemd 服务状态监控。

本脚本完全基于 **Python 标准库** 实现，**零第三方依赖**，无需安装任何额外的 `pip` 包。

```text
💰 ¥12.34 | 14:30
🆙 3d 2h  | 🟢SS 🟢Bot
```

---

## Features (核心功能)

- 🚀 **零依赖运行** — 纯 Python 标准库实现，解压即用，免去 `pip install` 烦恼。
- 📌 **消息自动置顶** — 始终保持一条置顶消息，实时更新，避免群聊/频道被刷屏。
- 🔄 **智能自动恢复** — 即使本地缓存丢失或程序重启，Bot 也会自动检测并复用 Telegram 中现有的置顶余额消息，不会重复创建。
- 🛡️ **单例运行保护** — 通过 PID 锁文件防止在同一台服务器上意外启动多个实例。
- 📡 **服务状态监控** — 支持在消息底部通过 🟢/🔴 指示灯实时监控其他 systemd 服务（如 Shadowsocks、Nginx 等）。
- ⏱️ **系统运行时间** — 实时读取 `/proc/uptime` 并展示精简的系统运行时间（如 `3d 2h`）。
- 🔁 **容错与重试机制** — 网络波动或 DeepSeek API 暂时不可用时自动重试，确保服务稳定。

---

## Command Reference (命令行指令)

脚本支持两种运行模式：**常驻守护进程模式** 和 **单次执行模式**。

### 1. 常驻守护进程模式 (默认)
```bash
python3 balance_bot.py
```
- **机制**：启动后，脚本会首先尝试获取 PID 文件锁（防止多实例运行），然后进入无限循环。
- **运行逻辑**：
  1. 启动时执行置顶消息清理与恢复逻辑。
  2. 每隔 `INTERVAL_SECONDS` 秒执行一次余额查询和状态更新。
  3. 通过修改已有的置顶消息更新内容。
- **推荐场景**：生产环境作为 systemd 守护进程长期后台运行。

### 2. 单次执行模式 (`--once`)
```bash
python3 balance_bot.py --once
```
- **机制**：不加 PID 锁，直接读取配置更新一次 Telegram 置顶消息后立即退出。
- **运行逻辑**：
  1. 读取本地消息 ID 缓存。
  2. 查询一次 DeepSeek 余额并获取系统状态。
  3. 编辑更新置顶消息（若无历史消息则新建并置顶）。
  4. 退出程序。
- **推荐场景**：首次部署测试、结合外部 `cron` 定时任务运行。

---

## Quick Start (快速开始)

### 1. Prerequisites (环境要求)

- **Linux** 服务器（推荐 Debian / Ubuntu）
- **Python ≥ 3.8**
- **systemd**（用于配置开机自启守护进程）

### 2. Create a Telegram Bot (创建 Telegram 机器人)

1. 在 Telegram 中私聊 [@BotFather](https://t.me/botfather)，发送 `/newbot` 指令。
2. 按照提示输入机器人的名字和用户名。
3. 创建成功后，保存 BotFather 返回的 **Token**，格式类似于：
   ```text
   123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
   ```
4. 将你的机器人拉入目标群组/频道，或者直接向它发送一条消息。

#### 获取 Chat ID
在浏览器或终端中访问以下 URL（注意将 `<YOUR_TOKEN>` 替换为上一步获取的 Token，保留前面的 `bot` 字符）：
```text
https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates
```
在返回的 JSON 数据中，找到 `chat` 下的 `id` 字段（通常是一串负数或正数数字），这就是你的 `TELEGRAM_CHAT_ID`。

### 3. Clone & Configure (克隆与配置)

根据你是**首次安装**还是**更新已有的版本**，选择以下相应的步骤：

#### 选项 A：首次安装
使用 `sudo` 将项目克隆到 `/opt` 目录，并**立即修改目录所有者**为当前用户，以防止后续测试和 Hook 写入文件时遭遇权限不足错误：
```bash
sudo mkdir -p /opt
sudo git clone https://github.com/YOUR_USER/deepseek-balance-bot.git /opt/deepseek-balance-bot
# 修改所有者为当前非 root 用户，避免权限问题
sudo chown -R $USER:$USER /opt/deepseek-balance-bot
cd /opt/deepseek-balance-bot
cp .env.example .env
```

#### 选项 B：更新已有版本
如果此前已经在 `/opt` 中克隆了该项目，请**不要**重复运行 `git clone`，直接进入目录拉取最新代码即可：
```bash
cd /opt/deepseek-balance-bot
git pull
```
> 💡 **提示**：如果是之前使用 `sudo` 部署导致现在有权限报错，可以随时运行 `sudo chown -R $USER:$USER /opt/deepseek-balance-bot` 来修复权限。


使用编辑器（如 `nano` 或 `vi`）修改 `.env` 配置文件：
```bash
nano .env
```

| 变量名 | 必填 | 说明 | 默认值 |
|----------|----------|-------------|---------|
| `DEEPSEEK_API_KEY` | ✅ | DeepSeek 开放平台 API Key | — |
| `TELEGRAM_BOT_TOKEN` | ✅ | Telegram Bot Token (包含 `bot` 前缀的完整 Token) | — |
| `TELEGRAM_CHAT_ID` | ✅ | 接收消息的 Telegram 聊天 ID (数字) | — |
| `INTERVAL_SECONDS` | ❌ | 轮询更新间隔（秒） | `300` (5分钟) |
| `TIMEZONE_OFFSET` | ❌ | 时区偏移（小时），北京时间填 `8` | `8` |
| `MONITOR_SERVICES` | ❌ | 需要监控的 systemd 服务列表 | `SS:shadowsocks-rust,Bot:deepseek-balance-bot` |
| `RETRY_COUNT` | ❌ | DeepSeek 余额查询失败时的重试次数 | `3` |
| `RETRY_INTERVAL` | ❌ | 重试之间的等待间隔（秒） | `5` |

> 💡 **提示**：DeepSeek API Key 可以在 [platform.deepseek.com](https://platform.deepseek.com/) 的 **API Keys** 菜单中生成。密钥生成时仅展示一次，请务必及时保存。

### 4. Test Run (测试运行)

配置完成后，进行单次运行测试：

```bash
python3 balance_bot.py --once
```

**预期控制台输出**：
```text
未找到已保存的消息 ID，将创建新消息。
正在创建新的置顶消息...
新消息已创建，ID：456
```

此时检查 Telegram 聊天窗口，应该会看到发送成功的第一条余额消息，并且该消息已被自动置顶。

### 5. Register as a System Service (注册为系统服务)

配置开机自启及守护进程管理：

```bash
# 复制服务模板到系统目录
sudo cp deepseek-balance-bot.service /etc/systemd/system/
# 重载系统服务配置
sudo systemctl daemon-reload
# 设置开机自启并立即启动
sudo systemctl enable deepseek-balance-bot
sudo systemctl start deepseek-balance-bot
```

**检查运行状态**：
```bash
sudo systemctl status deepseek-balance-bot
```

---

## Detailed Mechanics (核心运行机制说明)

### 1. PID 单例锁限制
为了防止在同一台服务器上因多次手动执行或配置错误导致多个常驻后台进程同时运行，脚本在启动时会在工作目录下创建 `balance_bot.pid` 文件。
- 启动时会检查该文件，如果发现已登记的位置上对应的 PID 进程仍处于存活状态，将**拒绝启动**并安全退出。
- 发生 `KeyboardInterrupt` 退出、接收到系统终止信号（`SIGTERM`，例如 `systemctl stop/restart` 服务）或正常停止服务时，脚本均会捕获并触发 `finally` 清理逻辑，自动删除 PID 文件，杜绝了服务重启时的锁残留问题。

### 2. 置顶消息防重与恢复
为了防止每次服务重启都在 Telegram 中发一条新消息，导致历史消息堆积和重复置顶，脚本实现了以下恢复逻辑：
1. **本地缓存恢复**：首先尝试从本地的 `tg_msg_id.txt` 中读取上一次成功发送并置顶的消息 ID。
2. **云端置顶核对**：
   - 脚本通过 `getChat` 接口获取当前 Telegram 聊天中实际置顶的消息。
   - 如果发现当前置顶消息的发送者是本 Bot，且消息内容包含 `💰` 符号，脚本会自动更新本地的缓存为该置顶消息 ID。
   - 如果本地存在有效的置顶消息 ID，但因为其他人置顶了别的内容导致余额消息被顶替，Bot 会自动将原先的余额消息重新置顶。
3. **多余置顶清理**：在启动以及创建新消息前，脚本会主动调用 `unpinAllChatMessages` 清空当前聊天中可能存在的其他置顶信息，保证整个聊天有且仅有一条最新的余额置顶消息。
4. **失效自动清理**：如果当前置顶的消息更新编辑失败（例如已被手动删除、或由于超过 Telegram 限制无法编辑），Bot 会在发送新置顶消息前，自动调用 `deleteMessage` 擦除并清理掉旧的余额消息卡片，确保聊天历史干净无残留。

### 3. systemd 服务监控
配置在 `MONITOR_SERVICES` 中的服务列表会由脚本定期通过执行 `systemctl is-active --quiet <service_name>` 命令进行探测：
- 返回码为 `0` 时判定为活跃，显示为 🟢 绿灯。
- 返回码非 `0` 时判定为宕机，显示为 🔴 红灯。
- 出现检测异常（如无权限或服务不存在）时，显示为 ⚪ 灰灯。

---

## Operations (运维与维护)

### View Logs (查看日志)

由于优化了服务文件的日志流机制，脚本的控制台输出已原生对接 systemd 的 `journald` 收集器。您可以使用标准指令查看、追踪日志：

```bash
# 实时滚动追踪最新日志
sudo journalctl -u deepseek-balance-bot -f

# 查看最后 50 行日志（不分页）
sudo journalctl -u deepseek-balance-bot -n 50 --no-pager
```

### Common Commands (常用维护命令)

```bash
# 重新启动服务
sudo systemctl restart deepseek-balance-bot

# 停止服务运行
sudo systemctl stop deepseek-balance-bot

# 禁用开机自启
sudo systemctl disable deepseek-balance-bot
```

### Git Auto-Restart Hook (Git 自动更新并重启)

项目内附带了一个 Git Post-Merge 钩子，可在您执行 `git pull` 合并代码后，自动检测并重启常驻的 systemd 服务。配置方法如下：

```bash
# 建立软链接（若提示权限不足，请使用 sudo）
sudo ln -sf ../../githook-post-merge.sh .git/hooks/post-merge
sudo chmod +x .git/hooks/post-merge
```

---

## Project Structure (项目结构)

```text
deepseek-balance-bot/
├── balance_bot.py                # 核心 Python 脚本
├── deepseek-balance-bot.service  # systemd 服务配置文件
├── githook-post-merge.sh         # Git 代码合并后自动重启 Hook
├── .env.example                  # 环境变量配置模板
├── tg_msg_id.txt                 # 本地缓存的消息 ID（自动生成）
└── balance_bot.pid               # 守护进程单例 PID 锁（自动生成）
```

---

## FAQ (常见问题解答)

<details>
<summary><b>启动时提示 "Another instance is already running..." (已有实例在运行)</b></summary>

这通常是因为先前程序非正常关闭，残留了 PID 锁文件。
1. 首先确认当前是否真的没有 `balance_bot` 进程在后台运行：
   ```bash
   ps aux | grep balance_bot.py
   ```
2. 确认没有运行后，删除残留的 PID 文件即可：
   ```bash
   rm -f /opt/deepseek-balance-bot/balance_bot.pid
   ```

</details>

<details>
<summary><b>Telegram 消息始终显示 "❌ 错误"</b></summary>

这意味着余额查询请求未通过。请依次检查：
1. `.env` 中的 `DEEPSEEK_API_KEY` 是否正确且有效（可前往平台 Billing 页面核对余额）。
2. 服务器是否能够正常访问 DeepSeek 接口：
   ```bash
   curl -I https://api.deepseek.com/user/balance
   ```
3. 检查 `.env` 配置项是否有多余的空格或双引号。

</details>

<details>
<summary><b>置顶消息长时间不更新</b></summary>

请检查以下几项：
1. 运行日志是否有报错（使用 `sudo journalctl -u deepseek-balance-bot -n 100` 查看）。
2. 机器人是否已被移出群组，或被设置了“禁止发送/置顶消息”的权限。
3. 检查服务器网络是否可达 Telegram API 服务器：
   ```bash
   curl -I https://api.telegram.org
   ```

</details>

<details>
<summary><b>如何调整监控刷新频率？</b></summary>

修改 `.env` 中的 `INTERVAL_SECONDS` 参数，然后重启服务生效：
```ini
INTERVAL_SECONDS=600   # 修改为每 10 分钟刷新一次
```
```bash
sudo systemctl restart deepseek-balance-bot
```

</details>

---

## License (开源协议)

[MIT](LICENSE)
