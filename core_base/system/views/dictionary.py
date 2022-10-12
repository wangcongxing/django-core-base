# -*- coding: utf-8 -*-

from rest_framework import serializers
from rest_framework.views import APIView

from core_base import dispatch
from core_base.models import Dictionary
from core_base.utils.json_response import SuccessResponse
from core_base.utils.serializers import CustomModelSerializer
from core_base.utils.viewset import CustomModelViewSet
from rest_framework.decorators import action


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
            data = {"id": child.id, "key": child.value, "label": child.label}
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

    # 返回字典类型
    @action(methods=['GET'], detail=False, permission_classes=[])
    def dictionary_tree(self, request, *args, **kwargs):
        result = []
        dictionarysParent = []
        dictionarys = Dictionary.objects.filter(status=True, parent=None).order_by('sort')
        dictionary_data = {"id": "0", "key": "root", "label": "全部字典", "children": []}
        for dictionary in dictionarys:
            children_data = {"id": dictionary.id, "key": dictionary.value, "label": dictionary.label}
            dictionarysParent.append(children_data)
        dictionary_data["children"] = dictionarysParent
        result.append(dictionary_data)
        return SuccessResponse(data=result, msg="获取成功")

    @action(methods=['GET'], detail=False, permission_classes=[])
    def dictionary_list(self, request, *args, **kwargs):
        label = request.GET.get('label', '')
        print(label)
        dictionarys = Dictionary.objects.filter(parent__label=label).order_by('sort').values("id", "label",
                                                                                                  "value", "parent",
                                                                                             "status","sort",
                                                                                                  "color",
                                                                                                  "description")
        return SuccessResponse(data=list(dictionarys), msg="获取成功")


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
