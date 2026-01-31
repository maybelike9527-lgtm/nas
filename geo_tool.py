import requests
import logging
import db_manager
import ui_template as ui
import json  # 💡 補上遺漏的導入，否則 send_dept_msg 會崩潰
import os  # 💡 補上遺漏的導入

logger = logging.getLogger("NAS_Manager")


def process(chat_id, msg):
    """
    座標部總處理：自己解析、自己存檔、自己回報
    """
    # 1. 判定訊息內容
    if msg.get("location"):
        loc = msg["location"]
        success, city, town = process_location_update(loc["latitude"], loc["longitude"])

        if success:
            db_manager.save_user_location(chat_id, city, town)
            report = ui.location_success_msg(city, town)
        else:
            report = ui.error_msg(f"定位處理失敗: {town}")

        # 💡 GEO 自己執行回報，不透過 main.py
        send_dept_msg(chat_id, report, ui.get_main_menu_keyboard())
        return

    elif msg.get("text") == "📍 傳送座標":
        # 💡 按鈕觸發後的提示也由 GEO 自己回報
        send_dept_msg(chat_id, f"{ui.ICON_GEO} 正在等待您的位置訊息...", ui.get_main_menu_keyboard())


def send_dept_msg(chat_id, text, keyboard):
    """
    部門專用的發送工具，獨立調用 API 避免循環導入
    """
    token = os.getenv('TELE_TOKEN')
    url = f"https://api.telegram.org/bot{token}/sendMessage"

    # 確保 keyboard 是字典格式以供序列化
    if isinstance(keyboard, list):
        reply_markup = json.dumps({"keyboard": keyboard, "resize_keyboard": True})
    else:
        reply_markup = json.dumps(keyboard)

    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "reply_markup": reply_markup
    }
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        logger.error(f"GEO 發送失敗: {e}")


def process_location_update(latitude, longitude):
    """
    座標轉換邏輯
    """
    url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={latitude}&lon={longitude}&addressdetails=1"
    headers = {'User-Agent': 'NAS_Bot_Manager_v1'}

    try:
        resp = requests.get(url, headers=headers, timeout=10).json()
        address = resp.get('address', {})
        city = address.get('city') or address.get('county') or address.get('state', '')
        town = address.get('suburb') or address.get('town') or address.get('district', '')
        city = city.replace("台", "臺")
        town = town.replace("台", "臺")

        if not city:
            return False, None, "無法辨識縣市"
        return True, city, town
    except Exception as e:
        logger.error(f"座標處理異常: {e}")
        return False, None, str(e)