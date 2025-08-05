# core/wecom.py

import requests
from core import config


def send_wecom_text(text: str) -> bool:
    payload = {
        "msgtype": "text",
        "text": {"content": text}
    }
    try:
        resp = requests.post(config.WECOM_WEBHOOK_URL, json=payload, timeout=5)
        return resp.status_code == 200
    except Exception as e:
        print(f"[WECOM] 文本推送失败: {e}")
        return False


def send_wecom_markdown(content: str) -> bool:
    payload = {
        "msgtype": "markdown",
        "markdown": {"content": content}
    }
    try:
        resp = requests.post(config.WECOM_WEBHOOK_URL, json=payload, timeout=5)
        return resp.status_code == 200
    except Exception as e:
        print(f"[WECOM] Markdown推送失败: {e}")
        return False
