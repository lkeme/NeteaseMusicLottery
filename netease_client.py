#!/usr/bin/env python
# -*- coding: utf-8 -*-
import random
import time
import traceback
import pymysql
import requests
from lib import NeteaseLogin, EncryptParams, printer

#######################
#       账户设置       #
#######################
username = ""
password = ""
user_id = ""
sc_key = ""

#######################
#      程序设置       #
#######################
host = 'localhost'
user = 'root'
pwd = ''
port = 3306
database = 'netease'


# 中奖发送
def server_chan(title="", content=""):
    while True:
        try:
            if sc_key != '':
                url = f'https://sc.ftqq.com/{sc_key}.send'
                data = {
                    'text': title,
                    'desp': content
                }
                headers = {
                    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                    'Referer': 'http://sc.ftqq.com/?c=code',
                }
                response = requests.post(url, headers=headers, data=data,
                                         timeout=30).json()
                if response['errmsg'] == 'success':
                    return True
        except:
            continue

    return False


# 数据库连接
def db_conn():
    db = pymysql.connect(host=host, user=user, password=pwd, db=database,
                         port=port)
    cur = db.cursor(cursor=pymysql.cursors.DictCursor)
    return db, cur


# 更新删除数据库
def update_delete_db(lottery_id, table='event_information'):
    db, cur = db_conn()
    sql = f'UPDATE {table} SET is_deleted = 1 WHERE lottery_id = %s;'
    try:
        cur.execute(sql, (lottery_id))
        db.commit()
    except Exception as e:
        # 错误回滚
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()
        printer(f"INFO: 更新删除数据库完毕")


# 时间戳
def current_unix():
    now = (int(time.time() * 1000))
    return now


# 查询
def query_data_db(table='event_information'):
    db, cur = db_conn()
    sql = f'select * from {table}; '
    cur.execute(sql)
    row_list = cur.fetchall()
    db.close()
    cur.close()
    return row_list


# 查询删除数据库
def query_delete_db(table='event_information'):
    db, cur = db_conn()
    row_list = []
    now_time = current_unix()
    sql = f'select * from {table} where ((lottery_time + 43200*1000) < %s and is_reposted=1 and is_deleted=0);'
    cur.execute(sql, (now_time))
    for row in cur.fetchall():
        row_list.append(row)
    db.close()
    cur.close()

    printer(f"INFO: 查询删除数据库完毕 DATA: {len(row_list)}")
    return row_list


# 查询转发数据库
def query_repost_db(table='event_information'):
    db, cur = db_conn()
    now_time = current_unix()
    sql = f'select * from {table} where  ((lottery_time - 43200*1000) < %s and lottery_time > %s and is_reposted=0); '
    cur.execute(sql, (now_time, now_time))
    row_list = cur.fetchall()
    db.close()
    cur.close()
    printer(row_list)
    return row_list


# 更新转发数据库
def update_repost_db(event_id, pre_event_id, table='event_information'):
    db, cur = db_conn()
    sql = f'UPDATE {table} SET is_reposted = 1 , pre_event_id = %s WHERE event_id = %s'
    try:
        cur.execute(sql, (pre_event_id, event_id))
        db.commit()
    except Exception as e:
        # 错误回滚
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()
        printer(f"INFO: 更新转发数据库完毕")


# 插入数据
def insert_data(uid, event_msg, event_id, lottery_id, lottery_time,
                is_reposted=0, is_deleted=0, pre_event_id=0,
                table='event_information'):
    db, cur = db_conn()

    sql = f'insert into {table}( uid, event_msg, event_id, lottery_id, lottery_time,crt_time, is_reposted, is_deleted, pre_event_id) values (%s,%s,%s,%s,%s,%s,%s,%s,%s)'

    try:
        cur.execute(sql, (
            uid, event_msg, event_id, lottery_id, lottery_time, current_unix(),
            is_reposted, is_deleted, pre_event_id))
        db.commit()
        printer(f"插入数据库成功")

    except Exception as e:
        traceback.print_exc()
        printer(f"插入数据库出错", e)
        # 错误回滚
        db.rollback()
    finally:
        db.close()


