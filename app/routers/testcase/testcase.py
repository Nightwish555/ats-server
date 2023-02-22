import json
from datetime import datetime
from typing import List, TypeVar

from fastapi import APIRouter, Depends, UploadFile, File, Request

from app.core.request import get_convertor
from app.core.request.generator import CaseGenerator
from app.crud.project.ProjectRoleDao import ProjectRoleDao
from app.crud.test_case.ConstructorDao import ConstructorDao
from app.crud.test_case.TestCaseAssertsDao import TestCaseAssertsDao
from app.crud.test_case.TestCaseDao import TestCaseDao
from app.crud.test_case.TestCaseDirectory import TestcaseDirectoryDao
from app.crud.test_case.TestCaseOutParametersDao import TestCaseOutParametersDao
from app.crud.test_case.TestReport import TestReportDao
from app.crud.test_case.TestcaseDataDao import TestcaseDataDao
from app.enums.ConvertorEnum import CaseConvertorType
from app.exception.error import AuthError
from app.handler.fatcory import AtsResponse
from app.middleware.RedisManager import RedisHelper
from app.models.out_parameters import TestCaseOutParameters
from app.models.test_case import TestCase
from app.routers import Permission, get_session
from app.schema.constructor import ConstructorForm, ConstructorIndex
from app.schema.testcase_data import TestcaseDataForm
from app.schema.testcase_directory import TestcaseDirectoryForm, MoveTestCaseDto
from app.schema.testcase_out_parameters import TestCaseOutParametersForm, TestCaseParametersDto, \
    TestCaseVariablesDto
from app.schema.testcase_schema import TestCaseAssertsForm, TestCaseForm, TestCaseInfo, TestCaseGeneratorForm

router = APIRouter(prefix="/testcase")
Author = TypeVar("Author", int, str)


@router.get("/list")
async def list_testcase(directory_id: int = None, name: str = "", create_user: str = ''):
    data = await TestCaseDao.list_test_case(directory_id, name, create_user)
    return AtsResponse.success(data)


@router.post("/insert")
async def insert_testcase(data: TestCaseForm, user_info=Depends(Permission())):
    try:
        record = await TestCaseDao.query_record(name=data.name, directory_id=data.directory_id)
        if record is not None:
            return AtsResponse.failed("用例已存在")
        model = TestCase(**data.dict(), create_user=user_info['id'])
        model = await TestCaseDao.insert(model=model, log=True)
        return AtsResponse.success(model.id)
    except Exception as e:
        return AtsResponse.failed(e)


# v2版本创建用例接口
@router.post("/create", summary="创建接口测试用例")
async def create_testcase(data: TestCaseInfo, user_info=Depends(Permission()), session=Depends(get_session)):
    async with session.begin():
        await TestCaseDao.insert_test_case(session, data, user_info['id'])
    return AtsResponse.success()


@router.post("/update")
async def update_testcase(form: TestCaseForm, user_info=Depends(Permission())):
    try:
        data = await TestCaseDao.update_test_case(form, user_info['id'])
        result = await TestCaseOutParametersDao.update_many(form.id, form.out_parameters, user_info['id'])
        return AtsResponse.success(dict(case_info=data, out_parameters=result))
    except Exception as e:
        return AtsResponse.failed(e)


@router.delete("/delete", description="删除测试用例")
async def delete_testcase(id_list: List[int], user_info=Depends(Permission()), session=Depends(get_session)):
    try:
        # 删除case
        async with session.begin():
            await TestCaseDao.delete_records(session, user_info['id'], id_list)
            # 删除断言
            await TestCaseAssertsDao.delete_records(session, user_info['id'], id_list, column="case_id")
            # 删除测试数据
            await TestcaseDataDao.delete_records(session, user_info['id'], id_list, column="case_id")
            return AtsResponse.success()
    except Exception as e:
        return AtsResponse.failed(e)


