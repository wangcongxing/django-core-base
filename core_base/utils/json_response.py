# -*- coding: utf-8 -*-

"""
@author: 猿小天
@contact: QQ:1638245306
@Created on: 2021/6/2 002 14:43
@Remark: 自定义的JsonResonpse文件
"""

from rest_framework.response import Response


class success_response(Response):
    """
    标准响应成功的返回, SuccessResponse(data)或者SuccessResponse(data=data)
    (1)默认code返回2000, 不支持指定其他返回码
    """

    def __init__(self, data_status=0, data_msg='ok', results=None
                 , http_status=None, headers=None, exception=False, **kwargs):
        # data的初始状态：状态码与状态信息
        data = {
            'code': data_status,
            'msg': data_msg,
        }
        # data的响应数据体
        # results可能是False、0等数据，这些数据某些情况下也会作为合法数据返回
        if results is not None:
            data['data'] = results
        # data响应的其他内容
        # if kwargs is not None:
        #     for k, v in kwargs:
        #         setattr(data, k, v)
        data.update(kwargs)

        # 重写父类的Response的__init__方法
        super().__init__(data=data, status=http_status, headers=headers, exception=exception)


class detail_response(Response):
    """
    不包含分页信息的接口返回,主要用于单条数据查询
    (1)默认code返回2000, 不支持指定其他返回码
    """

    def __init__(self, data=None, msg='success', status=None, template_name=None, headers=None, exception=False,
                 content_type=None,):
        std_data = {
            "code": 0,
            "data": data,
            "msg": msg
        }
        super().__init__(std_data, status, template_name, headers, exception, content_type)


class error_response(Response):
    """
    标准响应错误的返回,ErrorResponse(msg='xxx')
    (1)默认错误码返回400, 也可以指定其他返回码:ErrorResponse(code=xxx)
    """

    def __init__(self, data=None, msg='error', code=400, status=None, template_name=None, headers=None,
                 exception=False, content_type=None):
        std_data = {
            "code": code,
            "data": data,
            "msg": msg
        }
        super().__init__(std_data, status, template_name, headers, exception, content_type)
