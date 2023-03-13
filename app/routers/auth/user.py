import asyncio

import requests
import traceback
from fastapi import APIRouter, Depends
from starlette import status

from app.core.msg.mail import Email
from app.crud.auth.UserDao import UserDao
from app.exception.request import AuthException
from app.handler.fatcory import AtsResponse
from app.middleware.Jwt import UserToken
from app.routers import Permission, FORBIDDEN
from app.schema.user import UserUpdateForm, UserForm, UserDto, ResetPwdForm
from app.utils.des import Des
from config import Config

router = APIRouter(prefix="/auth")


# router注册的函数都会自带/auth，所以url是/auth/register
@router.post("/register")
async def register(user: UserDto):
    try:
        await UserDao.register_user(**user.dict())
        return AtsResponse.success(message="注册成功, 请登录")
    except Exception:
        return AtsResponse.failed(message=traceback.format_exc())


@router.post("/login")
async def login(data: UserForm):
    try:
        user = await UserDao.login(data.username, data.password)
        user = AtsResponse.model_to_dict(user, "password")
        expire, token = UserToken.get_token(user)
        return AtsResponse.success(data=dict(token=token, user=user, expire=expire), message=f"{data.username}登录成功")
    except Exception:
        return AtsResponse.failed(message=traceback.format_exc())


@router.get('/logout')
async def logout():
    try:
        return AtsResponse.success(message="退出成功")
    except Exception:
        return AtsResponse.failed(message=traceback.format_exc())


@router.get("/listUser")
async def list_users(user_info=Depends(Permission())):
    try:
        user = await UserDao.list_users()
        return AtsResponse.success(user)
    except Exception:
        return AtsResponse.failed(message=traceback.format_exc())


@router.get("/github/login")
async def login_with_github(code: str):
    try:
        code = code.rstrip("#/")
        with requests.Session() as session:
            r = session.get(Config.GITHUB_ACCESS, params=dict(client_id=Config.CLIENT_ID,
                                                              client_secret=Config.SECRET_KEY,
                                                              code=code), timeout=8)
            token = r.text.split("&")[0].split("=")[1]
            res = session.get(Config.GITHUB_USER, headers={"Authorization": "token {}".format(token)}, timeout=8)
            user_info = res.json()
            user = await UserDao.register_for_github(user_info.get("login"), user_info.get("name"),
                                                     user_info.get("email"),
                                                     user_info.get("avatar_url"))
            user = AtsResponse.model_to_dict(user, "password")
            expire, token = UserToken.get_token(user)
            return AtsResponse.success(dict(token=token, user=user, expire=expire), message="登录成功")
    except:
        # 大部分原因是github出问题，忽略
        return AtsResponse.failed(code=110, message="登录超时, 请稍后再试")


@router.post("/update")
async def update_user_info(user_info: UserUpdateForm, user=Depends(Permission(Config.MEMBER))):
    try:
        if user['role'] != Config.ADMIN:
            if user['id'] != user_info.id:
                # 既不是改自己的资料，也不是超管
                return AtsResponse.failed(FORBIDDEN)
            # 如果不是超管，说明是自己改自己，不允许自己改自己的角色
            user_info.role = None
        user = await UserDao.update_user(user_info, user['id'])
        return AtsResponse.success(user)
    except AuthException as e:
        raise e
    except Exception:
        return AtsResponse.failed(message=traceback.format_exc())


@router.get("/query")
async def query_user_info(token: str):
    try:
        if not token:
            raise AuthException(status.HTTP_200_OK, "token不存在")
        user_info = UserToken.parse_token(token)
        user = await UserDao.query_user(user_info['id'])
        if user is None:
            return AtsResponse.failed("用户不存在")
        return AtsResponse.success(user)
    except Exception:
        return AtsResponse.failed(message=traceback.format_exc())


@router.get("/delete")
async def delete_user(id: int, user=Depends(Permission(Config.ADMIN))):
    # 此处要插入操作记录
    try:
        user = await UserDao.delete_user(id, user['id'])
        return AtsResponse.success(user)
    except Exception:
        return AtsResponse.failed(message=traceback.format_exc())


# @router.post("/reset", summary="重置用户密码")
# async def reset_user(form: ResetPwdForm):
#     email = Des.des_decrypt(form.token)
#     await UserDao.reset_password(email, form.password)
#     return AtsResponse.success()
#
#
# @router.get("/reset/generate/{email}", summary="生成重置密码链接")
# async def generate_reset_url(email: str):
#     try:
#         user = await UserDao.query_user_by_email(email)
#         if user is not None:
#             # 说明邮件存在，发送邮件
#             em = Des.des_encrypt(email)
#             link = f"""https://ats.fun/#/user/resetPassword?token={em}"""
#             render_html = Email.render_html(Config.PASSWORD_HTML_PATH, link=link, name=user.name)
#             asyncio.create_task(Email.send_message("重置你的ats密码", render_html, None, email))
#         return AtsResponse.success()
#     except Exception:
#         return AtsResponse.failed(message=traceback.format_exc())


@router.get("/reset/check/{token}", summary="检测生成的链接是否正确")
async def check_reset_url(token: str):
    try:
        email = Des.des_decrypt(token)
        return AtsResponse.success(email)
    except:
        return AtsResponse.failed("重置链接不存在, 请不要无脑尝试")
