import html
import json
import os
import time
from datetime import datetime, timezone, timedelta
from urllib import error, request


# 时区偏移（小时），可通过环境变量 TIMEZONE_OFFSET 设置，默认 +8（北京时间）
TIMEZONE_OFFSET = int(os.environ.get("TIMEZONE_OFFSET", "8"))


def now_local():
    """返回当前本地时间（根据 TIMEZONE_OFFSET）"""
    tz = timezone(timedelta(hours=TIMEZONE_OFFSET))
    return datetime.now(tz)


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_FILE = os.path.join(BASE_DIR, ".env")
MSG_ID_FILE = os.path.join(BASE_DIR, "tg_msg_id.txt")


def load_dotenv(path=ENV_FILE):
    """Load simple KEY=VALUE pairs from .env without requiring python-dotenv."""
    if not os.path.exists(path):
        return

    with open(path, "r", encoding="utf-8") as file:
        for raw_line in file:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue

            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            os.environ.setdefault(key, value)


load_dotenv()

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")


def read_interval_seconds():
    raw_value = os.getenv("INTERVAL_SECONDS", "300")
    try:
        interval = int(raw_value)
    except ValueError as exc:
        raise RuntimeError("INTERVAL_SECONDS 必须是整数秒数。") from exc

    if interval <= 0:
        raise RuntimeError("INTERVAL_SECONDS 必须大于 0。")
    return interval


INTERVAL_SECONDS = read_interval_seconds()


def require_config():
    missing = [
        name
        for name, value in {
            "DEEPSEEK_API_KEY": DEEPSEEK_API_KEY,
            "TELEGRAM_BOT_TOKEN": TELEGRAM_BOT_TOKEN,
            "TELEGRAM_CHAT_ID": TELEGRAM_CHAT_ID,
        }.items()
        if not value
    ]
    if missing:
        raise RuntimeError(f"缺少必要配置：{', '.join(missing)}。请复制 .env.example 为 .env 后填写。")


def get_deepseek_balance():
    """获取 DeepSeek 账户余额。"""
    url = "https://api.deepseek.com/user/balance"
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Accept": "application/json",
    }

    try:
        http_request = request.Request(url, headers=headers, method="GET")
        with request.urlopen(http_request, timeout=15) as response:
            data = json.loads(response.read().decode("utf-8"))

        balance_infos = data.get("balance_infos") or []
        if data.get("is_available") and balance_infos:
            balance_info = balance_infos[0]
            return {
                "success": True,
                "currency": balance_info.get("currency", "CNY"),
                "total": balance_info.get("total_balance", "0.00"),
                "granted": balance_info.get("granted_balance", "0.00"),
                "topped_up": balance_info.get("topped_up_balance", "0.00"),
            }

        return {"success": False, "error": data.get("message", "余额接口返回不可用")}
    except error.HTTPError as exc:
        return {"success": False, "error": f"HTTP {exc.code}：{exc.reason}"}
    except error.URLError as exc:
        return {"success": False, "error": f"请求失败：{exc}"}
    except json.JSONDecodeError:
        return {"success": False, "error": "DeepSeek 返回的不是有效 JSON"}


def money_symbol(currency):
    if currency == "CNY":
        return "¥"
    if currency == "USD":
        return "$"
    return currency


def format_message(balance_data):
    """格式化发送给 Telegram 的消息。"""
    time_str = now_local().strftime("%H:%M")

    if balance_data["success"]:
        symbol = money_symbol(balance_data["currency"])
        return f"💰 {html.escape(symbol)} {html.escape(str(balance_data['total']))} | {time_str}"

    return f"❌ 错误"


def telegram_post(method, payload):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/{method}"
    body = json.dumps(payload).encode("utf-8")
    http_request = request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with request.urlopen(http_request, timeout=15) as response:
        return json.loads(response.read().decode("utf-8"))


def send_new_message(text):
    """发送一条新消息，先清空旧置顶再置顶新消息。"""
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
    }

    try:
        result = telegram_post("sendMessage", payload)
        if result.get("ok"):
            msg_id = result["result"]["message_id"]
            # 先清空所有置顶，再置顶新的，避免出现多个置顶
            unpin_all()
            pin_message(msg_id)
            return msg_id
        print(f"发送新消息失败：{result}")
    except (error.URLError, json.JSONDecodeError) as exc:
        print(f"发送新消息失败：{exc}")
    return None


def pin_message(message_id):
    """置顶消息。"""
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "message_id": message_id,
        "disable_notification": True,
    }

    try:
        result = telegram_post("pinChatMessage", payload)
        if result.get("ok", False):
            print(f"已置顶消息：{message_id}")
            return True
        else:
            print(f"置顶消息失败：{result}")
            return False
    except (error.URLError, json.JSONDecodeError) as exc:
        print(f"置顶消息失败：{exc}")
        return False


def get_me():
    """返回 bot 的信息（getMe）。"""
    try:
        return telegram_post("getMe", {})
    except (error.URLError, json.JSONDecodeError) as exc:
        print(f"getMe 请求失败：{exc}")
        return None


