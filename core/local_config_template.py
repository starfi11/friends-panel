# core/local_config.py

from datetime import timedelta

# 企业微信 Webhook
WECOM_WEBHOOK_URL = ""

# 启动服务器默认运行时间（None 表示不自动关机）
DEFAULT_RUNTIME = timedelta(minutes=60)

# 邮箱白名单
ALLOWED_EMAILS = {
    "example@123.com"
}
WHITE_LIST = {
    "example@123.com"
}
EMAIL_TO_NAME = {
    "example@123.com",
    "example@123.com"
}
# 控制名称（用于群消息）
INSTANCE_NAME = "MC服务器"

# 阿里云配置
ALIYUN_ACCESS_KEY_ID = "xxxx"
ALIYUN_ACCESS_KEY_SECRET = "xxxx"
ALIYUN_REGION_ID = "cn-shanghai"  # 根据你 ECS 所在区域填写
ECS_INSTANCE_ID = "xxxx"  # 你的 ECS 实例 ID

# MCSManager 配置
MCS_API_KEY = "xxxx"

# 具体服务器实例信息
POKEMON_INSTANCE_UUID = "xxxx"
POKEMON_DAEMON_ID = "xxxx"

# MCS 服务地址
MCS_BASE_URL = "xxxx"

# 邮件服务配置（用于发送验证码）
EMAIL_SMTP_SERVER = "smtp.126.com"
EMAIL_SMTP_PORT = 465
EMAIL_FROM = "xxxx"
EMAIL_PASSWORD = "xxxx"  # 使用授权码，而非登录密码
EMAIL_SUBJECT = "xxxx"
EMAIL_EXPIRE_SECONDS = 300

# 阿里云RAM用户策略
# {
#   "Version": "1",
#   "Statement": [
#     {
#       "Effect": "Allow",
#       "Action": [
#         "ecs:StartInstance",
#         "ecs:StopInstance",
#         "ecs:DescribeInstanceStatus"
#       ],
#       "Resource": "*"
#     }
#   ]
# }
