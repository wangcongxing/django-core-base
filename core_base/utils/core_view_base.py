#!/usr/bin/env python
# -*- coding: UTF-8 -*-
'''
@Project ：core_base
@File    ：core_view_base.py
@Author  ：cx
@Date    ：2022/9/15 00:59 
@Desc    ：
'''
# Base类，将增删改查方法重写
# !/usr/bin/env python
# -*- coding:utf-8 -*-
from django.http import QueryDict

import json_response
from rest_framework.response import Response
from rest_framework import status
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from rest_framework import filters
from django_filters import rest_framework
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth.models import User, Group, Permission
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.permissions import IsAuthenticated
import re

# 设置分页
class LargeResultsSetPagination(PageNumberPagination):
    page_size = 10  # 每页显示多少条
    page_size_query_param = 'limit'  # URL中每页显示条数的参数
    page_query_param = 'page'  # URL中页码的参数
    max_page_size = 200  # 最大页码数限制

# 过滤特殊表情符号
def getClearText(text):
    if type(text) == str:
        text = re.sub('["\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF"]', '',
                            text)
    return text

class CustomViewBase(viewsets.ModelViewSet):
    # 注意不是列表（只能有一个分页模式）1
    # pagination_class = PageNumberPagination
    # 自定义分页模式，不要写在base类中，如需要单独配置，请在views中通过继承的方式重写
    pagination_class = LargeResultsSetPagination
    # filter_class = ServerFilter
    # queryset = ''
    # serializer_class = ''
    permission_classes = [IsAdminUser]
    # permission_classes_by_action = {'create': [IsAuthenticated], 'list': [IsAdminUser]}
    # filter_fields = ()
    # search_fields = ()
    filter_backends = (rest_framework.DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter,)

    # 自定义permission_classes_by_action变量,重写get_permissions来给不同的动作设置不同的权限
    permission_classes_by_action = {'default': [IsAuthenticated],
                                    'create': [IsAdminUser],
                                    'update': [IsAdminUser],
                                    'destroy': [IsAdminUser],
                                    'list': [IsAdminUser],
                                    }

    # 重写get_permissions
    def get_permissions(self):
        try:
            # return permission_classes depending on `action`
            return [permission() for permission in self.permission_classes_by_action[self.action]]
        except KeyError:
            # 没用明确权限的话使用默认权限
            # action is not set return default permission_classes
            return [permission() for permission in self.permission_classes_by_action['default']]

    def create(self, request, *args, **kwargs):
        currentUser = request.user
        data = request.data.copy()
        for k,v in data.items():
            data[k] = getClearText(v)
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        serializer.instance.creator = currentUser
        serializer.instance.editor = currentUser
        serializer.instance.save()
        headers = self.get_success_headers(serializer.data)
        return json_response.success_response(0, '操作成功', results=serializer.data, http_status=status.HTTP_200_OK,
                                             headers=headers)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return json_response.success_response(0, '',
                                                 results=serializer.data,
                                                 http_status=status.HTTP_200_OK, **{"count": len(queryset)})

            # return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return json_response.success_response(0, '', results=serializer.data, http_status=status.HTTP_200_OK, )

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return json_response.success_response(0, '', results=serializer.data, http_status=status.HTTP_200_OK, )

    def update(self, request, *args, **kwargs):
        data = request.POST.copy()
        for k,v in data.items():
            data[k] = getClearText(v)
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        instance.editor = request.user
        upFiles = request.FILES
        for f in upFiles:
            data.update({f: upFiles[f]})
        serializer = self.get_serializer(instance, data=data, partial=partial)
        serializer.is_valid(raise_exception=True)

        # serializer.data["editor"] = username
        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a.js queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        return json_response.success_response(0, '操作成功', results=serializer.data, http_status=status.HTTP_200_OK, )

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return json_response.success_response(0, '操作成功',
                                             http_status=status.HTTP_200_OK, )

    # 批量删除
    @action(methods=['delete'], detail=False, url_path='multiple_delete', permission_classes=[IsAdminUser])
    def multiple_delete(self, request, *args, **kwargs):
        delete_id = request.data.get("deleteid", "")
        list_ids = list(filter(None, delete_id.split(',')))
        list_ids = [int(x) for x in list_ids if x.split()]
        self.queryset.model.objects.filter(id__in=list_ids).delete()
        return json_response.success_response(0, "操作成功", results=list_ids)
