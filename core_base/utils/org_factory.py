#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import sys, os, django

from core_base.models import Users, Tags, EmailGroup


class orgCommand():
    def __init__(self, org_type: str, infos: list, **kw):
        self.org_type = org_type
        self.infos = infos

    def getOrgResult(self):
        result = []
        userInfos = Users.objects.filter(dept__id__in=self.infos)
        for user_info in userInfos:
            result.append({"nid": user_info.id, "username": str(user_info.username).upper(),
                           "name": user_info.name})
        return result

    def getUserResult(self):
        result = []
        users = Users.objects.filter(id__in=self.infos)
        for user_info in users:
            result.append({"nid": user_info.id, "username": str(user_info.username).upper(),
                           "name": user_info.name})
        return result

    def getTagResult(self):
        result = []
        tags = Tags.objects.filter(id__in=self.infos)
        for t in tags:
            for user_info in t.user_info.all():
                result.append({"nid": user_info.id, "username": str(user_info.username).upper(),
                               "name": user_info.name})
        return result

    def getemailGroupResult(self):
        result = []
        emailgroups = EmailGroup.objects.filter(id__in=self.infos)
        for eGroups in emailgroups:
            for user_info in eGroups.user_json:
                result.append(
                    {"nid": user_info.id, "username": str(user_info.username).upper(), "name": user_info.name})
        return result

    def unknown(self):
        return ['未知类型']

    def getResult(self):
        orgSwitch = {
            'org': self.getOrgResult,
            'user': self.getUserResult,
            'tag': self.getTagResult,
            'emailGroup': self.getemailGroupResult
        }
        result = orgSwitch.get(self.org_type, self.unknown)()
        return result

if __name__ == "__main__":
    from pathlib import Path

    BASE_DIR = f'{Path(__file__).resolve().parent.parent}'
    sys.path.append(BASE_DIR)
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangoAdminPlus.settings')
    django.setup()
    authList = {"authList": [{"type": "org", "infos": [1, 2, 3]},
                             {"type": "user", "infos": [1, 2]},
                             {"type": "tag", "infos": [1, 2]},
                             {"type": "emailGroup", "infos": [1, 2]}]}
    result = []
    for item in authList.get("authList", []):
        orgType = item.get("type", "")
        infos = item.get("infos", [])
        result += orgCommand(orgType, infos).getResult()
    result = [dict(t) for t in set([tuple(d.items()) for d in result])]
    print(result)