@router.get("/query")
async def query_testcase(caseId: int, _=Depends(Permission())):
    try:
        data = await TestCaseDao.query_test_case(caseId)
        return AtsResponse.success(AtsResponse.dict_model_to_dict(data))
    except Exception as e:
        return AtsResponse.failed(e)


# @router.get("/list")
# async def query_testcase(user_info=Depends(Permission())):
#     try:
#         projects, _, _ = ProjectDao.list_project(user_info["role"], user_info["id"], 1, 2000)
#         data = TestCaseDao.list_testcase_tree(projects)
#         return dict(code=0, data=data, msg="操作成功")
#     except Exception as e:
#         return dict(code=110, msg=str(e))


@router.post("/asserts/insert")
async def insert_testcase_asserts(data: TestCaseAssertsForm, user_info=Depends(Permission())):
    try:
        new_assert = await TestCaseAssertsDao.insert_test_case_asserts(data, user_id=user_info["id"])
        return AtsResponse.success(new_assert)
    except Exception as e:
        return AtsResponse.failed(e)


@router.post("/asserts/update")
async def update_testcase_asserts(data: TestCaseAssertsForm, user_info=Depends(Permission())):
    try:
        updated = await TestCaseAssertsDao.update_test_case_asserts(data, user_id=user_info["id"])
        return AtsResponse.success(updated)
    except Exception as e:
        return AtsResponse.failed(e)


@router.get("/asserts/delete")
async def delete_testcase_asserts(id: int, user_info=Depends(Permission())):
    await TestCaseAssertsDao.delete_test_case_asserts(id, user_id=user_info["id"])
    return AtsResponse.success()


@router.post("/constructor/insert")
async def insert_constructor(data: ConstructorForm, user_info=Depends(Permission())):
    await ConstructorDao.insert_constructor(data, user_id=user_info["id"])
    return AtsResponse.success()


@router.post("/constructor/update")
async def update_constructor(data: ConstructorForm, user_info=Depends(Permission())):
    await ConstructorDao.update_constructor(data, user_id=user_info["id"])
    return AtsResponse.success()


@router.get("/constructor/delete")
async def delete_constructor(id: int, user_info=Depends(Permission())):
    await ConstructorDao.delete_constructor(id, user_id=user_info["id"])
    return AtsResponse.success()


@router.post("/constructor/order")
async def update_constructor_index(data: List[ConstructorIndex], user_info=Depends(Permission())):
    await ConstructorDao.update_constructor_index(data)
    return AtsResponse.success()


@router.get("/constructor/tree")
async def get_constructor_tree(suffix: bool, name: str = "", user_info=Depends(Permission())):
    result = await ConstructorDao.get_constructor_tree(name, suffix)
    return AtsResponse.success(result)


# 获取数据构造器树
@router.get("/constructor")
async def get_constructor(id: int, user_info=Depends(Permission())):
    result = await ConstructorDao.get_constructor_data(id)
    return AtsResponse.success(result)


# 获取所有数据构造器
@router.get("/constructor/list")
async def list_case_and_constructor(constructor_type: int, suffix: bool):
    ans = await ConstructorDao.get_case_and_constructor(constructor_type, suffix)
    return AtsResponse.success(ans)


# 根据id查询具体报告内容
@router.get("/report")
async def query_report(id: int, user_info=Depends(Permission())):
    report, case_list, plan_name = await TestReportDao.query(id)
    return AtsResponse.success(dict(report=report, plan_name=plan_name, case_list=case_list))


# 获取构建历史记录
@router.get("/report/list")
async def list_report(page: int, size: int, start_time: str, end_time: str, executor: Author = None,
                      _=Depends(Permission())):
    start = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
    end = datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")
    report_list, total = await TestReportDao.list_report(page, size, start, end, executor)
    return AtsResponse.success_with_size(data=report_list, total=total)


# 获取脑图数据
@router.get("/xmind")
async def get_xmind_data(case_id: int, user_info=Depends(Permission())):
    tree_data = await TestCaseDao.get_xmind_data(case_id)
    return AtsResponse.success(tree_data)


