# -*- coding: utf-8 -*-

from rest_framework import serializers
from rest_framework.views import APIView

from core_base import dispatch
from core_base.models import Dictionary
from core_base.utils.json_response import SuccessResponse,DetailResponse
from core_base.utils.serializers import CustomModelSerializer
from core_base.utils.viewset import CustomModelViewSet
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated


class DictionarySerializer(CustomModelSerializer):
    """
    字典-序列化器
    """

    class Meta:
        model = Dictionary
        fields = "__all__"
        read_only_fields = ["id"]


class DictionaryInitSerializer(CustomModelSerializer):
    """
    初始化获取数信息(用于生成初始化json文件)
    """
    children = serializers.SerializerMethodField()

    def get_children(self, obj: Dictionary):
        data = []
        instance = Dictionary.objects.filter(parent_id=obj.id)
        if instance:
            serializer = DictionaryInitSerializer(instance=instance, many=True)
            data = serializer.data
        return data

    def save(self, **kwargs):
        instance = super().save(**kwargs)
        children = self.initial_data.get('children')
        # 菜单表
        if children:
            for data in children:
                data['parent'] = instance.id
                filter_data = {
                    "value": data['value'],
                    "parent": data['parent']
                }
                instance_obj = Dictionary.objects.filter(**filter_data).first()
                if instance_obj and not self.initial_data.get('reset'):
                    continue
                serializer = DictionaryInitSerializer(instance_obj, data=data, request=self.request)
                serializer.is_valid(raise_exception=True)
                serializer.save()
        return instance

    class Meta:
        model = Dictionary
        fields = ['label', 'value', 'parent', 'type', 'color', 'is_value', 'status', 'sort', 'creator',
                  'dept_belong_id', 'children']
        read_only_fields = ["id"]
        extra_kwargs = {
            'creator': {'write_only': True},
            'dept_belong_id': {'write_only': True}
        }


class DictionaryCreateUpdateSerializer(CustomModelSerializer):
    """
    字典管理 创建/更新时的列化器
    """

    class Meta:
        model = Dictionary
        fields = '__all__'


def get_child_dictionary(childs):
    '''
    :param 当前节点:
    :return [{"id": child.id, "title": child.title, "children": []}]:
    '''
    children = []
    if childs:
        for child in childs:
            data = {"id": child.id, "parent": child.parent.id, "parentLabel": child.parent.label,
                    "createTime": child.create_datetime,
                    "label": child.label, "value": child.value, "color": child.color, "status": child.status,
                    "sort": child.sort, "description": child.description}
            _childs = Dictionary.objects.filter(parent=child)
            if _childs:
                data["children"] = get_child_dictionary(_childs)
            children.append(data)
    return children


class DictionaryViewSet(CustomModelViewSet):
    """
    字典管理接口
    list:查询
    create:新增
    update:修改
    retrieve:单例
    destroy:删除
    """
    queryset = Dictionary.objects.all()
    serializer_class = DictionarySerializer
    extra_filter_backends = []
    search_fields = ['label']

    # 返回字典全量
    @action(methods=['get'], detail=False, url_path='dictionaryTree', permission_classes=[IsAuthenticated])
    def dictionaryTree(self, request, *args, **kwargs):
        user = request.user
        label = str(request.GET.get("label", '')).strip()
        if label == '':
            dictionaryResult = Dictionary.objects.filter(parent=None).order_by('sort')
        else:
            dictionaryResult = Dictionary.objects.filter(label__icontains=label).order_by('sort')
        tree = []
        for dictionary in dictionaryResult:
            dictionary_data = {"id": dictionary.id, "createTime": dictionary.create_datetime.strftime("%Y-%m-%d %H:%M"), "label": dictionary.label,
                               "value": dictionary.value, "color": dictionary.color,
                               "sort": dictionary.sort, "status": dictionary.status,
                               "description": dictionary.description}
            childs = Dictionary.objects.filter(parent=dictionary).order_by('sort')
            if childs:
                dictionary_data["children"] = get_child_dictionary(childs)
            tree.append(dictionary_data)
        return SuccessResponse(data=tree, total=len(tree), msg="获取成功")

    @action(methods=['GET'], detail=False, permission_classes=[])
    def dictionaryAllKey(self, request, *args, **kwargs):
        dictionaryResult = Dictionary.objects.filter(parent=None, status=True).order_by('sort')
        tree = []
        for dictionary in dictionaryResult:
            dictionary_data = {"id": dictionary.id, "createTime": dictionary.create_datetime, "label": dictionary.label,
                               "value": dictionary.value, "color": dictionary.color,
                               "sort": dictionary.sort, "status": dictionary.status,
                               "description": dictionary.description}
            childs = Dictionary.objects.filter(parent=dictionary).order_by('sort')
            if childs:
                dictionary_data["children"] = get_child_dictionary(childs)
            tree.append(dictionary_data)
        return DetailResponse(data=tree, msg="获取成功")


class InitDictionaryViewSet(APIView):
    """
    获取初始化配置
    """
    authentication_classes = []
    permission_classes = []
    queryset = Dictionary.objects.all()

    def get(self, request):
        dictionary_key = self.request.query_params.get('dictionary_key')
        if dictionary_key:
            if dictionary_key == 'all':
                data = [ele for ele in dispatch.get_dictionary_config().values()]
                if not data:
                    dispatch.refresh_dictionary()
                    data = [ele for ele in dispatch.get_dictionary_config().values()]
            else:
                data = self.queryset.filter(parent__value=dictionary_key, status=True).values('label', 'value', 'type',
                                                                                              'color')
            return SuccessResponse(data=data, msg="获取成功")
        return SuccessResponse(data=[], msg="获取成功")
