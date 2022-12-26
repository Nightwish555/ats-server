import requests

from config import Config
from fastapi import APIRouter, Depends
from app.handler.factory import AtsResponse
from app.crud.user import UserDao

router = APIRouter(prefix="/auth")


@router.post("/register")
async def register():
    ...


@router.post("/login")
async def login():
    ...


@router.get("/github/login")
async def login_with_github(code: str):
    try:
        code = code.rstrip("#/")
        with requests.session() as session:
            r = session.get(Config.GITHUB_ACCESS,
                            params=dict(client_id=Config.GITHUB_PARAMS.get("client_id"),
                                        client_secret=Config.GITHUB_PARAMS.get("client_secret"),
                                        code=code), timeout=8)
            token = r.text.split("&")[0].split("=")[1]
            res = session.get(Config.GITHUB_USER, headers={"Authorization": "token {}".format(token)}, timeout=8)
            user_info = res.json()
            logger.info("User info: %s", user_info)
            await UserDao.set_current_user(user_info['email'], user_info['name'])
            return AtsResponse.success(dict(token=token, user=user_info), msg="登录成功")
    except:
        # 大部分原因是github出问题，忽略
        return AtsResponse.failed(code=110, msg="登录超时, 请稍后再试")
