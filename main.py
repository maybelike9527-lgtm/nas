import os
import json
import time
import logging
from logging.handlers import RotatingFileHandler
import requests
from dotenv import load_dotenv

# 💡 導入您的獨立功能模組與樣式模板
from nas_manager import NASManager
from nas_status import get_download_status
import ui_template as ui
from geo_tool import process_location_update

# ================= 📝 系統與日誌初始化 =================
load_dotenv()

# 設定日誌：同步輸出至檔案與控制台
log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler = RotatingFileHandler('nas_bot.log', maxBytes=5 * 1024 * 1024, backupCount=3, encoding='utf-8')
file_handler.setFormatter(log_formatter)
console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)

logger = logging.getLogger("NAS_Manager")
logger.setLevel(logging.INFO)
logger.addHandler(file_handler)
logger.addHandler(console_handler)

TOKEN = os.getenv('TELE_TOKEN')
MY_CHAT_ID = os.getenv('TELE_CHAT_ID')
user_location_cache = {}

# --- 實例化 NAS 管理器 (負責維持連線 Session) ---
nas_handler = NASManager()

# --- 選單結構定義 ---
MAIN_MENU = [["📥 倉儲部 (NAS)"], ["🌤️ 氣象局", "📍 座標查詢"], ["📊 秘書室"]]
NAS_MENU = [["🚀 新增下載任務", "📊 查詢下載狀態"], ["🏠 回主選單"]]

# 追蹤使用者狀態
user_states = {}


# ================= 🛠️ 核心功能函數 =================

def send_msg(chat_id, text, keyboard=None):
    """確保能同時處理列表選單與包含特殊功能的字典選單"""
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

    # 判斷 keyboard 是否已經是字典格式 (ui.get_main_menu_keyboard 提供)
    if isinstance(keyboard, dict):
        reply_markup = json.dumps(keyboard)
    elif isinstance(keyboard, list):
        reply_markup = json.dumps({"keyboard": keyboard, "resize_keyboard": True})
    else:
        reply_markup = ""

    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "reply_markup": reply_markup
    }
    requests.post(url, json=payload, timeout=10)


def start_listening():
    """啟動監聽迴圈：修正選單按鈕比對與樣式調用"""
    last_update_id = 0
    global user_location_cache

    logger.info("🔥 指揮中樞啟動 (自動座標偵測修正版)")

    while True:
        try:
            url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
            params = {"offset": last_update_id + 1, "timeout": 30}
            resp = requests.get(url, params=params, timeout=40).json()

            for update in resp.get("result", []):
                last_update_id = update["update_id"]
                msg = update.get("message", {})
                chat_id = str(msg.get("chat", {}).get("id"))
                text = msg.get("text", "")

                if chat_id != MY_CHAT_ID:
                    continue

                # --- 1. 座標訊息攔截 (由 UI 傳送座標按鈕觸發) ---
                if msg.get("location"):
                    loc = msg["location"]
                    success, result = process_location_update(loc["latitude"], loc["longitude"])

                    if success:
                        user_location_cache[chat_id] = result
                        # 💡 修正：使用 ui.get_main_menu_keyboard() 確保按鈕不會消失
                        send_msg(chat_id, ui.location_success_msg(result), ui.get_main_menu_keyboard())
                    else:
                        send_msg(chat_id, ui.error_msg(f"定位處理失敗: {result}"), ui.get_main_menu_keyboard())
                    continue

                # --- 2. 處理等待輸入狀態 ---
                if user_states.get(chat_id) == "WAIT_URL":
                    if text == "🏠 回主選單":
                        user_states.pop(chat_id)
                        send_msg(chat_id, ui.welcome_msg(), ui.get_main_menu_keyboard())
                    elif text:
                        success, info = nas_handler.add_download_task(text)
                        msg_text = ui.task_success_msg(text) if success else ui.error_msg(info)
                        send_msg(chat_id, msg_text, ui.NAS_MENU)
                        user_states.pop(chat_id)
                    continue

                # --- 3. 選單按鈕邏輯比對 (需與 ui_template 內容完全一致) ---
                if text in ["/start", "🏠 回主選單"]:
                    send_msg(chat_id, ui.welcome_msg(), ui.get_main_menu_keyboard())

                elif text == "📥 倉儲部 (NAS)":
                    send_msg(chat_id, ui.format_header("倉儲部控制面板"), ui.NAS_MENU)

                elif text == "🚀 新增下載任務":
                    user_states[chat_id] = "WAIT_URL"
                    send_msg(chat_id, ui.format_header("請貼上網址或磁力連結"), ui.NAS_MENU)

                elif text == "📊 查詢下載狀態":
                    success, data = get_download_status(nas_handler.ds)
                    if success:
                        msg_text = ui.status_report_msg(data['waiting'], data['active'])
                    else:
                        msg_text = ui.error_msg(data)
                    send_msg(chat_id, msg_text, ui.NAS_MENU)

                # 💡 修正：按鈕名稱需對應 ui_template 內的 "📍 傳送座標"
                elif text == "📍 傳送座標":
                    send_msg(chat_id, f"{ui.ICON_GEO} 正在等待您的位置訊息...", ui.get_main_menu_keyboard())

                elif text == "🌤️ 氣象局":
                    loc_name = user_location_cache.get(chat_id)
                    if loc_name:
                        send_msg(chat_id, f"🌤️ <b>即時氣象查詢</b>\n當前地區：<code>{loc_name}</code>\n(功能開發中...)",
                                 ui.get_main_menu_keyboard())
                    else:
                        send_msg(chat_id, "💡 請先點擊「📍 傳送座標」以利精確定位。", ui.get_main_menu_keyboard())

        except Exception as e:
            logger.error(f"監聽異常: {e}")
            time.sleep(10)



if __name__ == "__main__":
    start_listening()