# 获取case目录
@router.get("/directory")
async def get_testcase_directory(project_id: int, move: bool = False, user_info=Depends(Permission())):
    # 如果是move，则不需要禁用树
    tree_data, _ = await TestcaseDirectoryDao.get_directory_tree(project_id, move=move)
    return AtsResponse.success(tree_data)


# 获取case目录+case
@router.get("/tree")
async def get_directory_and_case(project_id: int, user_info=Depends(Permission())):
    try:
        tree_data, cs_map = await TestcaseDirectoryDao.get_directory_tree(project_id,
                                                                              TestCaseDao.get_test_case_by_directory_id)
        return AtsResponse.success(dict(tree=tree_data, case_map=cs_map))
    except Exception as e:
        return AtsResponse.failed(e)


@router.get("/directory/query")
async def query_testcase_directory(directory_id: int, user_info=Depends(Permission())):
    try:
        data = await TestcaseDirectoryDao.query_directory(directory_id)
        await ProjectRoleDao.read_permission(data.project_id, user_info["id"], user_info['role'])
        return AtsResponse.success(data)
    except AuthError:
        return AtsResponse.forbidden()
    except Exception as e:
        return AtsResponse.failed(e)


@router.post("/directory/insert")
async def insert_testcase_directory(form: TestcaseDirectoryForm, user_info=Depends(Permission())):
    try:
        await TestcaseDirectoryDao.insert_directory(form, user_info['id'])
        return AtsResponse.success()
    except Exception as e:
        return AtsResponse.failed(e)


@router.post("/directory/update")
async def update_testcase_directory(form: TestcaseDirectoryForm, user_info=Depends(Permission())):
    try:
        await TestcaseDirectoryDao.update_directory(form, user_info['id'])
        return AtsResponse.success()
    except Exception as e:
        return AtsResponse.failed(e)


@router.get("/directory/delete")
async def delete_testcase_directory(id: int, user_info=Depends(Permission())):
    try:
        await TestcaseDirectoryDao.delete_directory(id, user_info['id'])
        return AtsResponse.success()
    except Exception as e:
        return AtsResponse.failed(e)


@router.post("/data/insert")
async def insert_testcase_data(form: TestcaseDataForm, user_info=Depends(Permission())):
    try:
        data = await TestcaseDataDao.insert_testcase_data(form, user_info['id'])
        return AtsResponse.success(data)
    except Exception as e:
        return AtsResponse.failed(e)


@router.post("/data/update")
async def update_testcase_data(form: TestcaseDataForm, user_info=Depends(Permission())):
    try:
        data = await TestcaseDataDao.update_testcase_data(form, user_info['id'])
        return AtsResponse.success(data)
    except Exception as e:
        return AtsResponse.failed(e)


@router.get("/data/delete")
async def delete_testcase_data(id: int, user_info=Depends(Permission())):
    try:
        await TestcaseDataDao.delete_testcase_data(id, user_info['id'])
        return AtsResponse.success()
    except Exception as e:
        return AtsResponse.failed(e)


@router.post("/move", description="移动case到其他目录")
async def move_testcase(form: MoveTestCaseDto, user_info=Depends(Permission())):
    try:
        # 判断是否有移动case的权限
        await ProjectRoleDao.read_permission(form.project_id, user_info["id"], user_info['role'])
        await TestCaseDao.update_by_map(user_info['id'], TestCase.id.in_(form.id_list), directory_id=form.directory_id)
        return AtsResponse.success()
    except AuthError:
        return AtsResponse.forbidden()
    except Exception as e:
        return AtsResponse.failed(e)


