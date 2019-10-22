#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
- author: Lkeme
- contact: Useri@live.cn
- file: UtilClass
- time: 2019/10/21 17:30
- desc: 
"""


class Singleton(type):
    """
    Singleton Metaclass
    """

    _inst = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._inst:
            cls._inst[cls] = super(Singleton, cls).__call__(*args)
        return cls._inst[cls]
