# -*- coding: utf-8 -*-

from rest_framework import serializers

from core_base.models import Dept, Users, EmailGroup, Tags
from core_base.utils.json_response import DetailResponse, SuccessResponse, ErrorResponse
from core_base.utils.serializers import CustomModelSerializer
from core_base.utils.viewset import CustomModelViewSet
from rest_framework.decorators import action
from django_filters import rest_framework as filters
import django_filters
from rest_framework.permissions import IsAuthenticated
from core_base.utils import org_factory
from django.db.models import Q


class DeptSerializer(CustomModelSerializer):
    """
    部门-序列化器
    """
    parent_name = serializers.CharField(read_only=True, source='parent.name')
    has_children = serializers.SerializerMethodField()
    status_label = serializers.SerializerMethodField()

    def get_has_children(self, obj: Dept):
        return Dept.objects.filter(parent_id=obj.id).count()

    def get_status_label(self, instance):
        status = instance.status
        if status:
            return "启用"
        return "禁用"

    class Meta:
        model = Dept
        fields = '__all__'
        read_only_fields = ["id"]


class DeptInitSerializer(CustomModelSerializer):
    """
    递归深度获取数信息(用于生成初始化json文件)
    """
    children = serializers.SerializerMethodField()

    def get_children(self, obj: Dept):
        data = []
        instance = Dept.objects.filter(parent_id=obj.id)
        if instance:
            serializer = DeptInitSerializer(instance=instance, many=True)
            data = serializer.data
        return data

    def save(self, **kwargs):
        instance = super().save(**kwargs)
        children = self.initial_data.get('children')
        if children:
            for menu_data in children:
                menu_data['parent'] = instance.id
                filter_data = {
                    "name": menu_data['name'],
                    "parent": menu_data['parent']
                }
                instance_obj = Dept.objects.filter(**filter_data).first()
                if instance_obj and not self.initial_data.get('reset'):
                    continue
                serializer = DeptInitSerializer(instance_obj, data=menu_data, request=self.request)
                serializer.is_valid(raise_exception=True)
                serializer.save()
        return instance

    class Meta:
        model = Dept
        fields = ['name', 'sort', 'owner', 'status', 'parent', 'creator', 'dept_belong_id',
                  'children']
        extra_kwargs = {
            'creator': {'write_only': True},
            'dept_belong_id': {'write_only': True}
        }
        read_only_fields = ['id', 'children']


class DeptCreateUpdateSerializer(CustomModelSerializer):
    """
    部门管理 创建/更新时的列化器
    """

    def create(self, validated_data):
        instance = super().create(validated_data)
        instance.dept_belong_id = instance.id
        instance.save()
        return instance

    class Meta:
        model = Dept
        fields = '__all__'


# 递归获取菜单
def get_child_dept(childs):
    '''
    :param 当前节点:
    :return [{"id": child.id, "title": child.title, "children": []}]:
    '''
    children = []
    if childs:
        for child in childs:
            data = {"id": child.id, "parent": child.parent.name, "createTime": child.create_datetime,
                    "name": child.name,
                    "sort": child.sort, }
            _childs = Dept.objects.filter(parent=child)
            if _childs:
                data["children"] = get_child_dept(_childs)
            children.append(data)
    return children


class DeptFilter(filters.FilterSet):
    # 模糊过滤
    name = django_filters.CharFilter(field_name="name", lookup_expr='icontains')

    class Meta:
        model = Dept
        fields = ['name']
        search_fields = ('name')  # 允许模糊查询的字段


