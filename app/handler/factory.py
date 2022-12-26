import os
from datetime import datetime
from decimal import Decimal
from typing import Any


class AtsResponse(object):

    @staticmethod
    def success(data=None, code=0, msg="操作成功", **kwargs):
        return dict(code=code, msg=msg, data=data, **kwargs)

    @staticmethod
    def records(data: list, code=0, msg="操作成功"):
        return dict(code=code, msg=msg, data=PityResponse.model_to_list(data))

    @staticmethod
    def failed(msg, code=110, data=None):
        return dict(code=code, msg=str(msg), data=data)

    @staticmethod
    def forbidden():
        return dict(code=403, msg="对不起, 你没有权限")
