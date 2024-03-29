import os
from datetime import datetime
from decimal import Decimal
from typing import Any

from starlette.background import BackgroundTask
from starlette.responses import FileResponse

from app.handler.encoder import jsonable_encoder


class AtsResponse:

    @staticmethod
    def model_to_dict(obj, *ignore: str):
        if getattr(obj, '__table__', None) is None:
            return obj
        data = dict()
        for c in obj.__table__.columns:
            if c.name in ignore:
                # 如果字段忽略, 则不进行转换
                continue
            val = getattr(obj, c.name)
            if isinstance(val, datetime):
                data[c.name] = val.strftime("%Y-%m-%d %H:%M:%S")
            else:
                data[c.name] = val
        return data

    @staticmethod
    def dict_model_to_dict(obj: Any):
        for k, v in obj.items():
            if isinstance(v, dict):
                AtsResponse.dict_model_to_dict(v)
            elif isinstance(v, list):
                obj[k] = AtsResponse.model_to_list(v)
            else:
                obj[k] = AtsResponse.model_to_dict(v)
        return obj

    @staticmethod
    def json_serialize(obj: Any):
        ans = dict()
        for k, o in dict(obj).items():
            if isinstance(o, set):
                ans[k] = list(o)
            elif isinstance(o, datetime):
                ans[k] = o.strftime("%Y-%m-%d %H:%M:%S")
            elif isinstance(o, Decimal):
                ans[k] = str(o)
            elif isinstance(o, bytes):
                ans[k] = o.decode(encoding='utf-8')
            else:
                ans[k] = o
        return ans

    @staticmethod
    def parse_sql_result(data: list):
        columns = []
        if len(data) > 0:
            columns = list(data[0].keys())
        return columns, [AtsResponse.json_serialize(obj) for obj in data]

    @staticmethod
    def model_to_list(data: list, *ignore: str):
        return [AtsResponse.model_to_dict(x, *ignore) for x in data]

    @staticmethod
    def encode_json(data: Any, *exclude: str):
        return jsonable_encoder(data, exclude=exclude, custom_encoder={
            datetime: lambda x: x.strftime("%Y-%m-%d %H:%M:%S")
        })

    @staticmethod
    def success(data: Any = None, code: int = 200, message: str = "操作成功"):
        return dict(code=code, message=message, data=data, success=True)

    @staticmethod
    def failed(message: Any, code: int = 400, data: Any = None):
        return dict(code=code, message=message, success=False, data=data)

    @staticmethod
    def success_with_size(data: Any = None, code: int = 201, message: str = "操作成功", total: int = 0):
        if data is None:
            return AtsResponse.encode_json(
                dict(code=code, message=message, data={'data': data, 'total': total}, success=True))
        return AtsResponse.encode_json(
            dict(code=code, message=message, data={'data': data, 'total': total}, success=True))

    @staticmethod
    def forbidden():
        return dict(code=403, success=False, msg="对不起, 你没有权限")

    @staticmethod
    def file(filepath, filename):
        return FileResponse(filepath, filename=filename, background=BackgroundTask(lambda: os.remove(filepath)))
