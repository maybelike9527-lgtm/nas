import os
import requests


def get_download_status(ds_instance):
    """
    透過 main.py 傳入的 ds 實體進行查詢，避免重複登入
    """
    if not ds_instance:
        return False, "NAS 未登入"

    api_url = f"http://{os.getenv('NAS_225_IP')}:5000/webapi/DownloadStation/task.cgi"
    params = {
        "api": "SYNO.DownloadStation.Task",
        "version": "1",
        "method": "list",
        "additional": "transfer",  # 必須包含此項才有進度與速度
        "_sid": ds_instance.session._sid
    }

    try:
        resp = requests.get(api_url, params=params, timeout=15).json()
        if not resp.get('success'):
            return False, "無法取得清單"

        tasks = resp.get('data', {}).get('tasks', [])
        waiting_count = 0
        active_list = []

        for t in tasks:
            status = t.get('status')
            if status in ['waiting', 'waiting_extract', 'finishing']:
                waiting_count += 1
            elif status == 'downloading':
                size = t.get('size', 0)
                downloaded = t.get('additional', {}).get('transfer', {}).get('size_downloaded', 0)
                speed_raw = t.get('additional', {}).get('transfer', {}).get('speed_download', 0)

                # 計算格式化數據
                progress = (downloaded / size * 100) if size > 0 else 0
                speed_mb = speed_raw / 1024 / 1024

                active_list.append({
                    "title": t.get('title', '未知檔案'),
                    "progress": f"{progress:.1f}%",
                    "speed": f"{speed_mb:.2f} MB/s"
                })

        return True, {"waiting": waiting_count, "active": active_list}

    except Exception as e:
        return False, str(e)