class DeptViewSet(CustomModelViewSet):
    """
    部门管理接口
    list:查询
    create:新增
    update:修改
    retrieve:单例
    destroy:删除
    """
    queryset = Dept.objects.all()
    serializer_class = DeptSerializer
    create_serializer_class = DeptCreateUpdateSerializer
    update_serializer_class = DeptCreateUpdateSerializer
    filter_class = DeptFilter

    # extra_filter_backends = []
    @action(methods=['get'], detail=False, )
    def dept_lazy_tree(self, request, *args, **kwargs):
        parent = self.request.query_params.get('parent')
        queryset = self.filter_queryset(self.get_queryset())
        if not parent:
            if self.request.user.is_superuser:
                queryset = queryset.filter(parent__isnull=True)
            else:
                queryset = queryset.filter(id=self.request.user.dept_id)
        data = queryset.filter(status=True).order_by('sort').values('name', 'id', 'parent')
        return DetailResponse(data=data, msg="获取成功")

    # 返回部门组织架构树/全量 不包括用户信息
    @action(methods=['get'], detail=False, url_path='dept_tree', permission_classes=[IsAuthenticated])
    def dept_tree(self, request, *args, **kwargs):
        user = request.user
        name = str(request.GET.get("name", '')).strip()
        if name == '':
            deptResult = Dept.objects.filter(parent=None, status=True).order_by('sort')
        else:
            deptResult = Dept.objects.filter(status=True, name__icontains=name).order_by('sort')
        tree = []
        for dept in deptResult:
            menu_data = {"id": dept.id, "createTime": dept.create_datetime, "name": dept.name,
                         "sort": dept.sort, }
            childs = Dept.objects.filter(parent=dept).order_by('sort')
            if childs:
                menu_data["children"] = get_child_dept(childs)
            tree.append(menu_data)
        if len(tree) == 0:
            return SuccessResponse('您暂无登录系统权限', )
        return SuccessResponse(data=tree, total=len(tree), msg="获取成功")

    # 返回部门组织架构树/增量 包括用户信息
    @action(methods=['get'], detail=False, url_path='dept_tree_userinfo', permission_classes=[IsAuthenticated])
    def dept_tree_userinfo(self, request, *args, **kwargs):
        nid = request.GET.get("nid", 0)

        parent = None if nid == '' else Dept.objects.filter(id=nid).first()
        result = Dept.objects.filter(parent=parent, status=True).order_by(
            "sort").values("id", "name",
                           "owner",
                           "sort", "description")
        result = list(result)
        userList = Users.objects.filter(dept=parent)
        for item in userList:
            result.append({
                "id": item.id,
                "type": "user",
                "username": item.username,
                "name": item.name,
                "email": item.email,
                "mobile": item.mobile,
                "avatar": item.avatar,
                "structLevelName": item.structLevelName,
                "empNo": item.empNo,
                "phone": item.phone,
                "parent": item.dept.id,
                "sort": 1,
                "desc": ""
            })
        return SuccessResponse(data=result, total=len(result), msg="获取成功")

    # 解析前端提交的组织结构信息
    # 解析组织架构/标签/群组
    @action(methods=['post'], detail=False, url_path='parse_result', permission_classes=[IsAuthenticated])
    def parse_result(self, request, *args, **kwargs):
        authListResult = request.data.get("authList", [])
        if authListResult and len(authListResult) == 0:
            return ErrorResponse(-1, f'参数为空或不合法请稍后在试,{authListResult}')
        result = []
        for item in authListResult:
            org_type = item.get("type", "")
            infos = item.get("infos", [])
            result += org_factory.orgCommand(org_type, infos).getResult()
        result = [dict(t) for t in set([tuple(d.items()) for d in result])]
        return DetailResponse(data=result)

    # 通用搜索
    @action(methods=['get'], detail=False, url_path='searchOrg', permission_classes=[IsAuthenticated])
    def searchOrg(self, request, *args, **kwargs):
        result = {"org": [],
                  "emailGroup": [], "tag": [], "otherTags": [],
                  "user": []}
        searchValue = request.GET.get("searchValue", "")
        if searchValue == "":
            return DetailResponse(data=result)
        creator = request.user
        username = request.user.username
        organizationResult = list(
            Dept.objects.filter(name__icontains=searchValue, status=True).values("id", "name", "sort"))

        emailGroupResult = list(EmailGroup.objects.filter(status=True).filter(
            Q(title__icontains=searchValue) | Q(account_number__icontains=searchValue)).values("id",
                                                                                              "title",
                                                                                              "account_number",
                                                                                              "sort"))
        # 我的标签
        tagResult = list(
            Tags.objects.filter(title__icontains=searchValue, status=True, creator=creator).values("id", "title"))
        # 其它标签
        otherTags = list(Tags.objects.filter(share_user__username__in=username).values("id", "title"))

        # 查询用户
        userResult = Users.objects.filter(
            Q(username__icontains=searchValue) | Q(name__icontains=searchValue) | Q(
                email__icontains=searchValue))
        userResultList = []
        for item in userResult:
            userResultList.append({
                "id": item.id,
                "type": "user",
                "username": item.username.upper(),
                "name": item.name,
                "sort": 0,
            })
        result = {"org": organizationResult,
                  "emailGroup": emailGroupResult, "tag": tagResult, "otherTags": tagResult,
                  "user": userResultList}
        return DetailResponse(result)
