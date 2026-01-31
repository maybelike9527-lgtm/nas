import os
import json
import requests
import ui_template as ui
import logging

logger = logging.getLogger("NAS_Manager")


def process(chat_id, msg):
    """
    財務部總處理：處理選單導航與股票邏輯
    """
    text = msg.get("text", "")

    # 1. 進入財務部主選單
    if text == "📊 財務部":
        send_dept_msg(chat_id, f"{ui.ICON_STOCK} <b>進入財務部中心</b>\n請選擇您要視察的業務項目：", ui.STOCK_MENU)
        return

    # 2. 二級功能分流 (目前僅先建立框架)
    elif text == "🔍 查詢股價":
        send_dept_msg(chat_id, f"{ui.ICON_INFO} 請輸入股票代號 (例如：2330)：", ui.STOCK_MENU)

    elif text == "➕ 建立庫存":
        send_dept_msg(chat_id, f"{ui.ICON_INFO} 準備開啟庫存建立程序...", ui.STOCK_MENU)

    elif text == "➖ 刪除庫存":
        send_dept_msg(chat_id, f"{ui.ICON_INFO} 準備開啟庫存刪除程序...", ui.STOCK_MENU)


def send_dept_msg(chat_id, text, keyboard):
    """
    財務部專用自主發報工具
    """
    token = os.getenv('TELE_TOKEN')
    url = f"https://api.telegram.org/bot{token}/sendMessage"

    # 標準化鍵盤格式
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
        logger.error(f"財務部發送失敗: {e}")