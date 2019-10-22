#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
- author: Lkeme
- contact: Useri@live.cn
- file: ConfigGetter
- time: 2019/10/21 18:01
- desc: 
"""
from Util import LazyProperty
from Config.setting import *


class ConfigGetter(object):
    """
    get config
    """

    def __init__(self):
        pass

    @LazyProperty
    def db_name(self):
        return DATABASES.get("default", {}).get("DATABASE", "netease")

    @LazyProperty
    def db_host(self):
        return DATABASES.get("default", {}).get("HOST", "localhost")

    @LazyProperty
    def db_port(self):
        return DATABASES.get("default", {}).get("PORT", 3306)

    @LazyProperty
    def db_user(self):
        return DATABASES.get("default", {}).get("USERNAME", "root")

    @LazyProperty
    def db_password(self):
        return DATABASES.get("default", {}).get("PASSWORD", "123456")

    @LazyProperty
    def user_accounts(self):
        return ACCOUNTS

    @LazyProperty
    def notification(self):
        return NOTIFICATION


config = ConfigGetter()

if __name__ == '__main__':
    print(config.user_accounts)
