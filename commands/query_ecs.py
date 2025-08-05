# scripts/test_ecs_start.py
from core import config
from core.ecs_client import create_ecs_client, start_ecs_instance, get_ecs_instance_status

def main():
    # Step 1: 初始化客户端
    client = create_ecs_client(
        access_key_id=config.ALIYUN_ACCESS_KEY_ID,
        access_key_secret=config.ALIYUN_ACCESS_KEY_SECRET,
        region_id=config.ALIYUN_REGION_ID
    )

    # Step 2: 查询 ECS 实例状态
    print("查询启动后 ECS 状态...")
    status = get_ecs_instance_status(client, config.ALIYUN_REGION_ID, config.ECS_INSTANCE_ID)
    print("当前实例状态：", status)

if __name__ == '__main__':
    main()
