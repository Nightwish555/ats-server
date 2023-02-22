import time
from collections import defaultdict
from datetime import datetime

from sqlalchemy import select, asc, or_

from app.crud import Mapper
from app.models import async_session
from app.schema.testcase_directory import TestcaseDirectoryForm
from app.models.testcase_directory import TestcaseDirectory
from app.utils.logger import Log


class TestcaseDirectoryDao(Mapper):
    log = Log("TestcaseDirectoryDao")

    @staticmethod
    async def query_directory(directory_id: int):
        try:
            async with async_session() as session:
                sql = select(TestcaseDirectory).where(TestcaseDirectory.id == directory_id,
                                                         TestcaseDirectory.deleted_at == 0)
                result = await session.execute(sql)
                return result.scalars().first()
        except Exception as e:
            TestcaseDirectoryDao.log.error(f"获取目录详情失败: {str(e)}")
            raise Exception(f"获取目录详情失败: {str(e)}")

    @staticmethod
    async def list_directory(project_id: int):
        try:
            async with async_session() as session:
                sql = select(TestcaseDirectory) \
                    .where(TestcaseDirectory.deleted_at == 0,
                           TestcaseDirectory.project_id == project_id) \
                    .order_by(asc(TestcaseDirectory.name))
                result = await session.execute(sql)
                return result.scalars().all()
        except Exception as e:
            TestcaseDirectoryDao.log.error(f"获取用例目录失败, error: {e}")
            raise Exception(f"获取用例目录失败, error: {e}")

    @staticmethod
    async def insert_directory(form: TestcaseDirectoryForm, user: int):
        try:
            async with async_session() as session:
                async with session.begin():
                    sql = select(TestcaseDirectory).where(TestcaseDirectory.deleted_at == 0,
                                                             TestcaseDirectory.name == form.name,
                                                             TestcaseDirectory.parent == form.parent,
                                                             TestcaseDirectory.project_id == form.project_id)
                    result = await session.execute(sql)
                    if result.scalars().first() is not None:
                        raise Exception("目录已存在")
                    session.add(TestcaseDirectory(form, user))
        except Exception as e:
            TestcaseDirectoryDao.log.error(f"创建目录失败, error: {e}")
            raise Exception(f"创建目录失败: {e}")

    @staticmethod
    async def update_directory(form: TestcaseDirectoryForm, user: int):
        try:
            async with async_session() as session:
                async with session.begin():
                    sql = select(TestcaseDirectory).where(TestcaseDirectory.id == form.id,
                                                             TestcaseDirectory.deleted_at == 0)
                    result = await session.execute(sql)
                    query = result.scalars().first()
                    if query is None:
                        raise Exception("目录不存在")
                    query.name = form.name
                    query.update_user = user
                    query.updated_at = datetime.now()
        except Exception as e:
            TestcaseDirectoryDao.log.error(f"更新目录失败, error: {e}")
            raise Exception(f"更新目录失败: {e}")

    @staticmethod
    async def delete_directory(id: int, user: int):
        try:
            async with async_session() as session:
                async with session.begin():
                    sql = select(TestcaseDirectory).where(TestcaseDirectory.id == id,
                                                             TestcaseDirectory.deleted_at == 0)
                    result = await session.execute(sql)
                    query = result.scalars().first()
                    if query is None:
                        raise Exception("目录不存在")
                    query.deleted_at = int(time.time() * 1000)
                    query.update_user = user
        except Exception as e:
            TestcaseDirectoryDao.log.error(f"删除目录失败, error: {e}")
            raise Exception(f"删除目录失败: {e}")

    @staticmethod
    async def get_directory_tree(project_id: int, case_node=None, move: bool = False) -> (list, dict):
        """
        通过项目获取目录树
        :param project_id:
        :param case_node:
        :param move:
        :return:
        """
        res = await TestcaseDirectoryDao.list_directory(project_id)
        ans = list()
        ans_map = dict()
        case_map = dict()
        parent_map = defaultdict(list)
        for directory in res:
            if directory.parent is None:
                # 如果没有父亲，说明是最底层数据
                ans.append(dict(
                    title=directory.name,
                    key=directory.id,
                    value=directory.id,
                    label=directory.name,
                    children=list(),
                ))
            else:
                parent_map[directory.parent].append(directory.id)
            ans_map[directory.id] = directory
        # 获取到所有数据信息
        for r in ans:
            await TestcaseDirectoryDao.get_directory(ans_map, parent_map, r.get('key'), r.get('children'), case_map,
                                                        case_node, move)
            if not move and not r.get('children'):
                r['disabled'] = True
        return ans, case_map

    @staticmethod
    async def get_directory(ans_map: dict, parent_map, parent, children, case_map, case_node=None, move=False):
        current = parent_map.get(parent)
        if case_node is not None:
            nodes, cs = await case_node(parent)
            children.extend(nodes)
            case_map.update(cs)
        if current is None:
            return
        for c in current:
            temp = ans_map.get(c)
            if case_node is None:
                child = list()
            else:
                child, cs = await case_node(temp.id)
                case_map.update(cs)
            children.append(dict(
                title=temp.name,
                key=temp.id,
                children=child,
                label=temp.name,
                value=temp.id,
                disabled=len(child) == 0 and not move
            ))
            await TestcaseDirectoryDao.get_directory(ans_map, parent_map, temp.id, child, case_node, move=move)

    @staticmethod
    async def get_directory_son(directory_id: int):
        parent_map = defaultdict(list)
        async with async_session() as session:
            ans = [directory_id]
            # 找出父类为directory_id或者非根的目录
            sql = select(TestcaseDirectory) \
                .where(TestcaseDirectory.deleted_at == 0,
                       or_(TestcaseDirectory.parent == directory_id, TestcaseDirectory.parent != None)) \
                .order_by(asc(TestcaseDirectory.name))
            result = await session.execute(sql)
            data = result.scalars().all()
            for d in data:
                parent_map[d.parent].append(d.id)
            son = parent_map.get(directory_id)
            TestcaseDirectoryDao.get_sub_son(parent_map, son, ans)
            return ans

    @staticmethod
    def get_sub_son(parent_map: dict, son: list, result: list):
        if not son:
            return
        for s in son:
            result.append(s)
            sons = parent_map.get(s)
            if not sons:
                continue
            result.extend(sons)
            TestcaseDirectoryDao.get_sub_son(parent_map, sons, result)