class NeteaseLottery():

    def __init__(self):
        self.session = NeteaseLogin().login(username, password)
        # self.session = requests.Session()
        self.enc_params = EncryptParams()
        self.lottery_list = []
        self.session.headers.update(
            {
                'User-Agent': 'NeteaseMusic/5.9.1.1551789389(137);Dalvik/2.1.0 (Linux; U; Android 6.0.1; oneplus a5010 Build/V417IR)',
                'Host': 'music.163.com',
            }
        )
        self.lock = {
            'scan': 0,
        }

    def monitor(self):
        while True:
            try:
                self.scan_lottery_id()
                self.repeat_lottery()
                self.repost()
                self.rollback()
                printer('休眠一小时，稍后继续')
                time.sleep(3600)
            except Exception as e:
                printer('流程出错,稍后重试', e)
                time.sleep(30)

    # 扫描动态
    def scan_lottery_id(self):
        url = 'http://music.163.com/weapi/act/event?csrf_token='
        scan_page = 10
        max_page = '100'
        lasttime = '-1'
        actids = {
            '互动抽奖': '44196506',
            '抽奖活动': '17731067',
            '转发抽奖': '20397151',
            '抽奖福利': '19873053',
        }
        for actid in actids.keys():
            for page in range(0, scan_page):
                printer(f'开始扫描 {actid} 第 {page+1} 页')
                while True:
                    try:
                        params = {
                            "actid": actids[actid],
                            "total": "true",
                            "limit": "20",
                            "lasttime": lasttime,
                            "pagesize": max_page,
                            "getcounts": "true",
                            "csrf_token": ""
                        }
                        params = self.enc_params.get(params)
                        response = self.session.post(url, params=params).json()
                        events = response['events']
                        for event in events:
                            event_data = event['lotteryEventData']

                            if event_data is None or \
                                    event_data['lotteryId'] \
                                    in self.lottery_list or \
                                    event_data['status'] == "2":
                                continue
                            printer(
                                f"title: {event_data['title']}, lotteryId: {event_data['lotteryId']}, status: {event_data['status']}")
                            self.lottery_list.append(event_data['lotteryId'])
                        lasttime = response['lasttime']
                        break
                    except Exception as e:
                        traceback.print_exc()
                        printer('扫描动态出现错误, 重试!', e)

                if not response['more']:
                    break
        printer(f'此次扫描已结束,当前库存 {len(self.lottery_list)} 个未验证抽奖动态')

    # 获取动态信息
    def get_lottery_info(self, lottery_id):
        url = f"http://music.163.com/api/lottery/event/get?lotteryId={lottery_id}"
        response = self.session.get(url).json()
        data = {
            'uid': response['data']['user']['userId'],
            'event_msg': response['data']['event']['eventMsg'],
            'event_id': response['data']['lottery']['eventId'],
            'lottery_id': response['data']['lottery']['lotteryId'],
            'lottery_time': response['data']['lottery']['lotteryTime'],
            'status': response['data']['lottery']['status']
        }
        return data

    # 去重
    def repeat_lottery(self):
        lottery_data = query_data_db()
        temp_lottery_list = []
        for lottery in lottery_data:
            temp_lottery_list.append(lottery['lottery_id'])
        for lottery_id in self.lottery_list:
            if lottery_id in temp_lottery_list:
                continue
            data = self.get_lottery_info(lottery_id)
            if data['status'] == 2:
                continue
            insert_data(data['uid'], data['event_msg'], data['event_id'],
                        data['lottery_id'], data['lottery_time'])
        self.lottery_list = []
        printer('动态库存清理成功')

    # 转发
    def forward(self, event_id, event_uid, msg):
        url = f"http://music.163.com/weapi/event/forward"
        params = {
            "forwards": msg,
            "id": event_id,
            "eventUserId": event_uid,
            "checkToken": "",
            "csrf_token": ""
        }
        params = self.enc_params.get(params)
        response = self.session.post(url, params=params).json()
        printer("转发状态", response)
        update_repost_db(event_id, response['data']['eventId'])
        url = 'http://music.163.com/weapi/feedback/weblog'
        params = {
            "logs": [
                {
                    "action": "eventclick",
                    "json": {"id": event_id, "sourceid": event_uid, "alg": "",
                             "contentType": "user_event",
                             "actionType": "forward"}}
            ],
            "csrf_token": ""
        }
        params = self.enc_params.get(params)
        response = self.session.post(url, params=params).json()
        printer(response)

    # 关注
    def follow(self, follow_uid):
        user = self.session.cookies.get_dict()
        url = f"http://music.163.com/weapi/user/follow/{follow_uid}?csrf_token={user['__csrf']}"
        params = {
            "followId": follow_uid,
            "checkToken": "",
            "csrf_token": user['__csrf']
        }
        params = self.enc_params.get(params)
        response = self.session.post(url, params=params).json()
        printer(response)

    # 取消关注
    def unfollow(self, follow_uid):
        user = self.session.cookies.get_dict()

        url = f'http://music.163.com/weapi/user/delfollow/{follow_uid}?csrf_token='
        params = {
            "followId": follow_uid,
            "csrf_token": user['__csrf']
        }
        params = self.enc_params.get(params)
        response = self.session.post(url, params=params).json()
        printer(response)

    # 转发
    def repost(self):
        message = random.choice([
            '转发动态', '转发动态', '转发动态', '转发动态', '转发动态', '', '', '好运来', '脱非转欧',
            '啊~',
            '哈哈哈',
            '中奖绝缘体', '绝缘体', '求脱非入欧', '好运',
            '呜呜呜非洲人来了', '选我吧', '一定会中', '好运bufff', '滴滴滴', '哇哇哇哇', 'emm',
            '拉低中奖率', '万一呢', '非酋日常', '加油', '抽中吧', '我要', '想欧一次！',
            '拉低中奖率233', '想要...', '路过拉低中奖率', '希望有个好运气', '抽奖奖(⌒▽⌒)',
            '中奖绝缘体表示想中！',
            '中奖', '什么时候才会抽到我呢？', '试试水，看看能不能中', '过来水一手', '中奖什么的不可能的（￣▽￣）',
            '这辈子都不可能中奖的', '先拉低中奖率23333', '先抽奖，抽不到再说',
            '嘤嘤嘤', '捞一把', '我就想中一次', '拉低拉低', '试一试', '搞一搞', '听说我中奖了？'
        ])
        data = query_repost_db()
        for d in data:
            self.forward(d['event_id'], d['uid'], message)
            self.follow(d['uid'])

    #
    def del_event(self, event_id):
        user = self.session.cookies.get_dict()
        url = 'http://music.163.com/weapi/event/delete'
        params = {
            "type": "delete",
            "id": event_id,
            "transcoding": "false",
            "csrf_token": user['__csrf']
        }
        params = self.enc_params.get(params)
        response = self.session.post(url, params=params).json()
        printer(response)

    # rollbak
    def rollback(self):
        data = query_delete_db()
        for d in data:
            if self.win_check(d['lottery_id']):
                if (d['lottery_time'] + 86400) > current_unix():
                    continue

            self.del_event(d['pre_event_id'])
            self.unfollow(d['uid'])
            update_delete_db(d['lottery_id'])

    # wincheck
    def win_check(self, lottery_id):
        url = f"http://music.163.com/api/lottery/event/get?lotteryId={lottery_id}"
        response = self.session.get(url).json()
        prize_ids = response['data']['lottery']['prizeId']
        prize_ids = prize_ids.strip('[').strip(']').split(',')
        for prize_id in prize_ids:
            data = response['data']['luckUsers'][prize_id]
            for d in data:
                if d['userId'] == user_id:
                    server_chan('网易云互动抽奖', f'恭喜 {user_id} 在互动抽奖里中奖啦,请尽快填写信息')
                    return True

        return False


if __name__ == '__main__':
    NeteaseLottery().monitor()
