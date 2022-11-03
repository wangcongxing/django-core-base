# -*- coding: utf-8 -*-

"""
@author: 猿小天
@contact: QQ:1638245306
@Created on: 2021/6/3 003 0:30
@Remark: 角色管理
"""
from rest_framework import serializers
from rest_framework.decorators import action

from core_base.models import Role, Menu, MenuButton
from core_base.system.views.Dept import DeptSerializer
from core_base.system.views.Menu import MenuSerializer
from core_base.system.views.MenuButton import MenuButtonSerializer
from core_base.utils.json_response import SuccessResponse
from core_base.utils.serializers import CustomModelSerializer
from core_base.utils.validator import CustomUniqueValidator
from core_base.utils.viewset import CustomModelViewSet
from django_filters import rest_framework as filters
import django_filters
from core_base.utils.json_response import SuccessResponse, ErrorResponse, DetailResponse
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from django.db.models import Count, F, Value
from django.db import models


class RoleSerializer(CustomModelSerializer):
    """
    角色-序列化器
    """

    class Meta:
        model = Role
        fields = "__all__"
        read_only_fields = ["id"]


class RoleInitSerializer(CustomModelSerializer):
    """
    初始化获取数信息(用于生成初始化json文件)
    """

    class Meta:
        model = Role
        fields = ['name', 'key', 'sort', 'status', 'admin', 'data_range', 'remark',
                  'creator', 'dept_belong_id']
        read_only_fields = ["id"]
        extra_kwargs = {
            'creator': {'write_only': True},
            'dept_belong_id': {'write_only': True}
        }


class RoleCreateUpdateSerializer(CustomModelSerializer):
    """
    角色管理 创建/更新时的列化器
    """
    menu = MenuSerializer(many=True, read_only=True)
    dept = DeptSerializer(many=True, read_only=True)
    permission = MenuButtonSerializer(many=True, read_only=True)
    key = serializers.CharField(max_length=50,
                                validators=[CustomUniqueValidator(queryset=Role.objects.all(), message="权限字符必须唯一")])
    name = serializers.CharField(max_length=50, validators=[CustomUniqueValidator(queryset=Role.objects.all())])

    def validate(self, attrs: dict):
        return super().validate(attrs)

    def save(self, **kwargs):
        data = super().save(**kwargs)
        data.dept.set(self.initial_data.get('dept', []))
        data.menu.set(self.initial_data.get('menu', []))
        data.permission.set(self.initial_data.get('permission', []))
        return data

    class Meta:
        model = Role
        fields = '__all__'


class MenuPermissonSerializer(CustomModelSerializer):
    """
    菜单的按钮权限
    """
    menuPermission = MenuButtonSerializer(many=True, read_only=True)

    class Meta:
        model = Menu
        fields = '__all__'


class RoleFilter(filters.FilterSet):
    # 模糊过滤
    name = django_filters.CharFilter(field_name="name", lookup_expr='icontains')

    class Meta:
        model = Role
        fields = ['name']
        search_fields = ('name')  # 允许模糊查询的字段


# 递归获取菜单按钮
def get_child_menu_button(childs):
    children = []
    if childs:
        for child in childs:
            menu_button_list = list(MenuButton.objects.filter(menu=child).values("id", "name", "value"))

            data = {"id": child.id, "name": child.meta.get("title", ""),
                    "children": [], "menu_button_list": menu_button_list,
                    "isPenultimate": True}
            _childs = Menu.objects.filter(parent=child)
            if _childs:
                data["children"] = get_child_menu_button(_childs)

            children.append(data)
    return children


class RoleViewSet(CustomModelViewSet):
    """
    角色管理接口
    list:查询
    create:新增
    update:修改
    retrieve:单例
    destroy:删除
    """
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    create_serializer_class = RoleCreateUpdateSerializer
    update_serializer_class = RoleCreateUpdateSerializer
    filter_class = RoleFilter

    @action(methods=['GET'], detail=True, permission_classes=[])
    def roleId_get_menu(self, request, *args, **kwargs):
        """通过角色id获取该角色用于的菜单"""
        instance = self.get_object()
        queryset = instance.menu.all()
        # queryset = Menu.objects.filter(status=1).all()
        serializer = MenuPermissonSerializer(queryset, many=True)
        return SuccessResponse(data=serializer.data)

    @action(methods=['GET'], detail=False, permission_classes=[])
    def getList(self, request, *args, **kwargs):
        '''
        返回所有角色
        :param request:
        :param args:
        :param kwargs:
        :return:
        '''
        roleResult = Role.objects.filter(status=True).order_by("sort")
        children = [{
            "id": item.id,
            "role": item.key,
            "label": item.name
        } for item in roleResult]
        result = [
            {
                'id': 'root',
                'label': '全部角色',
                'children': children
            },
        ]
        return SuccessResponse(data=result, msg="获取成功")

    # 角色授权
    @action(methods=['get'], detail=False, url_path='actionMenuButton', permission_classes=[IsAdminUser])
    def actionMenuButton(self, request, *args, **kwargs):
        rid = request.GET.get('rid', 0)
        if rid == 0:
            return ErrorResponse(msg='参数不合法请稍后再试')
        result = {}
        tree = []
        menusResult = Menu.objects.filter(status=True, parent=None).order_by('sort')
        for menu in menusResult:
            menu_data = {"id": menu.id, "name": menu.meta.get("title", ""),
                         "children": []}
            childs = Menu.objects.filter(parent=menu).order_by('sort')
            if childs:
                menu_data["children"] = get_child_menu_button(childs)
            tree.append(menu_data)
        role = Role.objects.get(id=rid)
        menuCheckedKeys = role.menu.all().values("id")
        buttonCheckKeys = role.permission.all().values("id")
        deptKeys = role.dept.all().values("id")
        result.update(
            {"tree": tree, 'menuCheckedKeys': [item.get('id') for item in menuCheckedKeys],
             'buttonCheckKeys': [item.get('id') for item in buttonCheckKeys],
             'deptCheckKeys': [item.get('id') for item in deptKeys], 'dataRangeCheckKeys': role.data_range,
             'dataRange': Role.DATASCOPE_CHOICES})
        return DetailResponse(data=result)
