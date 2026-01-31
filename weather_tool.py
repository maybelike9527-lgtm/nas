import os
import requests
import urllib3
import db_manager
import ui_template as ui
from datetime import datetime

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def get_final_report(chat_id):
    """氣象部行政窗口：封裝所有邏輯"""
    city, town = db_manager.get_user_location(chat_id)
    if not city:
        return False, "💡 指揮部尚無您的紀錄，請先傳送座標。"

    # 💡 呼叫修正後的查詢邏輯
    success, data = get_weather_info(city, town)
    if success:
        return True, ui.weather_report_msg(data)
    else:
        return False, data


def get_weather_info(city, town):
    """同步成功代碼的解析邏輯"""
    api_key = os.getenv('CWA_API_KEY')

    # 💡 參考成功代碼使用 F-C0032-001 (縣市預報) 確保穩定
    url = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-C0032-001"

    # 💡 參考成功代碼的時間判斷邏輯
    now = datetime.now()
    time_index = 1 if now.hour >= 20 else 0

    try:
        params = {'Authorization': api_key, 'format': 'JSON', 'locationName': city}
        resp = requests.get(url, params=params, timeout=20, verify=False)
        data = resp.json()

        # 💡 同步成功代碼的解析路徑
        if not data.get('records') or not data['records'].get('location'):
            return False, f"氣象局無 {city} 資料。"

        elements = data['records']['location'][0]['weatherElement']

        # 💡 同步成功代碼的字典提取方式
        info = {el['elementName']: el['time'][time_index]['parameter']['parameterName'] for el in elements}

        # 整理回傳格式以對接 ui_template.weather_report_msg
        weather_data = {
            "city": city,
            "town": town,
            "state": info.get('Wx', '未知'),
            "temp": info.get('MinT', 'N/A'),  # 使用低溫作為代表
            "rain": info.get('PoP', '0')
        }

        return True, weather_data
    except Exception as e:
        return False, str(e)