import asyncio
import time
from copy import deepcopy

from sqlalchemy import select, and_, or_, null

from app.crud import Mapper, ModelWrapper
from app.crud.project.ProjectDao import ProjectDao
from app.enums.OperationEnum import OperationType
from app.models import async_session
from app.models.report import TestReport
from app.models.test_plan import TestPlan
from app.models.testplan_follow_user import TestPlanFollowUserRel
from app.schema.test_plan import TestPlanForm


@ModelWrapper(TestPlan)
class TestPlanDao(Mapper):

    @classmethod
    async def list_test_plan(cls, page: int, size: int, project_id: int = None, name: str = '', priority: str = '',
                             role: str = None, create_user: int = None,
                             user_id: int = None, follow: bool = None):
        try:
            async with async_session() as session:
                conditions = [TestPlan.deleted_at == 0]
                if project_id:
                    TestPlanDao.where(project_id, TestPlan.project_id == project_id, conditions)
                else:
                    # 找出用户能看到的项目
                    projects = await ProjectDao.list_project_id_by_user(session, user_id, role)
                    if projects is None:
                        # 说明用户一个项目都没有，不需要继续查询了
                        return [], 0
                    if len(projects) > 0:
                        cls.where(projects, TestPlan.project_id.in_(projects), conditions)
                cls.where(name, TestPlan.name.like(f"%{name}%"), conditions) \
                    .where(priority, TestPlan.priority == priority, conditions) \
                    .where(create_user, TestPlan.create_user == create_user, conditions)
                if follow is None:
                    sql = select(TestPlan, TestPlanFollowUserRel.id) \
                        .outerjoin(TestPlanFollowUserRel,
                                   and_(
                                       TestPlanFollowUserRel.user_id == user_id,
                                       TestPlanFollowUserRel.deleted_at == 0,
                                       TestPlanFollowUserRel.plan_id == TestPlan.id)) \
                        .where(*conditions)
                elif follow:
                    sql = select(TestPlan, TestPlanFollowUserRel.id) \
                        .outerjoin(TestPlanFollowUserRel,
                                   TestPlanFollowUserRel.plan_id == TestPlan.id,
                                   ).where(*conditions, TestPlanFollowUserRel.user_id == user_id,
                                           TestPlanFollowUserRel.deleted_at == 0)
                else:
                    sql = select(TestPlan, null().label('null_bar')) \
                        .outerjoin(TestPlanFollowUserRel,
                                   TestPlanFollowUserRel.plan_id == TestPlan.id).where(
                        *conditions, or_(TestPlanFollowUserRel.id == None,
                                         TestPlanFollowUserRel.deleted_at != 0))
                result, total = await cls.pagination(page, size, session, sql, False)
                return result, total
        except Exception as e:
            cls.__log__.error(f"获取测试计划失败: {str(e)}")
            raise Exception(f"获取测试计划失败: {str(e)}")

    @staticmethod
    async def insert_test_plan(plan: TestPlanForm, user: int) -> TestPlan:
        try:
            async with async_session() as session:
                async with session.begin():
                    query = await session.execute(select(TestPlan).where(TestPlan.project_id == plan.project_id,
                                                                             TestPlan.name == plan.name,
                                                                             TestPlan.deleted_at == 0))
                    if query.scalars().first() is not None:
                        raise Exception("测试计划已存在")
                    test_plan = TestPlan(**plan.dict(), user=user)
                    session.add(test_plan)
                    await session.flush()
                    await session.refresh(test_plan)
                    session.expunge(test_plan)
                    return test_plan
        except Exception as e:
            TestPlanDao.__log__.error(f"新增测试计划失败: {str(e)}")
            raise Exception(f"添加失败: {str(e)}")

    @classmethod
    async def update_test_plan(cls, plan: TestPlanForm, user: int, log=False):
        try:
            async with async_session() as session:
                async with session.begin():
                    query = await session.execute(
                        select(TestPlan).where(TestPlan.id == plan.id, TestPlan.deleted_at == 0))
                    data = query.scalars().first()
                    if data is None:
                        raise Exception("测试计划不存在")
                    old = deepcopy(data)
                    plan.env = ",".join(map(str, plan.env))
                    plan.receiver = ",".join(map(str, plan.receiver))
                    plan.case_list = ",".join(map(str, plan.case_list))
                    plan.msg_type = ",".join(map(str, plan.msg_type))
                    changed = cls.update_model(data, plan, user)
                    await session.flush()
                    session.expunge(data)
                if log:
                    async with session.begin():
                        await asyncio.create_task(
                            cls.insert_log(session, user, OperationType.UPDATE, data, old, plan.id, changed))
        except Exception as e:
            TestPlanDao.__log__.exception(f"编辑测试计划失败: {str(e)}")
            TestPlanDao.__log__.error(f"编辑测试计划失败: {str(e)}")
            raise Exception(f"编辑失败: {str(e)}")

    @staticmethod
    async def update_test_plan_state(id: int, state: int):
        try:
            async with async_session() as session:
                async with session.begin():
                    query = await session.execute(
                        select(TestPlan).where(TestPlan.id == id, TestPlan.deleted_at == 0))
                    data = query.scalars().first()
                    if data is None:
                        raise Exception("测试计划不存在")
                    data.state = state
                    # await session.flush()
                    # session.expunge(data)
                    # return data
        except Exception as e:
            TestPlanDao.__log__.error(f"编辑测试计划失败: {str(e)}")
            raise Exception(f"编辑失败: {str(e)}")

    @staticmethod
    async def query_test_plan(id: int) -> TestPlan:
        try:
            async with async_session() as session:
                sql = select(TestPlan).where(TestPlan.deleted_at == 0, TestPlan.id == id)
                data = await session.execute(sql)
                return data.scalars().first()
        except Exception as e:
            TestPlanDao.__log__.error(f"获取测试计划失败: {str(e)}")
            raise Exception(f"获取测试计划失败: {str(e)}")

    # @staticmethod
    # async def delete_test_plan(id: int, user: int):
    #     try:
    #         async with async_session() as session:
    #             async with session.begin():
    #                 query = await session.execute(
    #                     select(TestPlan).where(TestPlan.id == id, TestPlan.deleted_at == 0))
    #                 data = query.scalars().first()
    #                 if data is None:
    #                     raise Exception("测试计划不存在")
    #                 DatabaseHelper.delete_model(data, user)
    #     except Exception as e:
    #         TestPlanDao.__log__.error(f"删除测试计划失败: {str(e)}")
    #         raise Exception(f"删除失败: {str(e)}")

    @staticmethod
    async def follow_test_plan(plan_id: int, user_id: int):
        """
        关注测试计划
        :param plan_id:
        :param user_id:
        :return:
        """
        async with async_session() as session:
            async with session.begin():
                sql = select(TestPlanFollowUserRel).where(TestPlanFollowUserRel.deleted_at == 0,
                                                              TestPlanFollowUserRel.plan_id == plan_id,
                                                              TestPlanFollowUserRel.user_id == user_id)
                data = await session.execute(sql)
                ans = data.scalars().first()
                if ans is not None:
                    raise Exception("已关注过此测试计划")
                model = TestPlanFollowUserRel(plan_id, user_id)
                session.add(model)

    @staticmethod
    async def unfollow_test_plan(plan_id: int, user_id: int):
        """
        取关测试计划
        :param plan_id:
        :param user_id:
        :return:
        """
        async with async_session() as session:
            async with session.begin():
                sql = select(TestPlanFollowUserRel).where(TestPlanFollowUserRel.deleted_at == 0,
                                                              TestPlanFollowUserRel.plan_id == plan_id,
                                                              TestPlanFollowUserRel.user_id == user_id)
                data = await session.execute(sql)
                ans = data.scalars().first()
                if ans is None:
                    raise Exception("已取关过此测试计划")
                ans.deleted_at = int(time.time() * 1000)

    @staticmethod
    async def query_user_follow_test_plan(user_id: int):
        """
        根据用户id查询出用户关注的测试计划执行数据
        :param user_id:
        :return:
        """
        ans = []
        async with async_session() as session:
            # 找到最近7次通过率
            sql = select(TestPlan, TestPlanFollowUserRel.id) \
                .outerjoin(TestPlanFollowUserRel,
                           TestPlanFollowUserRel.plan_id == TestPlan.id,
                           ).where(
                TestPlanFollowUserRel.user_id == user_id,
                TestPlanFollowUserRel.deleted_at == 0,
                TestPlan.deleted_at == 0)
            data = await session.execute(sql)
            for d in data.scalars().all():
                reports = list()
                query = await session.execute(select(TestReport).where(TestReport.plan_id == d.id).order_by(
                    TestReport.start_at.desc()).limit(7))
                for report in query.scalars().all():
                    reports.append(report)
                ans.append({
                    "plan": d,
                    "report": reports,
                })
        return ans
