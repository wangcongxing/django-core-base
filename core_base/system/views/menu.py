# -*- coding: utf-8 -*-
import uuid
from rest_framework import serializers
from rest_framework.decorators import action

from core_base.models import Menu, MenuButton
from core_base.system.views.menu_button import MenuButtonSerializer
from core_base.utils.json_response import SuccessResponse, ErrorResponse
from core_base.utils.serializers import CustomModelSerializer
from core_base.utils.viewset import CustomModelViewSet


class MenuSerializer(CustomModelSerializer):
    """
    菜单表的简单序列化器
    """
    menuPermission = serializers.SerializerMethodField(read_only=True)

    def get_menuPermission(self, instance):
        queryset = instance.menuPermission.order_by('-name').values_list('name', flat=True)
        if queryset:
            return queryset
        else:
            return None

    class Meta:
        model = Menu
        fields = "__all__"
        read_only_fields = ["id"]


class MenuCreateSerializer(CustomModelSerializer):
    """
    菜单表的创建序列化器
    """
    name = serializers.CharField(required=False)

    class Meta:
        model = Menu
        fields = "__all__"
        read_only_fields = ["id"]


class MenuInitSerializer(CustomModelSerializer):
    """
    递归深度获取数信息(用于生成初始化json文件)
    """
    name = serializers.CharField(required=False)
    children = serializers.SerializerMethodField()
    menu_button = serializers.SerializerMethodField()

    def get_children(self, obj: Menu):
        data = []
        instance = Menu.objects.filter(parent_id=obj.id)
        if instance:
            serializer = MenuInitSerializer(instance=instance, many=True)
            data = serializer.data
        return data

    def get_menu_button(self, obj: Menu):
        data = []
        instance = obj.menuPermission.order_by('method')
        if instance:
            data = list(instance.values('name', 'value', 'api', 'method'))
        return data

    def save(self, **kwargs):
        instance = super().save(**kwargs)
        children = self.initial_data.get('children')
        # 菜单表
        if children:
            for menu_data in children:
                menu_data['parent'] = instance.id
                filter_data = {
                    "path": menu_data.get('path', '/'),
                    "name": menu_data.get('name', str(uuid.uuid4().hex)),
                    "component": menu_data.get('component', 'Layout'),
                    "meta": menu_data.get('meta', {}),
                    "sort": menu_data.get('sort', 1000),
                }
                instance_obj = Menu.objects.filter(**filter_data).first()
                if instance_obj and not self.initial_data.get('reset'):
                    continue
                serializer = MenuInitSerializer(instance_obj, data=menu_data, request=self.request)
                serializer.is_valid(raise_exception=True)
                objMenu = serializer.save()
                # 菜单按钮
                menu_button = menu_data.get('menu_button', [])
                if menu_button:
                    for menu_button_data in menu_button:
                        menu_button_data['menu'] = objMenu.id
                        filter_data = {
                            "menu": menu_button_data['menu'],
                            "value": menu_button_data['value']
                        }
                        instance_obj = MenuButton.objects.filter(**filter_data).first()
                        serializer = MenuButtonSerializer(instance_obj, data=menu_button_data, request=self.request)
                        serializer.is_valid(raise_exception=True)
                        serializer.save()
        return instance

    class Meta:
        model = Menu
        fields = ['path', 'name', 'component', 'meta', 'sort', 'parent', 'children', 'menu_button']
        extra_kwargs = {
            'creator': {'write_only': True},
            'dept_belong_id': {'write_only': True}
        }
        read_only_fields = ['id', 'children']


class WebRouterSerializer(CustomModelSerializer):
    """
    前端菜单路由的简单序列化器
    """
    path = serializers.CharField(source="web_path")
    title = serializers.CharField(source="name")
    menuPermission = serializers.SerializerMethodField(read_only=True)
    meta = serializers.SerializerMethodField(read_only=True)

    def get_meta(self, instance):
        return {
            "title": instance.name,
            "icon": instance.icon,
            "breadcrumbHidden": instance.breadcrumb_hidden,
        }

    def get_menuPermission(self, instance):
        # 判断是否是超级管理员
        if self.request.user.is_superuser:
            return instance.menuPermission.values_list('value', flat=True)
        else:
            # 根据当前角色获取权限按钮id集合
            permissionIds = self.request.user.role.values_list('permission', flat=True)
            queryset = instance.menuPermission.filter(id__in=permissionIds, menu=instance.id).values_list('value',
                                                                                                          flat=True)
            if queryset:
                return queryset
            else:
                return None

    class Meta:
        model = Menu
        fields = (
            'id', 'parent', 'meta', 'icon', 'sort', 'path', 'name', 'title', 'is_link', 'is_catalog', 'web_path',
            'component',
            'component_name', 'cache', 'visible', 'menuPermission')
        read_only_fields = ["id"]


# 递归获取菜单
def get_child_menu(childs, menuIds, treeIds):
    '''
    :param 当前节点:
    :return [{"id": child.id, "title": child.title, "children": []}]:
    '''
    children = []
    if childs:
        for child in childs:
            if child.id in menuIds and child.id not in treeIds:
                data = {"path": child.path, "name": child.name,
                        "component": child.component, "meta": child.meta}
                treeIds.append(child.id)
                _childs = Menu.objects.filter(parent=child)
                if _childs:
                    data["children"] = get_child_menu(_childs, menuIds, treeIds)
                children.append(data)
    return children





class MenuViewSet(CustomModelViewSet):
    """
    菜单管理接口
    list:查询
    create:新增
    update:修改
    retrieve:单例
    destroy:删除
    """
    queryset = Menu.objects.all()
    serializer_class = MenuSerializer
    create_serializer_class = MenuCreateSerializer
    update_serializer_class = MenuCreateSerializer
    search_fields = ['name', 'status']
    filter_fields = ['parent', 'name', 'status', 'is_link', 'visible', 'cache', 'is_catalog']

    # extra_filter_backends = []
    # 返回左侧菜单
    @action(methods=['get'], detail=False, url_path='leftMenu', permission_classes=[])
    def leftMenu(self, request, *args, **kwargs):
        # 获得用户权限
        user = request.user
        tree = []
        treeIds = []
        menuIds = user.role.values_list('menu__id', flat=True)
        menusResult = Menu.objects.filter(id__in=menuIds, status=True, parent=None).order_by('sort')
        for menu in menusResult:
            if menu.id not in treeIds:
                menu_data = {"path": menu.path, "name": menu.name,
                             "component": menu.component, "meta": menu.meta}
                treeIds.append(menu.id)
                childs = Menu.objects.filter(parent=menu).order_by('sort')
                if childs:
                    menu_data["children"] = get_child_menu(childs, menuIds, treeIds)
                tree.append(menu_data)
        if len(tree) == 0:
            return ErrorResponse(code=-1, msg='您暂无登录系统权限', )
        return SuccessResponse(data=tree, total=len(tree))
