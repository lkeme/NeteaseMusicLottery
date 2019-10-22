#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
- author: Lkeme
- contact: Useri@live.cn
- file: Printer
- time: 2019/10/21 17:41
- desc: 
"""
import time


class Printer:
    # 格式化时间
    @staticmethod
    def current_time():
        return f"[{str(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))}]"

    # 格式化打印
    def printer(self, genre, info, *args):
        # flag = "," if len(args) else " "
        content = f'{self.current_time()} [{genre}] {info} {" ".join(f"{str(arg)}" for arg in args)}'
        print(content, flush=True)


if __name__ == '__main__':
    printer = Printer()
    printer.printer("TEST", "ENABLE")
