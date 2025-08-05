# test_email.py
# commands/send_email.py 的顶部加入：
from core.email_utils import send_code_email

def main():
    to_email = "starfi11@qq.com"
    test_code = "123456"
    try:
        send_code_email(to_email, test_code)
        print(f"✅ 测试邮件发送成功，已将验证码 {test_code} 发送到 {to_email}")
    except Exception as e:
        print(f"❌ 邮件发送失败: {e}")


if __name__ == "__main__":
    main()
