import asyncio
import time
from datetime import datetime, timedelta
from core import ecs_client, server_state, wecom, wecom_templates
from core.ecs_client import create_ecs_client, get_ecs_instance_status, start_ecs_instance, stop_ecs_instance, get_ecs_public_ip
from core.config import (
    ECS_INSTANCE_ID, ALIYUN_REGION_ID, ALIYUN_ACCESS_KEY_ID, ALIYUN_ACCESS_KEY_SECRET,
    MCS_API_KEY, MCS_BASE_URL, POKEMON_DAEMON_ID, POKEMON_INSTANCE_UUID, EMAIL_TO_NAME
)
from core.mcs_client import MCSClient
from core.server_state import server_state
from alibabacloud_ecs20140526.client import Client as ECSClient


def get_display_name(email: str) -> str:
    return EMAIL_TO_NAME.get(email, email)


# 还是先调try_start，false就返回
# 然后开始执行开机逻辑，注意如果ECS已在运行，不管，继续去做MCS的操作，
def start_server(user_email: str, duration: timedelta = None) -> str:
    ok, msg = server_state.try_start()
    if not ok:
        return msg  # 状态不允许启动

    try:
        ecs = create_ecs_client(ALIYUN_ACCESS_KEY_ID, ALIYUN_ACCESS_KEY_SECRET, ALIYUN_REGION_ID)
        mcs = MCSClient(MCS_BASE_URL, MCS_API_KEY, POKEMON_DAEMON_ID, POKEMON_INSTANCE_UUID)

        ecs_status = get_ecs_instance_status(ecs, ALIYUN_REGION_ID, ECS_INSTANCE_ID)
        if ecs_status == "Stopped":
            start_ecs_instance(ecs, ECS_INSTANCE_ID)

            timeout = 120
            while timeout > 0:
                time.sleep(5)
                ecs_status = get_ecs_instance_status(ecs, ALIYUN_REGION_ID, ECS_INSTANCE_ID)
                if ecs_status == "Running":
                    break
                timeout -= 5
            else:
                raise TimeoutError("ECS 启动超时")

        public_ip = get_ecs_public_ip(ecs, ALIYUN_REGION_ID, ECS_INSTANCE_ID)
        ip_text = public_ip if public_ip else "未分配 / 内网不可达"

        # 即便 ECS 已运行，仍继续启动 MCS
        now = datetime.now()
        expire = now + duration if duration else None
        content = wecom_templates.build_server_action_message(user_email, "启动", now, expire)
        wecom.send_wecom_markdown(content)

        time.sleep(30)  # 等待系统服务就绪
        mcs.start_instance()

        timeout = 80
        while timeout > 0:
            time.sleep(5)
            status = mcs.get_instance_status()
            if status == "运行中":
                break
            timeout -= 5
        else:
            raise TimeoutError("MC服务器启动超时")

        start_fmt = datetime.now().strftime('%H:%M')
        expire_fmt = expire.strftime('%H:%M') if expire else "未设置"
        mc_msg = (
            f"**[宝可梦服务器已启动]**\n"
            f"> 启动时间：{start_fmt}\n"
            f"> 持续时间：<font color=\"warning\">{start_fmt} ~ {expire_fmt}</font>"
            f"> 公网 IP：<font color=\"info\">{ip_text}</font>"
        )

        wecom.send_wecom_markdown(mc_msg)

        # 设置启动成功
        server_state.on_start_success(now, expire, server_state.shutdown_callback)

        now_fmt = datetime.now().strftime('%H:%M')
        success_msg = (
            f"**[服务器启动成功]**\n"
            f"> 操作人：{user_email}\n"
            f"> 持续时间：<font color=\"comment\">{now_fmt} ~ {expire_fmt}</font>"
        )

        wecom.send_wecom_markdown(success_msg)

        return "服务器启动成功"

    except Exception as e:
        content = f"**[服务器启动失败]**\n> 操作人：{user_email}\n> 错误信息：{e}"
        wecom.send_wecom_markdown(content)
        server_state.on_start_failed()
        return f"启动失败：{e}"


