import asyncio
import uvicorn
from mimetypes import guess_type
from os.path import isfile

from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import Request, WebSocket, WebSocketDisconnect, Depends
from starlette.responses import Response
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates

from app import ats, init_logging
from app.core.msg.wss_msg import WebSocketMessage
from app.core.ws_connection_manager import ws_manage
from app.crud import create_table
from app.crud.notification.NotificationDao import NotificationDao
from app.enums.MessageEnum import MessageStateEnum, MessageTypeEnum
from app.middleware.RedisManager import RedisHelper
from app.routers.auth import user
from app.routers.config import router as config_router
from app.routers.notification import router as msg_router
from app.routers.online import router as online_router
from app.routers.operation import router as operation_router
from app.routers.oss import router as oss_router
from app.routers.project import project
from app.routers.request import http
from app.routers.testcase import router as testcase_router
from app.routers.workspace import router as workspace_router
from app.utils.scheduler import Scheduler
from config import Config, ATS_ENV, BANNER

logger = init_logging()

logger.bind(name=None).opt(ansi=True).success(f"ats is running at <red>{ATS_ENV}</red>")
logger.bind(name=None).success(BANNER)


async def request_info(request: Request):
    logger.bind(name=None).debug(f"{request.method} {request.url}")
    try:
        body = await request.json()
        logger.bind(payload=body, name=None).debug("request_json: ")
    except:
        try:
            body = await request.body()
            if len(body) != 0:
                # 有请求体，记录日志
                logger.bind(payload=body, name=None).debug(body)
        except:
            # 忽略文件上传类型的数据
            pass


# 注册路由
ats.include_router(user.router)
ats.include_router(project.router, dependencies=[Depends(request_info)])
ats.include_router(http.router, dependencies=[Depends(request_info)])
ats.include_router(testcase_router, dependencies=[Depends(request_info)])
ats.include_router(config_router, dependencies=[Depends(request_info)])
ats.include_router(online_router, dependencies=[Depends(request_info)])
ats.include_router(oss_router, dependencies=[Depends(request_info)])
ats.include_router(operation_router, dependencies=[Depends(request_info)])
ats.include_router(msg_router, dependencies=[Depends(request_info)])
ats.include_router(workspace_router, dependencies=[Depends(request_info)])


ats.mount("/statics", StaticFiles(directory="statics"), name="statics")

templates = Jinja2Templates(directory="statics")


@ats.get("/")
async def serve_spa(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@ats.get("/{filename}")
async def get_site(filename):
    filename = './statics/' + filename

    if not isfile(filename):
        return Response(status_code=404)

    with open(filename, mode='rb') as f:
        content = f.read()

    content_type, _ = guess_type(filename)
    return Response(content, media_type=content_type)


@ats.get("/static/{filename}")
async def get_site_static(filename):
    filename = './statics/static/' + filename

    if not isfile(filename):
        return Response(status_code=404)

    with open(filename, mode='rb') as f:
        content = f.read()

    content_type, _ = guess_type(filename)
    return Response(content, media_type=content_type)


@ats.on_event('startup')
async def init_redis():
    """
    初始化redis，失败则服务起不来
    :return:
    """
    try:
        await RedisHelper.ping()
        logger.bind(name=None).success("redis connected success.        ✔")
    except Exception as e:
        if not Config.REDIS_ON:
            logger.bind(name=None).warning(
                f"Redis is not selected, So we can't ensure that the task is not executed repeatedly.        🚫")
            return
        logger.bind(name=None).error(f"Redis connect failed, Please check config.py for redis config.        ❌")
        raise e


@ats.on_event('startup')
def init_scheduler():
    """
    初始化定时任务
    :return:
    """
    # SQLAlchemyJobStore指定存储链接
    job_store = {
        'default': SQLAlchemyJobStore(url=Config.SQLALCHEMY_DATABASE_URI, engine_options={"pool_recycle": 1500},
                                      pickle_protocol=3)
    }
    scheduler = AsyncIOScheduler()
    Scheduler.init(scheduler)
    Scheduler.configure(jobstores=job_store)
    Scheduler.start()
    logger.bind(name=None).success("ApScheduler started success.        ✔")


@ats.on_event('startup')
async def init_database():
    """
    初始化数据库，建表
    :return:
    """
    try:
        asyncio.create_task(create_table())
        logger.bind(name=None).success("database and tables created success.        ✔")
    except Exception as e:
        logger.bind(name=None).error(f"database and tables  created failed.        ❌\nerror: {e}")
        raise


@ats.on_event('shutdown')
def stop_test():
    pass


if __name__ == '__main__':
    uvicorn.run(ats, host=Config.SERVER_HOST, port=Config.SERVER_PORT, reload=False, forwarded_allow_ips="*")
