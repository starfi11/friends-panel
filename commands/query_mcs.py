from core.mcs_client import MCSClient
from core import config
def main():
    client = MCSClient(
        base_url=config.MCS_BASE_URL,
        apikey=config.MCS_API_KEY,
        daemon_id=config.POKEMON_DAEMON_ID,
        instance_uuid=config.POKEMON_INSTANCE_UUID
    )

    status = client.get_instance_status()
    print(f"宝可梦服务器当前状态：{status}")


if __name__ == "__main__":
    main()