def extend_server(user_email: str, extra_minutes: int) -> str:
    try:
        # ECS 状态判断
        ecs = create_ecs_client(ALIYUN_ACCESS_KEY_ID, ALIYUN_ACCESS_KEY_SECRET, ALIYUN_REGION_ID)
        ecs_status = get_ecs_instance_status(ecs, ALIYUN_REGION_ID, ECS_INSTANCE_ID)
        if ecs_status != "Running":
            return f"ECS 实例当前状态为【{ecs_status}】，无法延长运行时间"

        # MCS 状态判断
        mcs = MCSClient(MCS_BASE_URL, MCS_API_KEY, POKEMON_DAEMON_ID, POKEMON_INSTANCE_UUID)
        mcs_status = mcs.get_instance_status()
        if mcs_status != "运行中":
            return f"MCS 实例当前状态为【{mcs_status}】，无法延长运行时间"

        # 先尝试状态流转
        ok, msg = server_state.try_extend()
        if not ok:
            return msg

        # 计算新过期时间
        extra = timedelta(minutes=extra_minutes)
        now = datetime.now()
        new_expire = server_state._expire_time + extra if server_state._expire_time else now + extra

        # 延长成功
        server_state.on_extend_success(new_expire, server_state.shutdown_callback)

        content = wecom_templates.build_server_action_message(user_email, "延长", now, new_expire)
        wecom.send_wecom_markdown(content)

        success_msg = f"**[服务器延长成功]**\n> 操作人：{user_email}\n> 延长：{extra_minutes} 分钟\n> 新到期时间：{new_expire.strftime('%H:%M')}"
        wecom.send_wecom_markdown(success_msg)

        return f"成功延长 {extra_minutes} 分钟，新的到期时间为 {new_expire.strftime('%H:%M')}"

    except Exception as e:
        server_state.on_extend_failed()
        content = f"**[运行时间延长失败]**\n> 操作人：{user_email}\n> 错误信息：{e}"
        wecom.send_wecom_markdown(content)
        return f"延长失败：{e}"


def push_ecs_status(client: ECSClient, user_email: str):
    # 获取显示名：存在映射则使用名字，否则显示邮箱
    display_name = EMAIL_TO_NAME.get(user_email, user_email)

    try:
        ecs_status = get_ecs_instance_status(client, ALIYUN_REGION_ID, ECS_INSTANCE_ID)
        color = {
            "Running": "green",
            "Stopped": "red"
        }.get(ecs_status, "comment")

        status_msg = (
            f"**[ECS状态反馈]**\n"
            f"> 操作人：<font color=\"info\">{display_name}</font>\n"
            f"> 当前状态：<font color=\"{color}\">{ecs_status}</font>"
        )
        wecom.send_wecom_markdown(status_msg)

    except Exception as e:
        error_msg = (
            f"**[ECS状态获取失败]**\n"
            f"> 操作人：<font color=\"info\">{display_name}</font>\n"
            f"> 错误信息：{e}"
        )
        wecom.send_wecom_markdown(error_msg)


# 要先使用try_stop，返回值如果为false就直接返回，返回值为真再继续执行下面的关机操作。
# 如果关闭MCS失败，就调用关闭失败函数并返回
# 如果关闭ECS失败，调关闭成功（暂时这样），但要返回相关信息
# 最后调关闭成功
def shutdown_server(user_email: str) -> str:
    # Step 1: 先尝试状态转换
    ok, msg = server_state.try_stop()
    if not ok:
        return msg  # 状态不允许关机

    try:
        mcs = MCSClient(MCS_BASE_URL, MCS_API_KEY, POKEMON_DAEMON_ID, POKEMON_INSTANCE_UUID)
        ecs = create_ecs_client(ALIYUN_ACCESS_KEY_ID, ALIYUN_ACCESS_KEY_SECRET, ALIYUN_REGION_ID)

        # Step 2: 尝试关闭 MCS
        try:
            mcs.stop_instance()
            time.sleep(120)
            mcs.kill_instance()
        except Exception as e:
            content = f"**[MCS关闭异常]**\n> 操作人：{user_email}\n> 错误信息：{e}"
            wecom.send_wecom_markdown(content)
            server_state.on_stop_failed()
            push_ecs_status(ecs, user_email)
            return "MCS关闭失败，服务器状态已回滚"

        time.sleep(5)

        # Step 3: 尝试关闭 ECS
        try:
            stop_ecs_instance(ecs, ECS_INSTANCE_ID, force=False, mode="StopCharging")

            timeout = 90
            while timeout > 0:
                time.sleep(5)
                status = get_ecs_instance_status(ecs, ALIYUN_REGION_ID, ECS_INSTANCE_ID)
                if status == "Stopped":
                    break
                timeout -= 5
            else:
                raise TimeoutError("ECS 停机超时")

        except Exception as e:
            content = f"**[ECS关闭异常]**\n> 操作人：{user_email}\n> 错误信息：{e}"
            wecom.send_wecom_markdown(content)
            server_state.on_stop_success()
            push_ecs_status(ecs, user_email)
            return f"ECS关闭失败，但 MCS 已关闭，服务器已进入停止状态。\n详细信息：{e}"

        # Step 4: 全部成功，发送通知
        now = datetime.now()
        content = wecom_templates.build_server_action_message(user_email, "关闭", now)
        wecom.send_wecom_markdown(content)

        success_msg = f"**[服务器关闭成功]**\n> 操作人：{user_email}\n> 时间：{now.strftime('%H:%M:%S')}"
        wecom.send_wecom_markdown(success_msg)

        server_state.on_stop_success()
        push_ecs_status(ecs, user_email)
        return "服务器已成功关闭"

    except Exception as e:
        content = f"**[服务器关闭失败]**\n> 操作人：{user_email}\n> 错误信息：{e}"
        wecom.send_wecom_markdown(content)
        server_state.on_stop_failed()
        push_ecs_status(ecs, user_email)
        return f"关机失败：{e}"

