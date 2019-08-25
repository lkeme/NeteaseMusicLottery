#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re
import time
import random
import traceback
import asyncio
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

#######################
#      自用设置       #
#######################
sn_url = ''
sn_channel = ''


# 通知分发
def notice_handler(title, content, retry_count=10):
    # TODO 逻辑乱 待优化
    for _ in range(retry_count):
        if sn_url != '' and sn_channel != '':
            status = server_notify(title, content)
            if not status:
                time.sleep(60)
                continue
            return True
        elif sc_key != '':
            status = server_chan(title, content)
            if not status:
                time.sleep(60)
                continue
            return True
        else:
            return False

    return False


# 中奖发送 自用
def server_notify(title="", content=""):
    try:
        if sn_url != '' and sn_channel != '':
            json = {
                "channelName": sn_channel,
                "text": content}
            headers = {
                'content-type': 'application/json'
            }
            response = requests.post(sn_url, headers=headers, json=json,
                                     timeout=30).json()
            # {"error":0,"message":"Done!"}
            if response['message'] == 'Done!':
                return True
    except Exception as e:
        printer(f"[SERCERNOTIFY] {e}")
    return False


# 中奖发送
def server_chan(title="", content=""):
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
    except Exception as e:
        printer(f"[SERCERCHAN] {e}")
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


# 查询抽奖id
def query_lottery_id_db(table='event_information'):
    db, cur = db_conn()
    sql = f'select lottery_id from {table}; '
    cur.execute(sql)
    row_list = cur.fetchall()
    db.close()
    cur.close()
    return row_list


# 查询转发数据库
def query_valid_db(table='event_information'):
    db, cur = db_conn()
    now_time = current_unix()
    sql = f'select * from {table} where lottery_time > %s; '
    cur.execute(sql, (now_time,))
    row_list = cur.fetchall()
    db.close()
    cur.close()
    # printer(row_list)
    printer(f"INFO: 查询有效数据库完毕 DATA: {len(row_list)}")

    return row_list


# 查询删除数据库
def query_delete_db(table='event_information'):
    db, cur = db_conn()
    row_list = []
    now_time = current_unix()
    sql = f'select * from {table} where ((lottery_time + 3600*1000) < %s and is_reposted=1 and is_deleted=0);'
    cur.execute(sql, (now_time,))
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
    # printer(row_list)
    printer(f"INFO: 查询转发数据库完毕 DATA: {len(row_list)}")

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


