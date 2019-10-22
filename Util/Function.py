#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
- author: Lkeme
- contact: Useri@live.cn
- file: functions
- time: 2019/10/21 19:28
- desc: 
"""
import time


# 时间戳
def current_unix():
    now = (int(time.time() * 1000))
    return now
