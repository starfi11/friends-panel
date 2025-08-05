# core/ecs_client.py
# 相关API参考 https://api.aliyun.com/document/Ecs/2014-05-26/StartInstance

import time
import requests
from json import dumps
# tea SDK
from alibabacloud_tea_openapi.models import Config as AliyunOpenAPIConfig
from alibabacloud_ecs20140526.client import Client as ECSClient
from alibabacloud_ecs20140526.models import StartInstanceRequest, StopInstanceRequest, DescribeInstanceStatusRequest
from Tea.exceptions import TeaException


# 创建并返回一个 aliyunECS 的客户端对象，用于之后发起API请求
def create_ecs_client(
    access_key_id: str,
    access_key_secret: str,
    region_id: str
) -> ECSClient:
    conf = AliyunOpenAPIConfig(
        access_key_id=access_key_id,
        access_key_secret=access_key_secret,
        region_id=region_id
    )
    return ECSClient(conf)


# 启动和关闭实例，调用的API接口是异步的，调用后请求服务器状态
def start_ecs_instance(client: ECSClient, instance_id: str):
    print(f"[ECS] 正在启动实例 {instance_id}")
    request = StartInstanceRequest(instance_id=instance_id)
    try:
        response = client.start_instance(request)
        print("[ECS] 启动请求已发送")
        return response.body
    except TeaException as e:
        print(f"[ECS] 启动失败: {e.message}")
        raise


def stop_ecs_instance(
        client: ECSClient,
        instance_id: str,
        force: bool = False,
        mode: str = "StopCharging"
):
    """
    停止 ECS 实例。

    参数：
    - force: 是否强制关机（如无法正常关闭进程时）。
    - mode: 关机模式，支持 "StopCharging"（节省停机）或 "KeepCharging"（普通停机）。
    """
    print(f"[ECS] 正在关闭实例 {instance_id}（mode={mode}, force={force}）")
    request = StopInstanceRequest(
        instance_id=instance_id,
        force_stop=force,
        stopped_mode=mode
    )
    try:
        response = client.stop_instance(request)
        print("[ECS] 停止请求已发送")
        return response.body
    except TeaException as e:
        print(f"[ECS] 停止失败: {e.message}")
        raise


# 查询指定 ECS 实例的状态，只返回状态字符串，如 'Running'、'Stopped' 等
# Starting Running Stopping Stopped ... Pending
def get_ecs_instance_status(client: ECSClient, region_id: str, instance_id: str) -> str:
    #  Tea SDK 某些模型类属性不能直接通过构造函数传递，必须实例化后设置
    request = DescribeInstanceStatusRequest()
    request.region_id = region_id
    request.instance_ids = dumps([instance_id])  # 需要是 JSON 字符串

    try:
        response = client.describe_instance_status(request)
        instance_status_list = response.body.instance_statuses.instance_status
        for status in instance_status_list:
            if status.instance_id == instance_id:
                return status.status
        return "Unknown"
    except TeaException as e:
        print(f"[ECS] 查询失败: {e.message}")
        raise
