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
        printer("SERVERNOTIFY", e)
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
        printer("SERVERCHAN", e)
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
        printer("DB", "更新删除数据库完毕")


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
    lottery_id_list = [row['lottery_id'] for row in row_list]
    return lottery_id_list


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
    printer("DB", f"查询有效数据库完毕 data->{len(row_list)}")

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

    printer("DB", f"查询删除数据库完毕 data->{len(row_list)}")
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
    printer("DB", f" 查询转发数据库完毕 data->{len(row_list)}")

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
        printer("DB", "更新转发数据库完毕")


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
        printer("DB", "插入数据库成功")

    except Exception as e:
        traceback.print_exc()
        printer("DB", f"插入数据库出错 {e}")
        # 错误回滚
        db.rollback()
    finally:
        db.close()


class NetEaseLottery:

    def __init__(self):
        self.session = NeteaseLogin().login(username, password)
        # self.session = requests.Session()
        self.enc_params = EncryptParams()
        self.lottery_list = []
        self.pre_scan_list = []
        self.designation_list = []
        self.session.headers.update(
            {
                'User-Agent': 'NeteaseMusic/5.9.1.1551789389(137);Dalvik/2.1.0 (Linux; U; Android 6.0.1; oneplus a5010 Build/V417IR)',
                'Host': 'music.163.com',
            }
        )
        self.lock = {
            'scan': 0,
        }

    # 请求中心
    def _requests(self, method, url, decode=2, retry=10, timeout=15, **kwargs):
        if method in ["get", "post"]:
            for _ in range(retry + 1):
                try:
                    response = getattr(self.session, method)(
                        url, timeout=timeout, **kwargs
                    )
                    return response.json() if decode == 2 else response.content if decode == 1 else response
                except Exception as e:
                    printer("REQUEST", "出现错误 {e}")
                time.sleep(1)
        return None

    # 转发回滚
    async def client(self):
        while True:
            try:
                self.repost()
                self.rollback()
                printer("CLIENT", "休眠1小时后继续")
                await asyncio.sleep(60 * 60)
            except Exception as e:
                printer("CLIENT", f"流程出错 {e},稍后重试")
                await asyncio.sleep(60)

    # 迷你扫描
    async def mini_scan(self):
        while True:
            try:
                await asyncio.sleep(3 * 60)
                self.scan_lottery_id()
                self.repeat_lottery()
                printer("SERVER_MASTER", "休眠14小时后继续")
                await asyncio.sleep(14 * 60 * 60)
            except Exception as e:
                printer("SERVER_MASTER", f"流程出错 {e},稍后重试")
                await asyncio.sleep(60)

    # 完整扫描
    async def full_scan(self):
        while True:
            try:
                await asyncio.sleep(10 * 60)
                self.designation_section()
                self.repeat_lottery_scan()
                printer("SERVER_SLAVE", "休眠4小时后继续")
                await asyncio.sleep(4 * 60 * 60)
            except Exception as e:
                printer("SERVER_SLAVE", f"流程出错 {e},稍后重试")
                await asyncio.sleep(60)

    # 字符匹配抽奖id
    def match_lottery_id(self, json_data):
        pattern = r'\"lotteryId\":(\d+),\"status\":(\d)'
        str_data = str(json_data) \
            .replace(" ", "") \
            .replace("\n", "") \
            .replace("\r", "")
        return re.findall(pattern, str_data)

    # 去重
    def repeat_lottery(self):
        temp_lottery_list = query_lottery_id_db()
        printer("M_SCAN", f"当前共有 {len(self.lottery_list)} 个动态抽奖需要去重")
        for lottery_id in self.lottery_list:
            time.sleep(2)
            if lottery_id in temp_lottery_list:
                continue
            data = self.fetch_lottery_info(lottery_id)
            # if data['status'] == 2:
            #     continue
            insert_data(data['uid'], data['event_msg'], data['event_id'],
                        data['lottery_id'], data['lottery_time'])
        self.lottery_list = []
        printer("M_SCAN", f"动态抽奖库存去重完成")

    # 扫描动态
    def scan_lottery_id(self):
        url = 'http://music.163.com/weapi/act/event?csrf_token='
        scan_page = 10
        max_page = '100'
        last_time = '-1'
        act_ids = {
            '互动抽奖': '44196506',
            '抽奖活动': '17731067',
            '转发抽奖': '20397151',
            '抽奖福利': '19873053',
            '粉丝福利': '3753053'
        }
        for act_id in act_ids.keys():
            for page in range(0, scan_page):
                printer("M_SCAN", f'开始扫描 {act_id} 第 {page+1} 页')
                while True:
                    try:
                        params = {
                            "actid": act_ids[act_id],
                            "total": "true",
                            "limit": "20",
                            "lasttime": last_time,
                            "pagesize": max_page,
                            "getcounts": "true",
                            "csrf_token": ""
                        }
                        params = self.enc_params.get(params)
                        response = self.session.post(url, params=params).json()
                        # 匹配 未过滤
                        match_data_all = self.match_lottery_id(response)

                        for match_data in match_data_all:
                            try:
                                lottery_id = int(match_data[0])
                                lottery_status = int(match_data[1])
                            except Exception as e:
                                continue
                            status = 'valid' if lottery_status == 1 else 'invalid'
                            printer(
                                "M_SCAN",
                                f"title: {act_id}, lotteryId: {lottery_id}, status: {status}"
                            )
                            if lottery_id in self.lottery_list:
                                # or lottery_status == 2:
                                continue

                            self.lottery_list.append(lottery_id)
                        last_time = response['lasttime']
                        break
                    except Exception as e:
                        traceback.print_exc()
                        printer("M_SCAN", f"扫描动态出现错误 {e}, 稍后重试!")

                if not response['more']:
                    break
        printer("M_SCAN", f"此次扫描已结束,当前库存 {len(self.lottery_list)} 个未验证动态抽奖")

    # 分配扫描段
    def designation_section(self):
        if len(self.pre_scan_list) == 0:
            lottery_data = query_valid_db()
            valid_lottery_list = []
            for lottery in lottery_data:
                valid_lottery_list.append(lottery['lottery_id'])
            for lottery_id in valid_lottery_list:
                self.calc_section(lottery_id)

        for _ in range(1000):
            if len(self.pre_scan_list) == 0:
                break
            self.designation_list.append(self.pre_scan_list.pop(0))
        printer(
            "F_SCAN",
            f"预备扫描 {len(self.pre_scan_list)} 分配扫描 {len(self.designation_list)}"
        )

    # 去重扫描
    def repeat_lottery_scan(self):
        exist_lottery_list = query_lottery_id_db()
        printer("F_SCAN", f"当前分配 {len(self.designation_list)} 个动态抽奖需要扫描")
        for lottery_id in self.designation_list:
            time.sleep(2)
            if lottery_id in exist_lottery_list:
                continue
            data = self.fetch_lottery_info(lottery_id)
            if data is None:
                continue
            insert_data(data['uid'], data['event_msg'], data['event_id'],
                        data['lottery_id'], data['lottery_time'])

        self.designation_list = []
        printer("F_SCAN", f"动态抽奖去重扫描完成")

    # 取动态抽奖信息
    def fetch_lottery_info(self, lottery_id):
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
                printer("LOTTERY_INFO", f"{lottery_id} -> 命中抽奖")
                return data
            elif response['code'] == 404:
                printer(
                    "LOTTERY_INFO",
                    f"{lottery_id} -> {response['message']}"
                )
            else:
                printer("LOTTERY_INFO", f"{lottery_id} -> {response}")
            return None
        except Exception as e:
            printer("LOTTERY_INFO", f"{lottery_id} -> {e}")
            # {"code":404,"message":"动态资源不存在","debugInfo":null}
            return None

    # 计算区间
    def calc_section(self, lottery_id):
        # TODO 代码丑陋 待优化
        length = len(str(lottery_id)) - 1
        prefix = str(lottery_id)[0]
        start = int(prefix + "".join(['0' for _ in range(length)]))
        end = int(prefix + "".join(['9' for _ in range(length)])) + 2
        self.pre_scan_list = self.pre_scan_list + list(range(start, end))
        self.pre_scan_list = list(set(self.pre_scan_list))
        # 第二方案
        # self.pre_scan_list = list(set(self.pre_scan_list).union(set(list(range(start, end)))))
        # printer(f"当前区间 {start},{end} 已有数据 {len(self.pre_scan_list)}")

    # 转发
    def forward(self, event_id, event_uid, msg):
        try:
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
            printer("FORWARD", response)
            update_repost_db(event_id, response['data']['eventId'])
            url = 'http://music.163.com/weapi/feedback/weblog'
            params = {
                "logs": [
                    {
                        "action": "eventclick",
                        "json": {"id": event_id, "sourceid": event_uid,
                                 "alg": "",
                                 "contentType": "user_event",
                                 "actionType": "forward"}}
                ],
                "csrf_token": ""
            }
            params = self.enc_params.get(params)
            response = self.session.post(url, params=params).json()
            printer("FORWARD", response)
        except Exception as e:
            printer("FORWARD", f"{response} -> {e}")
            return False
        return True

    # 关注
    def follow(self, follow_uid):
        user_info = self.session.cookies.get_dict()
        url = f"http://music.163.com/weapi/user/follow/{follow_uid}?csrf_token={user_info['__csrf']}"
        params = {
            "followId": follow_uid,
            "checkToken": "",
            "csrf_token": user_info['__csrf']
        }
        params = self.enc_params.get(params)
        response = self.session.post(url, params=params).json()
        printer("FOLLOW", response)

    # 取消关注
    def un_follow(self, follow_uid):
        user_info = self.session.cookies.get_dict()
        url = f'http://music.163.com/weapi/user/delfollow/{follow_uid}?csrf_token='
        params = {
            "followId": follow_uid,
            "csrf_token": user_info['__csrf']
        }
        params = self.enc_params.get(params)
        response = self.session.post(url, params=params).json()
        printer("UN_FOLLOW", response)

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
            '黑名单', '拉黑', '拉黑', '脸皮厚', '没有奖品', '无奖', '脸皮厚',
            '测试', '脚本', '抽奖号', '不要脸', '至尊vip会员7天', '高级会员7天',
            '测试', '加密', 'test', 'TEST', '钓鱼', '炸鱼', '调试', '歌曲定制',
            '学习视频', '修图视频', '作词', '免费编曲', '后期制作', '编曲搬家',
            '内容自定', '音乐人一个', '私人唱歌', '感恩', '作业', '八字', '算命',
            '电台', '情感视频', '万兴神剪手', '学习修图', '写一首歌', 'ceshi',
        ]
        # 过滤 一等奖 奖品
        for prize in prizes:
            for key in keys:
                if key in prize['name']:
                    return False
            break
        return True

    # 过滤404动态
    def filter_dynamic(self, event_id):
        pass

    # 概率性抽奖
    def filter_probability(self):
        pass

    # 过滤转发数据
    def filter_repost(self, lottery_id):
        data = self.fetch_lottery_info(lottery_id)
        # 抽奖存在异常
        if data is None:
            return False, '获取动态抽奖信息异常'
        # 抽奖存在异常关键字返回假
        if not self.filter_keywords(data['event_msg']):
            return False, '标题内容存在异常关键字'
        # 抽奖奖品存在异常
        if not self.filter_prizes(data['prizes']):
            return False, '奖品内容存在异常关键字'
        return True, None

    # 转发动态
    def repost(self):
        messages = [
            '转发动态', '转发动态', '', '好运来', '啊~', '哈哈哈', '抽奖奖(⌒▽⌒)',
            '中奖绝缘体', '绝缘体', '求脱非入欧', '好运', '中奖绝缘体表示想中！',
            '呜呜呜非洲人来了', '选我吧', '一定会中', '好运bufff', '滴滴滴', '哇哇哇哇',
            '拉低中奖率', '万一呢', '非酋日常', '加油', '抽中吧', '我要', '想欧一次！',
            '拉低中奖率233', '想要...', '路过拉低中奖率', '希望有个好运气',
            '中奖', '什么时候才会抽到我呢？', '试试水，看看能不能中', '过来水一手',
            '这辈子都不可能中奖的', '先拉低中奖率23333', '先抽奖，抽不到再说',
            '嘤嘤嘤', '捞一把', '我就想中一次', '拉低拉低', '试一试', '搞一搞',
            '中奖什么的不可能的（￣▽￣）', '听说我中奖了？', '脱非转欧', 'emm',
        ]
        data = query_repost_db()
        for d in data:
            event_status, status_msg = self.filter_repost(d['lottery_id'])
            if not event_status:
                printer(
                    "REPOST", f"当前动态 {d['lottery_id']} {status_msg} 跳过"
                )
                continue
            message = random.choice(messages)
            status = self.forward(d['event_id'], d['uid'], message)
            if status:
                self.follow(d['uid'])

    # 删除动态
    def del_event(self, event_id):
        user_info = self.session.cookies.get_dict()
        url = 'http://music.163.com/weapi/event/delete'
        params = {
            "type": "delete",
            "id": event_id,
            "transcoding": "false",
            "csrf_token": user_info['__csrf']
        }
        params = self.enc_params.get(params)
        response = self.session.post(url, params=params).json()
        printer("DEL_EVENT", response)

    # 回滚
    def rollback(self):
        data = query_delete_db()
        for d in data:
            event_status, status_msg = self.filter_repost(d['lottery_id'])
            if not event_status:
                printer(
                    "ROLLBACK", f"当前动态 {d['lottery_id']} {status_msg} 跳过"
                )
                self.del_event(d['pre_event_id'])
                self.un_follow(d['uid'])
                update_delete_db(d['lottery_id'])
                continue

            if not self.win_check(d['lottery_id']):
                if (d['lottery_time'] + 5 * 60 * 60) > current_unix():
                    continue
                self.del_event(d['pre_event_id'])
                self.un_follow(d['uid'])
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
    net_ease = NetEaseLottery()
    tasks = [
        net_ease.client(),
        net_ease.mini_scan(),
        net_ease.full_scan()
    ]
    loop = asyncio.get_event_loop()
    loop.run_until_complete(asyncio.wait(tasks))
    loop.close()
