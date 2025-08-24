# scripts/test_ecs_ip.py
from core import config
from core.ecs_client import create_ecs_client, get_ecs_public_ip

def main():
    # Step 1: 初始化客户端
    client = create_ecs_client(
        access_key_id=config.ALIYUN_ACCESS_KEY_ID,
        access_key_secret=config.ALIYUN_ACCESS_KEY_SECRET,
        region_id=config.ALIYUN_REGION_ID
    )

    # Step 2: 查询 ECS 公网 IP
    print("尝试获取 ECS 公网 IP...")
    public_ip = get_ecs_public_ip(client, config.ALIYUN_REGION_ID, config.ECS_INSTANCE_ID)

    if public_ip:
        print(f"实例 {config.ECS_INSTANCE_ID} 的公网 IP：{public_ip}")
    else:
        print(f"实例 {config.ECS_INSTANCE_ID} 未分配公网 IP 或查询失败")

if __name__ == '__main__':
    main()
