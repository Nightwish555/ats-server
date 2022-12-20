import os
from loguru import logger
from pydantic import BaseSettings
from typing import Union

ROOT = os.path.dirname(os.path.abspath(__file__))


class BaseConfig(BaseSettings):
    LOG_DIR = os.path.join(ROOT, 'logs')
    LOG_NAME = os.path.join(LOG_DIR, 'ats.log')

    RDB_HOST: str
    RDB_PORT: int
    RDB_USER: str
    RDB_PASSWD: Union[str, None]
    RDB_DBNAME: str

    AUTH_BACKENDS: dict = {
        "openid": {
            "endpoint": "https://login.netease.com/openid/"
        }
    }

    GITHUB: dict = {
        "client_id": "afcf1b59a82d9608437b",
        "client_secret": "f2af29bffa634f3390f56c047a6fcd894a9d1a21",
        "redirect_uri": "http://your-web-site/login"
    }

    class Config:
        env_file = os.path.join(ROOT, "conf", "dev.env")


Config = BaseConfig()

# 日志输出地方
logger.add(Config.LOG_NAME)
