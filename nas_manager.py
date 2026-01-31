import os
import logging
import requests
from synology_api import downloadstation

logger = logging.getLogger("NAS_Manager")


class NASManager:
    def __init__(self):
        try:
            # 建立連線並維持 Session
            self.ds = downloadstation.DownloadStation(
                os.getenv('NAS_225_IP'), '5000',
                os.getenv('NAS_225_USER'), os.getenv('NAS_225_PASS'),
                secure=False, cert_verify=False, dsm_version=7
            )
            logger.info("✅ NAS 模組：DS225+ 登入成功")
        except Exception as e:
            logger.error(f"❌ NAS 模組：登入失敗: {e}")
            self.ds = None

    def add_download_task(self, url_text):
        """建立下載任務"""
        if not self.ds:
            return False, "NAS 未連線"

        api_url = f"http://{os.getenv('NAS_225_IP')}:5000/webapi/DownloadStation/task.cgi"
        data = {
            "api": "SYNO.DownloadStation.Task",
            "version": "1",
            "method": "create",
            "uri": url_text,  # 磁力連結與一般網址通用鍵名
            "_sid": self.ds.session._sid
        }

        try:
            resp = requests.post(api_url, data=data, timeout=15).json()
            if resp.get('success'):
                return True, "成功"
            else:
                return False, f"錯誤碼 {resp.get('error', {}).get('code')}"
        except Exception as e:
            return False, str(e)