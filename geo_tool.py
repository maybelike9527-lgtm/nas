import requests
import logging

logger = logging.getLogger("NAS_Manager")


def process_location_update(latitude, longitude):
    """
    由 main.py 接收座標後傳入此處處理
    回傳：(成功與否, 地區名稱或錯誤訊息)
    """
    # 使用 OpenStreetMap 的 Reverse Geocoding
    url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={latitude}&lon={longitude}&addressdetails=1"
    headers = {'User-Agent': 'NAS_Bot_Manager_v1'}

    try:
        resp = requests.get(url, headers=headers, timeout=10).json()
        address = resp.get('address', {})

        # 提取台灣縣市與鄉鎮資訊
        city = address.get('city') or address.get('county') or address.get('state', '')
        town = address.get('suburb') or address.get('town') or address.get('district', '')

        if not city:
            return False, "無法辨識該座標的行政區劃"

        # 格式化結果 (例如：臺中市大雅區)
        full_name = f"{city}{town}".replace("台", "臺")
        logger.info(f"📍 座標轉換成功：{full_name}")
        return True, full_name

    except Exception as e:
        logger.error(f"座標處理異常: {e}")
        return False, str(e)