def unpin_all():
    """取消所有置顶消息，保证只有一条余额消息被置顶。"""
    payload = {"chat_id": TELEGRAM_CHAT_ID}
    try:
        result = telegram_post("unpinAllChatMessages", payload)
        if result.get("ok", False):
            print("已清空所有置顶消息")
            return True
        else:
            print(f"取消置顶失败：{result}")
            return False
    except (error.URLError, json.JSONDecodeError) as exc:
        print(f"取消置顶失败：{exc}")
        return False


def get_chat():
    """获取 chat 信息（包含 pinned_message）。"""
    payload = {"chat_id": TELEGRAM_CHAT_ID}
    try:
        return telegram_post("getChat", payload)
    except (error.URLError, json.JSONDecodeError) as exc:
        print(f"getChat 请求失败：{exc}")
        return None


def delete_message(message_id):
    """删除消息。"""
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "message_id": message_id,
    }

    try:
        result = telegram_post("deleteMessage", payload)
        if result.get("ok", False):
            print(f"消息 {message_id} 已删除")
            return True
        else:
            print(f"删除消息失败：{result}")
            return False
    except (error.URLError, json.JSONDecodeError) as exc:
        print(f"删除消息失败：{exc}")
        return False


def edit_message(message_id, text):
    """编辑已有的置顶消息。"""
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "message_id": message_id,
        "text": text,
        "parse_mode": "HTML",
    }

    try:
        result = telegram_post("editMessageText", payload)
        if result.get("ok", False):
            return True
        else:
            print(f"修改消息失败：{result}")
            return False
    except (error.URLError, json.JSONDecodeError) as exc:
        print(f"修改消息失败：{exc}")
        return False


def load_message_id():
    if not os.path.exists(MSG_ID_FILE):
        return None

    try:
        with open(MSG_ID_FILE, "r", encoding="utf-8") as file:
            return int(file.read().strip())
    except (OSError, ValueError):
        return None


def save_message_id(message_id):
    with open(MSG_ID_FILE, "w", encoding="utf-8") as file:
        file.write(str(message_id))


def main():
    require_config()
    print("DeepSeek 余额监控脚本已启动...")

    msg_id = load_message_id()
    if msg_id:
        print(f"已加载消息 ID：{msg_id}")
    else:
        print("未找到已保存的消息 ID，将创建新消息。")

    # 先清空多余的置顶消息，保证只有一条
    unpin_all()

    # 检查当前聊天的置顶消息，尝试恢复正确的余额消息
    bot_info = get_me()
    bot_id = None
    if bot_info and bot_info.get("ok"):
        bot_id = bot_info["result"].get("id")

    chat_info = get_chat()
    if chat_info and chat_info.get("ok"):
        chat = chat_info["result"]
        pinned = chat.get("pinned_message")
        if pinned:
            pinned_id = pinned.get("message_id")
            # 支持多种来源：直接发送的 from、转发的 forward_from、以及 channel 形式的 sender_chat
            pinned_from = (
                pinned.get("from", {}) or {}
            ).get("id") or (
                pinned.get("forward_from", {}) or {}
            ).get("id") or (
                pinned.get("sender_chat", {}) or {}
            ).get("id")
            pinned_text = pinned.get("text", "") or pinned.get("caption", "") or ""

            # 如果置顶的是 bot 自己发的、且看起来是余额消息，则把本地 msg_id 更新为该消息
            if bot_id and pinned_from == bot_id and "💰" in pinned_text:
                if pinned_id != msg_id:
                    msg_id = pinned_id
                    save_message_id(msg_id)
                    print(f"已恢复并保存置顶余额消息 ID：{msg_id}")
            else:
                # 如果本地有 msg_id，但它未被置顶，尝试再次置顶本地消息
                if msg_id and pinned_id != msg_id:
                    print(f"当前置顶消息不是保存的余额消息，尝试重新置顶本地消息 {msg_id}...")
                    if pin_message(msg_id):
                        print(f"已成功将消息 {msg_id} 置顶")
                    else:
                        # 如果置顶失败，且置顶的消息看起来是余额消息（可能来自其他 bot），则采用该置顶消息
                        if pinned_from and "💰" in pinned_text:
                            msg_id = pinned_id
                            save_message_id(msg_id)
                            print(f"采用现有置顶余额消息 ID：{msg_id}")

    while True:
        balance = get_deepseek_balance()
        message_text = format_message(balance)

        success = False
        if msg_id:
            print(f"尝试编辑消息 {msg_id}...")
            success = edit_message(msg_id, message_text)

        if not success:
            print("正在创建新的置顶消息...")
            msg_id = send_new_message(message_text)
            if msg_id:
                print(f"新消息已创建，ID：{msg_id}")
                save_message_id(msg_id)
        else:
            print(f"[{now_local().strftime('%H:%M:%S')}] 余额已更新。")

        time.sleep(INTERVAL_SECONDS)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("已停止。")
