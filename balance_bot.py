import html
import json
import os
import time
from datetime import datetime
from urllib import error, request


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
    time_str = datetime.now().strftime("%H:%M")

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
    """发送一条新消息，并尝试置顶。"""
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
    }

    try:
        result = telegram_post("sendMessage", payload)
        if result.get("ok"):
            msg_id = result["result"]["message_id"]
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
        if not result.get("ok"):
            print(f"置顶消息失败：{result}")
    except (error.URLError, json.JSONDecodeError) as exc:
        print(f"置顶消息失败：{exc}")


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
        return result.get("ok", False)
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

    while True:
        balance = get_deepseek_balance()
        message_text = format_message(balance)

        success = False
        if msg_id:
            success = edit_message(msg_id, message_text)

        if not success:
            print("正在创建新的置顶消息...")
            msg_id = send_new_message(message_text)
            if msg_id:
                save_message_id(msg_id)
        else:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 余额已更新。")

        time.sleep(INTERVAL_SECONDS)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("已停止。")
