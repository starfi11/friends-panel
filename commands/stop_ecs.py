# scripts/test_ecs_start.py
from core import config
from core.ecs_client import create_ecs_client, stop_ecs_instance, get_ecs_instance_status

def main():
    # Step 1: 初始化客户端
    client = create_ecs_client(
        access_key_id=config.ALIYUN_ACCESS_KEY_ID,
        access_key_secret=config.ALIYUN_ACCESS_KEY_SECRET,
        region_id=config.ALIYUN_REGION_ID
    )
    # Step 2: 关闭 ECS
    response = stop_ecs_instance(client, config.ECS_INSTANCE_ID)
    print("关闭响应：", response)
if __name__ == '__main__':
    main()
