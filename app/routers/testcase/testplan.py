import asyncio

from apscheduler.jobstores.base import JobLookupError
from fastapi import Depends

from app.core.executor import Executor
from app.crud.test_case.TestPlan import TestPlanDao
from app.handler.fatcory import AtsResponse
from app.schema.test_plan import TestPlanForm
from app.routers import Permission, get_session
from app.routers.testcase.testcase import router
from app.utils.scheduler import Scheduler
from config import Config


@router.get("/plan/list")
async def list_test_plan(page: int, size: int, project_id: int = None, name: str = "", priority: str = '',
                         create_user: int = None, follow: bool = None, user_info=Depends(Permission())):
    try:
        data, total = await TestPlanDao.list_test_plan(page, size, project_id=project_id, name=name,
                                                       follow=follow, priority=priority, role=user_info['role'],
                                                       create_user=create_user, user_id=user_info['id'])

        ans = Scheduler.list_test_plan(data)
        return AtsResponse.success_with_size(ans, total=total)
    except Exception as e:
        return AtsResponse.failed(e)


@router.post("/plan/insert")
async def insert_test_plan(form: TestPlanForm, user_info=Depends(Permission(Config.MANAGER))):
    try:
        plan = await TestPlanDao.insert_test_plan(form, user_info['id'])
        # 添加定时任务
        Scheduler.add_test_plan(plan.id, plan.name, plan.cron)
        return AtsResponse.success()
    except Exception as e:
        return AtsResponse.failed(str(e))


@router.post("/plan/update")
async def update_test_plan(form: TestPlanForm, user_info=Depends(Permission(Config.MANAGER))):
    try:
        await TestPlanDao.update_test_plan(form, user_info['id'], True)
        Scheduler.edit_test_plan(form.id, form.name, form.cron)
        return AtsResponse.success()
    except Exception as e:
        return AtsResponse.failed(str(e))


@router.get("/plan/delete")
async def delete_test_plan(id: int, user_info=Depends(Permission(Config.MANAGER)), session=Depends(get_session)):
    try:
        await TestPlanDao.delete_record_by_id(session, user_info['id'], id)
        Scheduler.remove(id)
    except JobLookupError:
        # 说明没找到job
        pass
    except Exception as e:
        return AtsResponse.failed(str(e))
    return AtsResponse.success()


@router.get("/plan/switch")
async def switch_test_plan(id: int, status: bool, user_info=Depends(Permission(Config.MANAGER))):
    try:
        Scheduler.pause_resume_test_plan(id, status)
        return AtsResponse.success()
    except Exception as e:
        return AtsResponse.failed(str(e))


@router.get("/plan/execute")
async def run_test_plan(id: int, user_info=Depends(Permission(Config.MEMBER))):
    try:
        asyncio.create_task(Executor.run_test_plan(id, user_info['id']))
        return AtsResponse.success("开始执行，请耐心等待")
    except Exception as e:
        return AtsResponse.failed(str(e))


@router.get("/plan/follow", description="关注测试计划")
async def follow_test_plan(id: int, user_info=Depends(Permission(Config.MEMBER))):
    try:
        await TestPlanDao.follow_test_plan(id, user_info['id'])
        return AtsResponse.success(message="关注成功")
    except Exception as e:
        return AtsResponse.failed(str(e))


@router.get("/plan/unfollow", description="取消关注测试计划")
async def unfollow_test_plan(id: int, user_info=Depends(Permission(Config.MEMBER))):
    try:
        await TestPlanDao.unfollow_test_plan(id, user_info['id'])
        return AtsResponse.success(msg="取关成功")
    except Exception as e:
        return AtsResponse.failed(str(e))
