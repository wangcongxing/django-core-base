from rest_framework import exceptions
from rest_framework.authentication import BaseAuthentication
from django.contrib.auth import get_user_model
from core_base import settings as config
from jwt import decode as jwt_decode
User = get_user_model()

class UserAuthentication(BaseAuthentication):
    '''
    支持GET 参数传入token 为了解决导出excel身份认证问题
    '''
    def authenticate(self, request):
        access_token = request.GET.get('access_token', "")
        try:
            decoded_data = jwt_decode(access_token, config.SECRET_KEY, algorithms=["HS256"])
            userid = decoded_data["user_id"]
            currentUser = User.objects.get(id=int(userid))
            return currentUser, access_token
        except Exception as ex:
            raise exceptions.AuthenticationFailed(detail={'code': 401, 'msg': 'access_token已过期'})

    def authenticate_header(self, request):
        pass