@router.post("/parameters/insert")
async def insert_testcase_out_parameters(form: TestCaseParametersDto, user_info=Depends(Permission())):
    query = await TestCaseOutParametersDao.query_record(name=form.name, case_id=form.case_id)
    if query is not None:
        return AtsResponse.failed("参数名称已存在")
    data = TestCaseOutParameters(**form.dict(), user_id=user_info['id'])
    data = await TestCaseOutParametersDao.insert(model=data)
    return AtsResponse.success(data)


@router.post("/parameters/update/batch", summary="批量更新出参数据")
async def update_batch_testcase_out_parameters(case_id: int, form: List[TestCaseOutParametersForm],
                                               user_info=Depends(Permission())):
    result = await TestCaseOutParametersDao.update_many(case_id, form, user_info['id'])
    return AtsResponse.success(result)


@router.post("/parameters/update")
async def update_testcase_out_parameters(form: TestCaseOutParametersForm, user_info=Depends(Permission())):
    data = await TestCaseOutParametersDao.update_record_by_id(user_info['id'], form)
    return AtsResponse.success(data)


@router.get("/parameters/delete")
async def delete_testcase_out_parameters(id: int, user_info=Depends(Permission()), session=Depends(get_session)):
    await TestCaseOutParametersDao.delete_record_by_id(session, id, user_info['id'], log=False)
    return AtsResponse.success()


@router.get("/record/start", summary="开始录制接口请求")  # TODO
async def record_requests(request: Request, regex: str, user_info=Depends(Permission())):
    await RedisHelper.set_address_record(user_info['id'], request.client.host, regex)
    return AtsResponse.success(msg="开始录制，可以在浏览器/app上操作啦！")


@router.get("/record/stop", summary="停止录制接口请求")  # TODO
async def record_requests(request: Request, _=Depends(Permission())):
    await RedisHelper.remove_address_record(request.client.host)
    return AtsResponse.success(msg="停止成功，快去生成用例吧~")


@router.get("/record/status", summary="获取录制接口请求状态")  # TODO
async def record_requests(request: Request, _=Depends(Permission())):
    record = await RedisHelper.get_address_record(request.client.host)
    status = False
    regex = ''
    if record is not None:
        record_data = json.loads(record)
        regex = record_data.get('regex', '')
        status = True
    data = await RedisHelper.list_record_data(request.client.host)
    return AtsResponse.success(dict(data=data, regex=regex, status=status))


@router.get("/record/remove", summary="删除录制接口")  # TODO
async def remove_record(index: int, request: Request, _=Depends(Permission())):
    await RedisHelper.remove_record_data(request.client.host, index)
    return AtsResponse.success()


@router.post("/generate", summary="生成用例")
async def generate_case(form: TestCaseGeneratorForm, user=Depends(Permission()), session=Depends(get_session)):
    if len(form.requests) == 0:
        return AtsResponse.failed("无http请求，请检查参数")
    CaseGenerator.extract_field(form.requests)
    cs = CaseGenerator.generate_case(form.directory_id, form.name, form.requests[-1])
    constructors = CaseGenerator.generate_constructors(form.requests)
    info = TestCaseInfo(constructor=constructors, case=cs)
    async with session.begin():
        ans = await TestCaseDao.insert_test_case(session, info, user['id'])
        return AtsResponse.success(ans)


@router.post("/import", summary="导入har或其他用例数据文件")
async def convert_case(import_type: CaseConvertorType, file: UploadFile = File(...), _=Depends(Permission())):
    convert, file_ext = get_convertor(import_type)
    if convert is None:
        return AtsResponse.failed(f"不支持的导入数据")
    if not file.filename.endswith(f".{file_ext}"):
        return AtsResponse.failed(f"请传入{file_ext}后缀文件")
    requests = convert(file.file)
    return AtsResponse.success(requests)


@router.post("/variables", summary="根据前后置步骤查询变量名", tags=["测试用例"])
async def query_variables(steps: List[TestCaseVariablesDto], session=Depends(get_session)):
    var_list = list()
    await TestCaseDao.query_test_case_out_parameters(session, steps, var_list=var_list)
    return AtsResponse.success(var_list)
