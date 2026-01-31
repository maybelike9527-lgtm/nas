# --- 圖示定義 ---
ICON_HUB = "🏢"
ICON_NAS = "📥"
ICON_WAIT = "⏳"
ICON_SPEED = "🚀"
ICON_SUCCESS = "✅"
ICON_FAIL = "❌"
ICON_INFO = "💡"
ICON_GEO = "📍"

# --- 選單定義 (移至此處以修正 AttributeError) ---
MAIN_MENU = [["📥 倉儲部 (NAS)"], ["🌤️ 氣象局", "📍 座標查詢"], ["📊 秘書室"]]
NAS_MENU = [["🚀 新增下載任務", "📊 查詢下載狀態"], ["🏠 回主選單"]]


def format_header(title):
    """標準化訊息標頭"""
    return f"<b>{ICON_HUB} 【{title}】</b>\n\n"


def welcome_msg(status="正常"):
    """主選單歡迎訊息"""
    return (
        f"{format_header('指揮中樞')}"
        f"{ICON_INFO} 報告老闆，系統目前運作【{status}】。\n"
        f"請從下方選單選擇視察項目。"
    )


def location_success_msg(city, town):
    """座標辨識成功樣式 (支援分開顯示)"""
    return (
        f"{format_header('座標查詢結果')}"
        f"{ICON_GEO} 偵測到您的位置：\n"
        f"<b>{city} {town}</b>\n\n"
        f"{ICON_INFO} 此位置已分區存入資料庫，可精準查詢氣象。"
    )


def task_success_msg(url):
    """任務派發成功樣式"""
    display_url = (url[:40] + '...') if len(url) > 40 else url
    return (
        f"{format_header('任務派發成功')}"
        f"{ICON_SUCCESS} 任務已成功加入隊列\n"
        f"🔗 標的：<code>{display_url}</code>"
    )


def status_report_msg(waiting_count, active_tasks):
    """查詢狀態回報樣式"""
    msg = format_header("倉儲部現況回報")
    msg += f"{ICON_WAIT} <b>等待對列中：</b> {waiting_count} 個任務\n"

    if active_tasks:
        msg += f"\n{ICON_SPEED} <b>正在執行下載：</b>"
        for i, t in enumerate(active_tasks, 1):
            short_title = (t['title'][:20] + '...') if len(t['title']) > 20 else t['title']
            msg += (
                f"\n{i}. <code>{short_title}</code>\n"
                f"   進度：{t['progress']} | 速度：{t['speed']}"
            )
    else:
        msg += f"\n{ICON_INFO} 目前沒有正在下載的任務。"
    return msg

def get_main_menu_keyboard():
    """定義主選單鍵盤，包含自動請求座標按鈕"""
    return {
        "keyboard": [
            [{"text": "📥 倉儲部 (NAS)"}],
            [{"text": "🌤️ 氣象局"}, {"text": "📍 傳送座標", "request_location": True}], # 💡 直接分享座標
            [{"text": "📊 秘書室"}]
        ],
        "resize_keyboard": True
    }

def weather_report_msg(data):
    """產出最終顯示在 Telegram 的 HTML 訊息"""
    return (
        f"🌤️ <b>{data['city']} {data['town']} 天氣預報</b>\n"
        f"📝 狀況：<b>{data['state']}</b>\n"
        f"🌡️ 溫度：<b>{data['temp']}°C</b>\n"
        f"☔ 降雨：<b>{data['rain']}%</b>"
    )

def error_msg(reason):
    """標準錯誤回報樣式"""
    return f"{format_header('系統異常報告')}\n{ICON_FAIL} <b>操作失敗</b>\n原因：{reason}"