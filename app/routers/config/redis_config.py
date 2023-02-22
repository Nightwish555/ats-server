from fastapi import Depends
from starlette.background import BackgroundTasks

from app.crud.config.RedisConfigDao import RedisInfoConfigDao
from app.handler.fatcory import AtsResponse
from app.middleware.RedisManager import RedisInfoManager
from app.models import DatabaseHelper
from app.models.redis_config import RedisInfo
from app.routers import Permission, get_session
from app.routers.config.environment import router
from app.schema.online_redis import OnlineRedisForm
from app.schema.redis_config import RedisConfigForm
from config import Config


@router.get("/redis/list")
async def list_redis_config(name: str = '', addr: str = '', env: int = None,
                            cluster: bool = None, _=Depends(Permission(Config.MEMBER))):
    try:
        data = await RedisInfoConfigDao.select_list(
            name=RedisInfoConfigDao.like(name), addr=RedisInfoConfigDao.like(addr),
            env=env, cluster=cluster
        )
        return AtsResponse.success(data=data)
    except Exception as err:
        return AtsResponse.failed(err)


@router.post("/redis/insert")
async def insert_redis_config(form: RedisConfigForm,
                              user_info=Depends(Permission(Config.ADMIN))):
    try:
        query = await RedisInfoConfigDao.query_record(name=form.name, env=form.env)
        if query is not None:
            raise Exception("数据已存在, 请勿重复添加")
        data = RedisInfo(**form.dict(), user=user_info['id'])
        result = await RedisInfoConfigDao.insert(model=data, log=True)
        return AtsResponse.success(data=result)
    except Exception as err:
        return AtsResponse.failed(err)


@router.post("/redis/update")
async def update_redis_config(form: RedisConfigForm,
                              background_tasks: BackgroundTasks,
                              user_info=Depends(Permission(Config.ADMIN))):
    try:
        result = await RedisInfoConfigDao.update_record_by_id(user_info['id'], form, log=True)
        if result.cluster:
            background_tasks.add_task(RedisInfoManager.refresh_redis_cluster, *(result.id, result.addr))
        else:
            background_tasks.add_task(RedisInfoManager.refresh_redis_client,
                                      *(result.id, result.addr, result.password, result.db))
        return AtsResponse.success(data=result)
    except Exception as err:
        return AtsResponse.failed(err)


@router.get("/redis/delete")
async def delete_redis_config(id: int, background_tasks: BackgroundTasks,
                              user_info=Depends(Permission(Config.ADMIN)), session=Depends(get_session)):
    try:
        ans = await RedisInfoConfigDao.delete_record_by_id(session, user_info['id'], id)
        # 更新缓存
        background_tasks.add_task(RedisInfoManager.delete_client, *(id, ans.cluster))
        return AtsResponse.success()
    except Exception as err:
        return AtsResponse.failed(err)


@router.post("/redis/command")
async def test_redis_command(form: OnlineRedisForm):
    try:
        res = await RedisInfoConfigDao.execute_command(form.command, id=form.id)
        return AtsResponse.success(res)
    except Exception as err:
        return AtsResponse.failed(err)
