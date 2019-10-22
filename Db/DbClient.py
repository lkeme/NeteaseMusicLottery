#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
- author: Lkeme
- contact: Useri@live.cn
- file: DbClient
- time: 2019/10/21 17:27
- desc: 
"""
import os
import sys
import pymysql
from Util import Singleton, Printer
from Util.Function import current_unix
from Config.ConfigGetter import config

sys.path.append(os.path.dirname(os.path.abspath(__file__)))


class DbClient(object):
    """
    DbClient DB工厂类
    """

    __metaclass__ = Singleton

    def __init__(self):
        """
        init
        :return:
        """
        self.name = None
        self.client = None
        self.cursor = None
        self.log = Printer()
        self.db_conn()

    def db_conn(self):
        """
        init DB Client
        :return:
        """
        self.client = pymysql.connect(
            host=config.db_host,
            user=config.db_user,
            password=config.db_password,
            db=config.db_name,
            port=config.db_port
        )
        self.cursor = self.client.cursor(cursor=pymysql.cursors.DictCursor)

    # 查询key
    def query_key(self, key):
        sql = f"select {key} from {self.name}"
        self.cursor.execute(sql)
        row_list = self.cursor.fetchall()
        new_row_list = [row[key] for row in row_list]
        return new_row_list

    # 查询有效数据
    def query_valid(self):
        sql = f"select * from {self.name} where lottery_time > %s"
        self.cursor.execute(sql, (current_unix(),))
        row_list = self.cursor.fetchall()
        self.log.printer("DB", f"查询有效数据库完毕 data->{len(row_list)}")
        return row_list

    # 查询转发数据库
    def query_forward(self):
        sql = f"select * from {self.name} where  ((lottery_time - 43200*1000) < %s and lottery_time > %s and is_reposted=0)"
        self.cursor.execute(sql, (current_unix(), current_unix()))
        row_list = self.cursor.fetchall()
        self.log.printer("DB", f"查询转发数据库完毕 data->{len(row_list)}")
        return row_list

    # 查询删除数据库
    def query_delete(self):
        sql = f"select * from {self.name} where ((lottery_time + 3600*1000) < %s and is_reposted=1 and is_deleted=0)"
        self.cursor.execute(sql, (current_unix(),))
        row_list = self.cursor.fetchall()
        self.log.printer("DB", f"查询删除数据库完毕 data->{len(row_list)}")
        return row_list

    # 查询event_raw_id 2 pre_event_id数据库
    def query_pre_event(self, username, event_id):
        sql = f"select pre_event_id from {self.name} where (username = %s and raw_event_id = %s)"
        self.cursor.execute(sql, (username, event_id))
        row_list = self.cursor.fetchone()
        self.log.printer("DB", f"查询PRE数据库完毕 data->{len(row_list)}")
        return row_list

    # 插入原始数据
    def insert_raw(self, uid, event_msg, event_id, lottery_id, lottery_time):
        sql = f"INSERT INTO {self.name}( uid, event_msg, event_id, lottery_id, lottery_time,crt_time,is_reposted, is_deleted) values (%s,%s,%s,%s,%s,%s,%s,%s)"
        try:
            self.cursor.execute(sql, (
                uid, event_msg, event_id, lottery_id,
                lottery_time, current_unix(), 0, 0
            ))
            self.client.commit()
        except Exception as e:
            self.client.rollback()
            self.log.printer("DB", "插入原始数据", e)
        finally:
            self.log.printer("DB", "插入原始数据", "ok")

    # 插入使用数据
    def insert_used(self, username, pre_event_id, raw_event_id):
        sql = f"INSERT INTO {self.name}( username, pre_event_id, raw_event_id, crt_time) values (%s,%s,%s,%s)"
        try:
            self.cursor.execute(sql, (
                username, pre_event_id, raw_event_id, current_unix()
            ))
            self.client.commit()
        except Exception as e:
            self.client.rollback()
            self.log.printer("DB", "插入使用数据", e)
        finally:
            self.log.printer("DB", "插入使用数据", "ok")

    # 更新原始删除
    def update_raw_deleted(self, lottery_id):
        sql = f"UPDATE {self.name} SET is_deleted = 1 WHERE lottery_id = %s"
        try:
            self.cursor.execute(sql, (lottery_id,))
            self.client.commit()
        except Exception as e:
            self.client.rollback()
            self.log.printer("DB", "更新删除数据库", e)

        finally:
            self.log.printer("DB", "更新删除数据库", "ok")

    # 更新原始转发
    def update_raw_reposted(self, lottery_id):
        sql = f"UPDATE {self.name} SET is_reposted = 1 WHERE lottery_id = %s"
        try:
            self.cursor.execute(sql, (lottery_id,))
            self.client.commit()
        except Exception as e:
            self.client.rollback()
            self.log.printer("DB", "更新删除数据库", e)

        finally:
            self.log.printer("DB", "更新删除数据库", "ok")

    # 改变表
    def change_table(self, name):
        self.name = name


if __name__ == '__main__':
    pass
