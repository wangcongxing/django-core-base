#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from django.urls import path
from rest_framework import routers

from core_base.system.views.api_white_list import ApiWhiteListViewSet
from core_base.system.views.area import AreaViewSet
from core_base.system.views.dept import DeptViewSet
from core_base.system.views.dictionary import DictionaryViewSet
from core_base.system.views.file_list import FileViewSet
from core_base.system.views.logs import LogsViewSet
from core_base.system.views.menu import MenuViewSet
from core_base.system.views.menu_button import MenuButtonViewSet
from core_base.system.views.message_center import MessageCenterViewSet
from core_base.system.views.role import RoleViewSet
from core_base.system.views.system_config import SystemConfigViewSet
from core_base.system.views.tags import TagsViewSet
from core_base.system.views.email_group import EmailGroupViewSet

from core_base.system.views.user import UserViewSet
from django.conf.urls.static import static
from django.urls import path, include, re_path
from rest_framework import permissions
from rest_framework_simplejwt.views import (TokenRefreshView)
from core_base import dispatch, settings
from core_base.system.views.dictionary import InitDictionaryViewSet
from core_base.system.views.login import LoginView, CaptchaView, ApiLogin, LogoutView
from core_base.system.views.system_config import InitSettingsViewSet

system_url = routers.SimpleRouter()
system_url.register(r'menu', MenuViewSet)
system_url.register(r'menu_button', MenuButtonViewSet)
system_url.register(r'role', RoleViewSet)
system_url.register(r'dept', DeptViewSet)
system_url.register(r'user', UserViewSet)
system_url.register(r'dictionary', DictionaryViewSet)
system_url.register(r'area', AreaViewSet)
system_url.register(r'file', FileViewSet)
system_url.register(r'tags', TagsViewSet)
system_url.register(r'email_group', EmailGroupViewSet)
system_url.register(r'api_white_list', ApiWhiteListViewSet)
system_url.register(r'system_config', SystemConfigViewSet)
system_url.register(r'message_center', MessageCenterViewSet)

urlpatterns = [
    path("captcha/", CaptchaView.as_view()),
    path("settings/", InitSettingsViewSet.as_view()),
    path("login/", LoginView.as_view(), name="token_obtain_pair"),
    path("logout/", LogoutView.as_view(), name="token_obtain_pair"),
    path("refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("captcha/", CaptchaView.as_view()),
    path("init/dictionary/", InitDictionaryViewSet.as_view()),
    path("init/settings/", InitSettingsViewSet.as_view()),
    path("apiLogin/", ApiLogin.as_view()),
    path('system_config/save_content/', SystemConfigViewSet.as_view({'put': 'save_content'})),
    path('system_config/get_association_table/', SystemConfigViewSet.as_view({'get': 'get_association_table'})),
    path('system_config/get_table_data/<int:pk>/', SystemConfigViewSet.as_view({'get': 'get_table_data'})),
    path('system_config/get_relation_info/', SystemConfigViewSet.as_view({'get': 'get_relation_info'})),
    path('logs/', LogsViewSet.as_view({'get': 'list'})),
    path('logs/<int:pk>/', LogsViewSet.as_view({'get': 'retrieve'})),
    path('dept_lazy_tree/', DeptViewSet.as_view({'get': 'dept_lazy_tree'})),
    # 导入用户
    path('user/export/', UserViewSet.as_view({'get': 'export_data'})),
    # Get请求下载模版 Post请求导入用户
    path('user/import/', UserViewSet.as_view({'get': 'import_data', 'post': 'import_data'})),
]
urlpatterns += system_url.urls
