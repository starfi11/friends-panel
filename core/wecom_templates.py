# core/wecom_templates.py

from datetime import datetime
from typing import Literal, Optional


def build_server_action_message(
    operator: str,
    action: Literal["启动", "关闭", "延长"],
    start_time: Optional[datetime] = None,
    expire_time: Optional[datetime] = None
) -> str:
    """
    构建服务器操作的 markdown 消息内容：
    - 若 operator 存在于 config.EMAIL_TO_NAME 中，显示昵称
    - 否则显示原始邮箱
    """
    from core import config  # 动态加载配置模块

    action_map = {
        "启动": "启动服务器",
        "关闭": "关闭服务器",
        "延长": "延长服务器运行时间"
    }

    # ✅ 使用昵称映射
    display_name = config.EMAIL_TO_NAME.get(operator, operator)

    start_fmt = start_time.strftime("%H:%M") if start_time else "-"
    expire_fmt = expire_time.strftime("%H:%M") if expire_time else "-"
    remaining_minutes = int((expire_time - datetime.now()).total_seconds() // 60) if expire_time else 0

    header = f"**[{action}]** <font color=\"info\">{display_name}</font> 进行了{action_map[action]}操作。\n"
    time_info = ""

    if action in {"启动", "延长"}:
        time_info += f"> 持续时间：<font color=\"comment\">{start_fmt} ~ {expire_fmt}</font>\n"
        time_info += f"> 剩余时长：<font color=\"warning\">{remaining_minutes} 分钟</font>\n"

    return header + time_info
