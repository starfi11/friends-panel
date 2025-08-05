# core/email_utils.py

import random
import time
from core import config
import smtplib
from email.mime.text import MIMEText

# 简单内存存储（可换为 Redis）
_code_map = {}
EXPIRE_SECONDS = 300  # 5分钟


def generate_code(email: str) -> str:
    code = str(random.randint(100000, 999999))
    _code_map[email] = (code, time.time())
    return code


def check_code(email: str, code: str) -> bool:
    if email not in config.ALLOWED_EMAILS:
        return False
    if email not in _code_map:
        return False
    cached_code, ts = _code_map[email]
    if time.time() - ts > EXPIRE_SECONDS:
        return False
    return cached_code == code


def send_code_email(to_email: str, code: str):
    msg = MIMEText(f"""
    <html>
      <body style="font-family: Arial, sans-serif; line-height: 1.6;">
        <h2 style="color: #2c3e50;">UnderLamp 验证码通知</h2>
        <p>您好，</p>
        <p>您正在进行身份验证，请在 <b>{config.EMAIL_EXPIRE_SECONDS // 60} 分钟</b> 内使用以下验证码完成操作：</p>
        <div style="font-size: 24px; font-weight: bold; color: #e74c3c; margin: 16px 0;">
          {code}
        </div>
        <p>如果您并未请求此验证码，请忽略此邮件。</p>
        <br>
        <p style="font-size: 14px; color: #555;">—— 芦苇软件</p>
        <p style="font-size: 12px; color: #aaa;">UnderLamp · 此邮件由系统自动发送，请勿回复</p>
      </body>
    </html>
    """, "html", "utf-8")

    msg["Subject"] = config.EMAIL_SUBJECT
    msg["From"] = config.EMAIL_FROM
    msg["To"] = to_email

    smtp = smtplib.SMTP_SSL(config.EMAIL_SMTP_SERVER, config.EMAIL_SMTP_PORT)
    smtp.login(config.EMAIL_FROM, config.EMAIL_PASSWORD)
    smtp.sendmail(config.EMAIL_FROM, [to_email], msg.as_string())
    smtp.quit()
