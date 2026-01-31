import os
import json
import time
import logging
from logging.handlers import RotatingFileHandler
import requests
from dotenv import load_dotenv

# 💡 導入獨立功能模組與樣式模板
from nas_manager import NASManager
from nas_status import get_download_status
import ui_template as ui
from geo_tool import process_location_update
import db_manager
from weather_tool import get_final_report

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
    """
    啟動監聽迴圈：嚴格執行選單調度原則，禁止在選單層級判斷訊息型態
    """
    last_update_id = 0
    # 啟動時初始化資料庫
    db_manager.init_db()

    logger.info("🔥 指揮中樞啟動 (純選單調度轉接版)")

    while True:
        try:
            # 獲取 Telegram 更新訊息
            url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
            params = {"offset": last_update_id + 1, "timeout": 30}
            resp = requests.get(url, params=params, timeout=40).json()

            for update in resp.get("result", []):
                last_update_id = update["update_id"]
                msg = update.get("message", {})
                chat_id = str(msg.get("chat", {}).get("id"))
                text = msg.get("text", "")

                # 安全檢查：僅限老闆本人存取
                if chat_id != MY_CHAT_ID:
                    continue

                # --- 1. 座標部轉接：禁止型態判斷，由部門內部處理 msg ---
                if text == "📍 傳送座標"or msg.get("location"):
                    import geo_tool
                    # 💡 轉接任務：直接丟給部門，不准在 main 解析經緯度或 location 物件
                    geo_tool.process(chat_id, msg)
                    continue

                # --- 2. 氣象部轉接 ---
                elif text == "🌤️ 氣象局":
                    import weather_tool
                    # 💡 轉接任務：直接向氣象部要報告，不准在 main 讀取資料庫
                    success, report = weather_tool.get_final_report(chat_id)
                    send_msg(chat_id, report if success else ui.error_msg(report), ui.get_main_menu_keyboard())
                    continue

                # --- 3. 處理 NAS 下載任務輸入狀態 ---
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

                # --- 4. 選單按鈕邏輯比對 ---
                if text in ["/start", "🏠 回主選單"]:
                    send_msg(chat_id, ui.welcome_msg(), ui.get_main_menu_keyboard())

                elif text == "📥 倉儲部 (NAS)":
                    send_msg(chat_id, ui.format_header("倉儲部控制面板"), ui.NAS_MENU)

                elif text == "🚀 新增下載任務":
                    user_states[chat_id] = "WAIT_URL"
                    send_msg(chat_id, ui.format_header("請貼上網址或磁力連結"), ui.NAS_MENU)

                elif text == "📊 查詢下載狀態":
                    success, data = get_download_status(nas_handler.ds)
                    send_msg(chat_id, ui.status_report_msg(data['waiting'], data['active']) if success else ui.error_msg(data), ui.NAS_MENU)

        except Exception as e:
            logger.error(f"監聽異常: {e}")
            time.sleep(10)



if __name__ == "__main__":
    db_manager.init_db()
    start_listening()