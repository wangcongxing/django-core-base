"""
Django settings for application project.

Generated by 'django-admin startproject' using Django 3.2.3.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.2/ref/settings/
"""

import os
import sys
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = 'django-insecure-no%8z#s@7=%-6+yw5c(88!qo8)!xc#$gmez$g3s6wmdkszdhg*'

API_LOG_ENABLE = True
# API_LOG_METHODS = 'ALL'
API_LOG_METHODS = ["POST", "UPDATE", "DELETE", "PUT"]  # ['POST', 'DELETE']
API_MODEL_MAP = {
    "/token/": "登录模块",
    "/api/login/": "登录模块",
    "/api/plugins_market/plugins/": "插件市场",
}
AUTH_USER_MODEL = "core_base.Users"
USERNAME_FIELD = "username"
ALL_MODELS_OBJECTS = []  # 所有app models 对象
# 初始化需要执行的列表，用来初始化后执行
INITIALIZE_LIST = []
INITIALIZE_RESET_LIST = []
# 表前缀
TABLE_PREFIX = locals().get('TABLE_PREFIX', "core_base_")
# 系统配置
SYSTEM_CONFIG = {}
# 字典配置
DICTIONARY_CONFIG = {}
# ================================================= #
# ******************** 插件配置 ******************** #
# ================================================= #
# 租户共享app
TENANT_SHARED_APPS = []
# 插件 urlpatterns
PLUGINS_URL_PATTERNS = []
# ********** 一键导入插件配置开始 **********
# 例如:
# from dvadmin_upgrade_center.settings import *    # 升级中心
# from dvadmin_celery.settings import *            # celery 异步任务
# ...
# ********** 一键导入插件配置结束 **********
