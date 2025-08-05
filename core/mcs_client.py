# 相关API参考 https://docs.mcsmanager.com/zh_cn/apis/get_apikey.html
import requests


class MCSClient:
    def __init__(self, base_url, apikey, daemon_id, instance_uuid):
        self.base_url = base_url.rstrip('/')
        self.apikey = apikey
        self.daemon_id = daemon_id
        self.instance_uuid = instance_uuid
        self.headers = {
            "X-Requested-With": "XMLHttpRequest",
            "Content-Type": "application/json; charset=utf-8"
        }

    def _get(self, path):
        """统一的GET请求方法，带apikey和通用headers"""
        url = f"{self.base_url}{path}"
        params = {
            "apikey": self.apikey,
            "uuid": self.instance_uuid,
            "daemonId": self.daemon_id
        }
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()

    def get_instance_status(self):
        """获取实例状态，返回：运行中、停止、启动中、停止中、忙碌或未知"""
        result = self._get("/api/instance")
        code_map = {
            -1: "忙碌",
             0: "停止",
             1: "停止中",
             2: "启动中",
             3: "运行中"
        }
        status_code = result.get("data", {}).get("status", -99)
        return code_map.get(status_code, f"未知状态（{status_code}）")

    def start_instance(self):
        """启动实例"""
        return self._get("/api/protected_instance/open")

    def stop_instance(self):
        """关闭实例"""
        return self._get("/api/protected_instance/stop")

    def kill_instance(self):
        """强制终止实例进程"""
        return self._get("/api/protected_instance/kill")

    def restart_instance(self):
        """重启实例"""
        return self._get("/api/protected_instance/restart")
