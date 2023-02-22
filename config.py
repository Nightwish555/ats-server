import os

from pydantic import BaseSettings
from typing import Union, List

ROOT = os.path.dirname(os.path.abspath(__file__))


class BaseConfig(BaseSettings):
    LOG_DIR = os.path.join(ROOT, 'logs')
    LOG_NAME = os.path.join(LOG_DIR, 'ats.log')

    # server ip port
    SERVER_HOST = "0.0.0.0"
    SERVER_PORT = 7777

    # mock server
    MYSQL_HOST: str
    MYSQL_PORT: int
    MYSQL_USER: str
    MYSQL_PWD: str
    DBNAME: str

    # WARNING: close redis can make job run multiple times at the same time
    REDIS_ON: bool
    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_DB: int
    REDIS_PASSWORD: str
    # Redis连接信息
    REDIS_NODES: List[dict] = []

    # 权限 0 普通用户 1 组长 2 管理员
    MEMBER = 0
    MANAGER = 1
    ADMIN = 2

    # GitHub access_token地址
    GITHUB_ACCESS = "https://github.com/login/oauth/access_token"

    # github获取用户信息
    GITHUB_USER = "https://api.github.com/user"

    AUTH_BACKENDS: dict = {
        "openid": {
            "endpoint": "https://login.netease.com/openid/"
        }
    }

    GITHUB_PARAMS: dict = {
        "client_id": "afcf1b59a82d9608437b",
        "client_secret": "f2af29bffa634f3390f56c047a6fcd894a9d1a21",
    }

    RELATION = "ats_relation"
    MARKDOWN_PATH = os.path.join(ROOT, 'templates', "markdown")

    # 测试报告路径
    REPORT_PATH = os.path.join(ROOT, "templates", "report.html")

    # APP 路径
    APP_PATH = os.path.join(ROOT, "app")

    # dao路径
    DAO_PATH = os.path.join(APP_PATH, 'crud')

    ATS_INFO = "ats_info"
    ATS_ERROR = "ats_error"

    # sqlalchemy
    SQLALCHEMY_DATABASE_URI: str = ''

    # 异步URI
    ASYNC_SQLALCHEMY_URI: str = ''
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    class Config:
        env_file = os.path.join(ROOT, "conf", "dev.env")


Config = BaseConfig()

# 获取ats环境变量
ATS_ENV = os.environ.get("ats_env", "dev")

# init sqlalchemy (used by apscheduler)
Config.SQLALCHEMY_DATABASE_URI = 'mysql+mysqlconnector://{}:{}@{}:{}/{}'.format(
    Config.MYSQL_USER, Config.MYSQL_PWD, Config.MYSQL_HOST, Config.MYSQL_PORT, Config.DBNAME)

# init async sqlalchemy
Config.ASYNC_SQLALCHEMY_URI = f'mysql+aiomysql://{Config.MYSQL_USER}:{Config.MYSQL_PWD}' \
                              f'@{Config.MYSQL_HOST}:{Config.MYSQL_PORT}/{Config.DBNAME}'

BANNER = """
    ___       ______   _____
   /   |     /_  __/  / ___/
  / /| |      / /     \__ \ 
 / ___ |     / /     ___/ / 
/_/  |_|    /_/     /____/  

"""
