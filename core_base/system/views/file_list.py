from core_base.models import FileList
from core_base.utils.serializers import CustomModelSerializer
from core_base.utils.viewset import CustomModelViewSet
import os, uuid
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from core_base import settings as config
from core_base.utils.json_response import ErrorResponse, DetailResponse
import hashlib
from django_filters import rest_framework as filters
import django_filters
import pandas as pd


class FileSerializer(CustomModelSerializer):
    class Meta:
        model = FileList
        fields = "__all__"


class FileFilter(filters.FilterSet):
    # 模糊过滤
    name = django_filters.CharFilter(field_name="name", lookup_expr='icontains')

    class Meta:
        model = FileList
        fields = ['name']
        search_fields = ('name')  # 允许模糊查询的字段

class FileViewSet(CustomModelViewSet):
    """
    文件管理接口
    list:查询
    create:新增
    update:修改
    retrieve:单例
    destroy:删除
    """
    queryset = FileList.objects.all()
    serializer_class = FileSerializer
    filter_class = FileFilter
    permission_classes = []

    # 上传文件/多文件
    @action(methods=['post'], detail=False, url_path='uploadFile', permission_classes=[IsAuthenticated])
    def uploadFile(self, request, *args, **kwargs):
        fileNames = []
        files = request.FILES.getlist('file', [])
        creator = request.user
        for item in files:
            ext = config.safeFileExt
            fn, t = os.path.splitext(item.name)
            if t.lower() not in ext:
                t = ".png"
            filename = f"{uuid.uuid4().hex}{t.lower()}"
            filePath = config.MEDIA_ROOT + "/" + filename
            with open(filePath, 'wb') as f:
                for c in item.chunks():
                    f.write(c)
                f.close()
            md5 = hashlib.md5()
            for chunk in item.chunks():
                md5.update(chunk)
            FileList.objects.create(name=fn, file=filename, md5sum=md5.hexdigest(), creator=creator)
            if config.envpro == "pro":
                fileNames.append("/teamwork/media/" + filename)
            else:
                fileNames.append(config.domain + "media/" + filename)
        return DetailResponse(data=fileNames, msg="上传成功")

    # 解析excel文件,用于上传组件预览
    @action(methods=['post'], detail=False, url_path='parseExcelToJson', permission_classes=[IsAuthenticated])
    def parseExcelToJson(self, request, *args, **kwargs):
        result = {}
        fileStream = request.FILES.get("file", None)
        limit = int(request.data.get('limit', 2000))
        if fileStream is None:
            return ErrorResponse('请上传excel文件')
        # 读取Excel文件
        df = pd.read_excel(fileStream)
        result.update({"count": len(df)})
        df = df[0:limit] if len(df) > limit else df

        # 替换Excel表格内的空单元格，否则在下一步处理中将会报错
        df.fillna("", inplace=True)
        data = df.to_dict(orient="records")
        result.update({"data": data})
        return DetailResponse(result)
