from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy import desc

from app.crud.operation.OperationDao import OperationDao
from app.handler.fatcory import AtsResponse
from app.models.operation_log import OperationLog
from app.routers import Permission

router = APIRouter(prefix="/operation")


# 获取用户操作记录
@router.get("/list")
async def list_user_operation(start_time: str, end_time: str, user_id: int, tag: str = None, _=Depends(Permission())):
    try:
        start = datetime.strptime(start_time, "%Y-%m-%d")
        end = datetime.strptime(end_time, "%Y-%m-%d")
        records = await OperationDao.select_list(user_id=user_id, tag=tag, condition=[
            OperationLog.operate_time.between(start, end)], _sort=[desc(OperationLog.operate_time)])
        return AtsResponse.records(records)
    except Exception as e:
        return AtsResponse.failed(e)


# 获取用户操作记录热力图以及参与的项目数量
@router.get("/count")
async def list_user_activities(user_id: int, start_time: str, end_time: str, _=Depends(Permission())):
    try:
        start = datetime.strptime(start_time, "%Y-%m-%d")
        end = datetime.strptime(end_time, "%Y-%m-%d")
        records = await OperationDao.count_user_activities(user_id, start, end)
        ans = list()
        for r in records:
            # 解包日期和数量
            date, count = r
            ans.append(dict(date=date.strftime("%Y-%m-%d"), count=count))
        return AtsResponse.success(ans)
    except Exception as e:
        return AtsResponse.failed(e)
