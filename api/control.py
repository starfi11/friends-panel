# api/control.py

from fastapi import APIRouter, Form, Request
from fastapi.responses import JSONResponse
from datetime import timedelta
from core import config
from core import actions, server_state
from core.email_utils import send_code_email, check_code, generate_code
from core.server_state import server_state
from fastapi import BackgroundTasks
router = APIRouter()


@router.post("/add-allowed-email")
def add_allowed_email(
    email: str = Form(...),         # 操作人邮箱
    code: str = Form(...),          # 操作人验证码
    target_email: str = Form(...),  # 要加入白名单的邮箱
    target_name: str = Form(...)    # 要添加的用户显示昵称
):
    # 鉴权：是否有权限执行
    if email not in config.WHITE_LIST:
        return JSONResponse(status_code=403, content={"message": "你没有权限添加白名单邮箱"})

    # 验证码校验
    if not check_code(email, code):
        return JSONResponse(status_code=403, content={"message": "邮箱或验证码不正确"})

    # 添加目标邮箱到白名单
    if target_email in config.ALLOWED_EMAILS:
        return {"message": f"{target_email} 已经在ALLOWED_EMAILS中"}

    config.ALLOWED_EMAILS.add(target_email)
    config.EMAIL_TO_NAME[target_email] = target_name

    return {"message": f"{target_email}（{target_name}）已成功加入ALLOWED_EMAILS"}


@router.post("/send-code")
def send_code(email: str = Form(...)):
    if email not in config.ALLOWED_EMAILS:
        return JSONResponse(status_code=403, content={"message": "邮箱不在白名单中"})
    code = generate_code(email)
    send_code_email(email, code)
    return {"message": "验证码已发送，请查收邮件"}


# 调用的start_server会花费很多时间才会返回


@router.post("/start")
def start_server(
        background_tasks: BackgroundTasks,
        email: str = Form(...),
        code: str = Form(...),
        duration: int = Form(...)
):
    if duration not in [30, 60, 90, 120]:
        return JSONResponse(status_code=400, content={"message": "无效的启动时间"})
    if not check_code(email, code):
        return JSONResponse(status_code=403, content={"message": "邮箱或验证码不正确"})

    duration_td = timedelta(minutes=duration)
    background_tasks.add_task(actions.start_server, user_email=email, duration=duration_td)

    return {"message": "服务器启动请求已提交，稍后将完成处理"}


@router.post("/extend")
def extend_server(
    background_tasks: BackgroundTasks,
    email: str = Form(...),
    code: str = Form(...),
    extra_minutes: int = Form(...)
):
    if extra_minutes not in [30, 60]:
        return JSONResponse(status_code=400, content={"message": "只能延长30或60分钟"})
    if not check_code(email, code):
        return JSONResponse(status_code=403, content={"message": "邮箱或验证码不正确"})

    background_tasks.add_task(actions.extend_server, user_email=email, extra_minutes=extra_minutes)
    return {"message": "延长请求已提交，稍后将完成处理"}

# 问题和start一样，调用的shutdown_server会持续很长时间才返回
@router.post("/shutdown")
def shutdown_server(
    background_tasks: BackgroundTasks,
    email: str = Form(...),
    code: str = Form(...)
):
    if not check_code(email, code):
        return JSONResponse(status_code=403, content={"message": "邮箱或验证码不正确"})

    background_tasks.add_task(actions.shutdown_server, user_email=email)
    return {"message": "关机请求已提交，稍后将完成处理"}



@router.get("/status")
def get_status(email: str, code: str):
    if not check_code(email, code):
        return JSONResponse(status_code=403, content={"message": "邮箱或验证码不正确"})

    return server_state.get_status()
