try:
    import core.local_config as local_config
except ImportError:
    local_config = None

# 配置项列表
_CONFIG_KEYS = [
    "WECOM_WEBHOOK_URL",
    "WHITE_LIST",
    "DEFAULT_RUNTIME",
    "ALLOWED_EMAILS",
    "WHITE_LIST",
    "INSTANCE_NAME",
    "ALIYUN_ACCESS_KEY_ID",
    "ALIYUN_ACCESS_KEY_SECRET",
    "ALIYUN_REGION_ID",
    "ECS_INSTANCE_ID",
    "MCS_API_KEY",
    "MCS_BASE_URL",
    "POKEMON_INSTANCE_UUID",
    "POKEMON_DAEMON_ID",
    "EMAIL_SMTP_SERVER",
    "EMAIL_SMTP_PORT",
    "EMAIL_FROM",
    "EMAIL_PASSWORD",
    "EMAIL_SUBJECT",
    "EMAIL_EXPIRE_SECONDS",
    "EMAIL_TO_NAME",
]

# 批量挂载变量到当前模块命名空间
for key in _CONFIG_KEYS:
    globals()[key] = getattr(local_config, key, None)