class NeteaseLottery:

    def __init__(self):
        self.session = NeteaseLogin().login(username, password)
        # self.session = requests.Session()
        self.enc_params = EncryptParams()
        self.lottery_list = []
        self.pre_scan_list = []
        self.session.headers.update(
            {
                'User-Agent': 'NeteaseMusic/5.9.1.1551789389(137);Dalvik/2.1.0 (Linux; U; Android 6.0.1; oneplus a5010 Build/V417IR)',
                'Host': 'music.163.com',
            }
        )
        self.lock = {
            'scan': 0,
        }

    # 扫描存储
    async def server(self):
        while True:
            try:
                await asyncio.sleep(3 * 60)
                self.scan_lottery_id()
                self.repeat_lottery()
                self.repeat_lottery_scan()
                printer('[SERVER] 休眠八小时，稍后继续')
                await asyncio.sleep(8 * 60 * 60)
            except Exception as e:
                printer('[SERVER] 流程出错,稍后重试', e)
                await asyncio.sleep(60)

    # 转发删除
    async def client(self):
        while True:
            try:
                self.repost()
                self.rollback()
                printer('[CLIENT] 休眠一小时，稍后继续')
                await asyncio.sleep(60 * 60)
            except Exception as e:
                printer('[CLIENT] 流程出错,稍后重试', e)
                await asyncio.sleep(60)

    # 扫描动态
    def scan_lottery_id(self):
        # 匹配抽奖id
        def match_lottery_id(json_data):
            pattern = r'\"lotteryId\":(\d+),\"status\":(\d)'
            str_data = str(json_data) \
                .replace(" ", "") \
                .replace("\n", "") \
                .replace("\r", "")
            return re.findall(pattern, str_data)

        url = 'http://music.163.com/weapi/act/event?csrf_token='
        scan_page = 10
        max_page = '100'
        lasttime = '-1'
        actids = {
            '互动抽奖': '44196506',
            '抽奖活动': '17731067',
            '转发抽奖': '20397151',
            '抽奖福利': '19873053',
            '粉丝福利': '3753053'
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
                        # 匹配 未过滤
                        match_data_all = match_lottery_id(response)

                        for match_data in match_data_all:
                            try:
                                lottery_id = int(match_data[0])
                                lottery_status = int(match_data[1])
                            except Exception as e:
                                continue
                            status = 'valid' if lottery_status == 1 else 'invalid'
                            printer(
                                f"title: {actid}, lotteryId: {lottery_id}, status: {status}"
                            )
                            if lottery_id in self.lottery_list:
                                # or lottery_status == 2:
                                continue

                            self.lottery_list.append(lottery_id)
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
        try:
            response = self.session.get(url).json()
            if response['code'] == 200:
                data = {
                    'uid': response['data']['user']['userId'],
                    'event_msg': response['data']['event']['eventMsg'],
                    'event_id': response['data']['lottery']['eventId'],
                    'lottery_id': response['data']['lottery']['lotteryId'],
                    'lottery_time': response['data']['lottery']['lotteryTime'],
                    'prizes': response['data']['prize'],
                    'status': response['data']['lottery']['status']
                }
                printer(f"[SERVER] {lottery_id} -> 命中抽奖")
                return data
            elif response['code'] == 404:
                printer(f"[SERVER] {lottery_id} -> {response['message']}")
            else:
                printer(f"[SERVER] {lottery_id} -> {response}")
            return None
        except Exception as e:
            printer(f"[SERVER] {lottery_id} -> {e}")
            # {"code":404,"message":"动态资源不存在","debugInfo":null}
            return None

    # 区间
    def find_section(self, id):
        # TODO 代码丑陋 待优化
        length = len(str(id)) - 1
        prefix = str(id)[0]
        start = int(prefix + "".join(['0' for _ in range(length)]))
        end = int(prefix + "".join(['9' for _ in range(length)])) + 2
        self.pre_scan_list = self.pre_scan_list + list(range(start, end))
        self.pre_scan_list = list(set(self.pre_scan_list))
        # 第二方案
        # self.pre_scan_list = list(set(self.pre_scan_list).union(set(list(range(start, end)))))
        # printer(f"当前区间 {start},{end} 已有数据 {len(self.pre_scan_list)}")
        return None

    # 去重
    def repeat_lottery(self):
        temp_lottery_list = query_lottery_id_db()
        printer(f"[SERVER] 当前共有 {len(self.lottery_list)} 个需要去重")
        for lottery_id in self.lottery_list:
            if lottery_id in temp_lottery_list:
                continue
            data = self.get_lottery_info(lottery_id)
            # if data['status'] == 2:
            #     continue
            insert_data(data['uid'], data['event_msg'], data['event_id'],
                        data['lottery_id'], data['lottery_time'])
        self.lottery_list = []
        printer(f"[SERVER] 动态库存去重成功")

    # 去重扫描
    def repeat_lottery_scan(self):
        lottery_data = query_valid_db()
        temp_lottery_list = []
        for lottery in lottery_data:
            temp_lottery_list.append(lottery['lottery_id'])
        for lottery_id in temp_lottery_list:
            self.find_section(lottery_id)
        temp_lottery_list = query_lottery_id_db()
        printer(f"[SERVER] 当前共有 {len(self.pre_scan_list)} 个需要扫描")
        for index, lottery_id in enumerate(self.pre_scan_list):
            # if index % 99 == 0:
            #     asyncio.sleep(60)
            if lottery_id in temp_lottery_list:
                continue
            data = self.get_lottery_info(lottery_id)
            if data is None:
                continue
            insert_data(data['uid'], data['event_msg'], data['event_id'],
                        data['lottery_id'], data['lottery_time'])

        self.pre_scan_list = []
        printer(f"[SERVER] 动态去重扫描成功")

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
        printer(f"[CLIENT] forward -> {response}")

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
        printer(f"[CLIENT] follow -> {response}")

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
        printer(f"[CLIENT] unfollow -> {response}")

    # 过滤关键词 钓鱼测试
    def filter_keywords(self, desp):
        keys = [
            '禁言', '测试', 'vcf', '体验中奖', '中奖的感觉', '赶脚', '感脚', '感jio',
            '黑名单', '拉黑', '拉黑', '脸皮厚', '没有奖品', '无奖', '脸皮厚', 'ceshi',
            '测试', '脚本', '抽奖号', '不要脸', '至尊vip会员7天', '高级会员7天', '万兴神剪手',
            '测试', '加密', 'test', 'TEST', '钓鱼', '炸鱼', '调试'
        ]
        for key in keys:
            if key in desp:
                return False
        return True

    # 过滤关键词 奖品
    def filter_prizes(self, prizes):
        keys = [
            '编曲', '作词', '半价', '打折', '机器', '禁言', '测试', 'vcf', '体验中奖',
            '中奖的感觉', '录歌', '混音', '一毛', '0.1元', '1角', '0.5元', '5毛',
            '赶脚', '感脚', '曲风', '专辑封面', '封面', '一元红包', '感jio', '名片赞',
            '黑名单', '拉黑', '拉黑', '脸皮厚', '没有奖品', '无奖', '脸皮厚', 'ceshi',
            '测试', '脚本', '抽奖号', '不要脸', '至尊vip会员7天', '高级会员7天', '万兴神剪手',
            '测试', '加密', 'test', 'TEST', '钓鱼', '炸鱼', '调试', '歌曲定制', '学习修图',
            '学习视频', '修图视频', '作词', '免费编曲', '后期制作', '编曲搬家', '写一首歌',
            '内容自定', '音乐人一个', '私人唱歌'
        ]
        # 过滤 一等奖 奖品
        for prize in prizes:
            for key in keys:
                if key in prize['name']:
                    return False
            break
        return True

    # 概率性抽奖
    def filter_probability(self):
        pass

    # 过滤转发数据
    def filter_repost(self, lottery_id):
        data = self.get_lottery_info(lottery_id)
        # 动态存在异常
        if data is None:
            return False, '获取动态信息异常'
        # 动态存在异常关键字返回假
        if not self.filter_keywords(data['event_msg']):
            return False, '标题内容存在异常关键字'
        # 奖品存在异常
        if not self.filter_prizes(data['prizes']):
            return False, '奖品内容存在异常关键字'
        return True, None

    # 转发动态
    def repost(self):
        messages = [
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
        ]
        data = query_repost_db()
        for d in data:
            event_status, event_status_msg = self.filter_repost(
                d['lottery_id'])
            if not event_status:
                printer(
                    f"[CLIENT] 当前动态 {d['lottery_id']} {event_status_msg} 跳过!"
                )
                continue
            message = random.choice(messages)
            self.forward(d['event_id'], d['uid'], message)
            self.follow(d['uid'])

    # 删除动态
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
        printer(f"[CLIENT] del_event -> {response}")

    # 回滚
    def rollback(self):
        data = query_delete_db()
        for d in data:
            event_status, event_status_msg = self.filter_repost(
                d['lottery_id'])
            if not event_status:
                printer(
                    f"[CLIENT] 当前动态 {d['lottery_id']} {event_status_msg} 跳过!"
                )
                self.del_event(d['pre_event_id'])
                self.unfollow(d['uid'])
                update_delete_db(d['lottery_id'])
                continue

            if not self.win_check(d['lottery_id']):
                if (d['lottery_time'] + 5 * 60 * 60) > current_unix():
                    continue
                self.del_event(d['pre_event_id'])
                self.unfollow(d['uid'])
            update_delete_db(d['lottery_id'])

    # 中奖检测
    def win_check(self, lottery_id):
        url = f"http://music.163.com/api/lottery/event/get?lotteryId={lottery_id}"
        response = self.session.get(url).json()
        prize_ids = response['data']['lottery']['prizeId']
        prize_ids = prize_ids.strip('[').strip(']').split(',')

        for prize_id in prize_ids:
            data = response['data']['luckUsers'][prize_id]
            for d in data:
                if d['userId'] == int(user_id):
                    prizes = response['data']['prize']
                    for index, prize in enumerate(prizes):
                        if str(prize['id']) == prize_id:
                            prize_level = index + 1
                            prize_name = prize['name']

                    info = f"""亲爱的 [{username} -> {user_id}] 您好:  
        恭喜您在【{response['data']['user']['nickname']}】发布的动态互动抽奖活动中，喜获奖品啦!  
        >>> 互动抽奖{lottery_id} -> {prize_level}等奖 -> {prize_name}] <<<  
        请前往网易云音乐APP查看详情，尽快填写中奖信息或领取奖品。"""
                    #  (https://music.163.com/st/m#/lottery/detail?id={lottery_id})
                    # 提醒
                    notice_handler('网易云互动抽奖', info)
                    return True
        return False


if __name__ == '__main__':
    net_ease = NeteaseLottery()
    tasks = [
        net_ease.server(),
        net_ease.client()
    ]
    loop = asyncio.get_event_loop()
    loop.run_until_complete(asyncio.wait(tasks))
    loop.close()
