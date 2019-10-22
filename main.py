#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import re
import time
import random
import traceback
import asyncio
from Util.Function import current_unix
from Util import EncryptParams, Printer, NetEaseLogin, Notification
from Db.DbClient import DbClient
from Config.ConfigGetter import config
import faker

fake = faker.Faker(locale='zh_CN')


class NetEaseLottery:

    def __init__(self):
        # 加密 日志 数据库
        self.enc = EncryptParams()
        self.log = Printer()
        self.db = DbClient()
        # 数据表
        self.raw_event = 'raw_event'
        self.used_event = 'used_event'
        # pass
        self.session = None
        self.user_box = []
        self.lottery_list = []
        self.pre_scan_list = []
        self.designation_list = []
        self.lock = {
            'scan': 0,
        }
        self.__init_user_manager()

    # 初始化用户管理
    def __init_user_manager(self):
        if self.user_box and self.session:
            return
        temp = []
        accounts = config.user_accounts
        for account in accounts:
            if account['user_id'] in temp:
                continue
            for key, value in account.items():
                if not value or value == 'invalid':
                    break
            else:
                try:
                    account['session'] = self.login(
                        account['username'], account['password']
                    )
                    if account['type'] == 'default':
                        self.session = account['session']
                    self.user_box.append(account)
                except Exception as e:
                    self.log.printer("LOGIN", e)
                    continue
            temp.append(account['user_id'])
        if not self.user_box:
            exit("有效用户为0，请检查配置！")
        if not self.session:
            self.session = self.user_box[0]['session']
            self.user_box[0]['type'] = 'default'

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
                    self.log.printer("REQUEST", "出现错误 {e}")
                time.sleep(1)
        return None

    # 请求中心
    def _multi_requests(self, session, method, url, decode=2, retry=10,
                        timeout=15,
                        **kwargs):
        if method in ["get", "post"]:
            for _ in range(retry + 1):
                try:
                    response = getattr(session, method)(
                        url, timeout=timeout, **kwargs
                    )
                    return response.json() if decode == 2 else response.content if decode == 1 else response
                except Exception as e:
                    self.log.printer("MULTI_REQUEST", "出现错误 {e}")
                time.sleep(1)
        return None

    # 登陆
    def login(self, username, password):
        return NetEaseLogin().login(username=username, password=password)

    # 用户相关
    async def users(self):
        while True:
            try:
                user_len = len(self.user_box)
                for _ in range(user_len):
                    await asyncio.sleep(30)
                    user = self.user_box.pop(0)
                    survive_status = self.check_survive(user)
                    if not survive_status:
                        user = self.flush_session(user)
                    self.user_box.append(user)
                self.log.printer("SURVIVE", "休眠12小时后继续")
                await asyncio.sleep(12 * 60 * 60)
            except Exception as e:
                self.log.printer("SURVIVE", f"流程出错 {e},稍后重试")
                self.user_box.append(user)
                await asyncio.sleep(60)

    # 转发回滚
    async def client(self):
        while True:
            try:
                self.forward()
                self.rollback()
                self.log.printer("CLIENT", "休眠1小时后继续")
                await asyncio.sleep(60 * 60)
            except Exception as e:
                self.log.printer("CLIENT", f"流程出错 {e},稍后重试")
                await asyncio.sleep(60)

    # 迷你扫描
    async def mini_scan(self):
        while True:
            try:
                await asyncio.sleep(3 * 60)
                self.scan_lottery_id()
                self.repeat_lottery()
                self.log.printer("SERVER_MASTER", "休眠14小时后继续")
                await asyncio.sleep(14 * 60 * 60)
            except Exception as e:
                self.log.printer("SERVER_MASTER", f"流程出错 {e},稍后重试")
                await asyncio.sleep(60)

    # 完整扫描
    async def full_scan(self):
        while True:
            try:
                await asyncio.sleep(10 * 60)
                self.designation_section()
                self.repeat_lottery_scan()
                self.log.printer("SERVER_SLAVE", "休眠4小时后继续")
                await asyncio.sleep(4 * 60 * 60)
            except Exception as e:
                self.log.printer("SERVER_SLAVE", f"流程出错 {e},稍后重试")
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
        self.db.change_table(self.raw_event)
        temp_lottery_list = self.db.query_key('lottery_id')
        self.log.printer("M_SCAN", f"当前共有 {len(self.lottery_list)} 个动态抽奖需要去重")
        for lottery_id in self.lottery_list:
            time.sleep(2)
            if lottery_id in temp_lottery_list:
                continue
            data = self.fetch_lottery_info(lottery_id)
            # if data['status'] == 2:
            #     continue
            self.db.change_table(self.raw_event)
            self.db.insert_raw(
                data['uid'], data['event_msg'], data['event_id'],
                data['lottery_id'], data['lottery_time']
            )
        self.lottery_list = []
        self.log.printer("M_SCAN", f"动态抽奖库存去重完成")

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
                self.log.printer("M_SCAN", f'开始扫描 {act_id} 第 {page+1} 页')
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
                        params = self.enc.get(params)
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
                            self.log.printer(
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
                        self.log.printer("M_SCAN", f"扫描动态出现错误 {e}, 稍后重试!")

                if not response['more']:
                    break
        self.log.printer("M_SCAN",
                         f"此次扫描已结束,当前库存 {len(self.lottery_list)} 个未验证动态抽奖")

    # 分配扫描段
    def designation_section(self):
        if len(self.pre_scan_list) == 0:
            self.db.change_table(self.raw_event)
            lottery_data = self.db.query_valid()
            valid_lottery_list = []
            for lottery in lottery_data:
                valid_lottery_list.append(lottery['lottery_id'])
            for lottery_id in valid_lottery_list:
                self.calc_section(lottery_id)

        for _ in range(1000):
            if len(self.pre_scan_list) == 0:
                break
            self.designation_list.append(self.pre_scan_list.pop(0))
        self.log.printer(
            "F_SCAN",
            f"预备扫描 {len(self.pre_scan_list)} 分配扫描 {len(self.designation_list)}"
        )

    # 去重扫描
    def repeat_lottery_scan(self):
        self.db.change_table(self.raw_event)
        exist_lottery_list = self.db.query_key('lottery_id')
        self.log.printer("F_SCAN",
                         f"当前分配 {len(self.designation_list)} 个动态抽奖需要扫描")
        for lottery_id in self.designation_list:
            time.sleep(2)
            if lottery_id in exist_lottery_list:
                continue
            data = self.fetch_lottery_info(lottery_id)
            if data is None:
                continue
            self.db.change_table(self.raw_event)
            self.db.insert_raw(
                data['uid'], data['event_msg'], data['event_id'],
                data['lottery_id'], data['lottery_time']
            )

        self.designation_list = []
        self.log.printer("F_SCAN", f"动态抽奖去重扫描完成")

    # 生存检测
    def check_survive(self, user):
        url = f"http://music.163.com/api/lottery/event/get?lotteryId=1"
        try:
            response = user['session'].get(url).json()
            # {"code":301,"message":"系统错误","debugInfo":null}
            if response['code'] == 301:
                self.log.printer("SURVIVE", f"{user['username']} 存活检测 -> fail")
                return False
            self.log.printer("SURVIVE", f"{user['username']} 存活检测 -> success")
            return True
        except Exception as e:
            self.log.printer("SURVIVE", f"{user['username']} 存活检测 -> {e}")
            return None

    # 刷新session
    def flush_session(self, user):
        try:
            user['session'] = self.login(
                user['username'], user['password']
            )
            if user['type'] == 'default':
                self.session = user['session']
            self.log.printer(
                "SURVIVE",
                f"{user['username']} 刷新SESSION -> success"
            )
        except Exception as e:
            self.log.printer("SURVIVE", f"{user['username']} 刷新SESSION -> {e}")
        return user

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
                    'lottery_time': response['data']['lottery'][
                        'lotteryTime'],
                    'prizes': response['data']['prize'],
                    'status': response['data']['lottery']['status']
                }
                self.log.printer("LOTTERY_INFO", f"{lottery_id} -> 命中抽奖")
                return data
            elif response['code'] == 404:
                self.log.printer(
                    "LOTTERY_INFO",
                    f"{lottery_id} -> {response['message']}"
                )
            else:
                self.log.printer("LOTTERY_INFO",
                                 f"{lottery_id} -> {response}")
            return None
        except Exception as e:
            self.log.printer("LOTTERY_INFO", f"{lottery_id} -> {e}")
            # {"code":404,"message":"动态资源不存在","debugInfo":null}
            return None

    # 计算区间
    def calc_section(self, lottery_id):
        # TODO 代码待优化
        length = len(str(lottery_id)) - 1
        prefix = str(lottery_id)[0]
        start = int(prefix + "".join(['0' for _ in range(length)]))
        end = int(prefix + "".join(['9' for _ in range(length)])) + 2
        self.pre_scan_list = self.pre_scan_list + list(range(start, end))
        self.pre_scan_list = list(set(self.pre_scan_list))
        # 第二方案
        # self.pre_scan_list = list(set(self.pre_scan_list).union(set(list(range(start, end)))))
        # self.log.printer(f"当前区间 {start},{end} 已有数据 {len(self.pre_scan_list)}")

    # 转发
    def publish(self, user, raw_event_id, event_id, event_uid, msg):
        try:
            csrf = self.get_csrf(user)
            url = f"http://music.163.com/weapi/event/forward?csrf_token={csrf}"
            params = {
                "forwards": msg,
                "id": event_id,
                "eventUserId": event_uid,
                "checkToken": "",
                "csrf_token": csrf
            }
            params = self.enc.get(params)
            response = user['session'].post(url, params=params).json()
            self.log.printer("FORWARD", response)
            self.db.change_table(self.used_event)
            self.db.insert_used(
                user['username'], response['data']['eventId'], raw_event_id
            )
            url = f'http://music.163.com/weapi/feedback/weblog?csrf_token={csrf}'
            params = {
                "logs": '[{"action": "eventclick","json":{"id": %s,"sourceid": %s,"alg": "","contentType": "user_event","actionType": "forward"}}]' % (
                    event_id, event_uid),
                "csrf_token": csrf
            }
            params = self.enc.get(params)
            response = user['session'].post(url, params=params).json()
            self.log.printer("FORWARD", response)
        except Exception as e:
            self.log.printer("FORWARD", f"{response} -> {e}")
            return False
        return True

    # 获取csrf
    def get_csrf(self, user):
        return (user['session'].cookies.get_dict())['__csrf']

    # 关注
    def follow(self, user, follow_uid):
        csrf = self.get_csrf(user)
        url = f"http://music.163.com/weapi/user/follow/{follow_uid}?csrf_token={csrf}"
        user['session'].headers.update(
            {
                'Host': 'music.163.com',
                'Origin': 'http://music.163.com',
                'Referer': f"http://music.163.com/user/home?id={follow_uid}",
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36',
            }
        )
        params = {
            "followId": follow_uid,
            "checkToken": "",
            "csrf_token": csrf
        }
        params = self.enc.get(params)
        response = user['session'].post(url, params=params)
        self.log.printer("FOLLOW", response.json())

    # 取消关注
    def un_follow(self, user, follow_uid):
        csrf = self.get_csrf(user)
        url = f'http://music.163.com/weapi/user/delfollow/{follow_uid}?csrf_token={csrf}'
        params = {
            "followId": follow_uid,
            "csrf_token": csrf
        }
        params = self.enc.get(params)
        response = user['session'].post(url, params=params).json()
        self.log.printer("UN_FOLLOW", response)

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
            '管饱', 'dong tai ga', '电话唱歌', '感谢转发'
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
    def forward(self):
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
        self.db.change_table(self.raw_event)
        data = self.db.query_forward()
        for d in data:
            event_status, status_msg = self.filter_repost(d['lottery_id'])
            if not event_status:
                self.log.printer(
                    "REPOST", f"当前动态 {d['lottery_id']} {status_msg} 跳过"
                )
                continue
            for user in self.user_box:
                message = random.choice(messages)
                status = self.publish(user, d['id'], d['event_id'], d['uid'],
                                      message)
                if status:
                    self.follow(user, d['uid'])
            self.db.change_table(self.raw_event)
            self.db.update_raw_reposted(d['lottery_id'])

    # 删除动态
    def del_event(self, user, event_id):
        csrf = self.get_csrf(user)
        url = f'http://music.163.com/weapi/event/delete?csrf_token={csrf}'
        params = {
            "type": "delete",
            "id": event_id,
            "transcoding": "false",
            "csrf_token": csrf
        }
        params = self.enc.get(params)
        response = user['session'].post(url, params=params).json()
        self.log.printer("DEL_EVENT", response)

    # 回滚
    def rollback(self):
        self.db.change_table(self.raw_event)
        data = self.db.query_delete()
        for d in data:
            event_status, status_msg = self.filter_repost(d['lottery_id'])
            for user in self.user_box:
                if not event_status:
                    self.log.printer(
                        "ROLLBACK", f"当前动态 {d['lottery_id']} {status_msg} 跳过"
                    )
                    self.db.change_table(self.used_event)
                    pre_d = self.db.query_pre_event(user['username'], d['id'])
                    if pre_d is not None:
                        self.del_event(user, pre_d[0])
                        self.un_follow(user, d['uid'])
                    continue

                if not self.win_check(user, d['lottery_id']):
                    if (d['lottery_time'] + 5 * 60 * 60) > current_unix():
                        continue
                    self.db.change_table(self.used_event)
                    pre_d = self.db.query_pre_event(user['username'], d['id'])
                    if pre_d is not None:
                        self.del_event(user, pre_d[0])
                        self.un_follow(user, d['uid'])
            self.db.change_table(self.raw_event)
            self.db.update_raw_deleted(d['lottery_id'])

    # 中奖检测
    def win_check(self, user, lottery_id):
        url = f"http://music.163.com/api/lottery/event/get?lotteryId={lottery_id}"
        response = self.session.get(url).json()
        prize_ids = response['data']['lottery']['prizeId']
        prize_ids = prize_ids.strip('[').strip(']').split(',')

        for prize_id in prize_ids:
            data = response['data']['luckUsers'][prize_id]
            for d in data:
                if d['userId'] == int(user['user_id']):
                    prizes = response['data']['prize']
                    for index, prize in enumerate(prizes):
                        if str(prize['id']) == prize_id:
                            prize_level = index + 1
                            prize_name = prize['name']

                    info = f"""亲爱的 [{user['username']} -> {user['user_id']}] 您好:  
    恭喜您在【{response['data']['user']['nickname']}】发布的动态互动抽奖活动中，喜获奖品啦!  
    >>> 互动抽奖{lottery_id} -> {prize_level}等奖 -> {prize_name}] <<<  
    请前往网易云音乐APP查看详情，尽快填写中奖信息或领取奖品。"""
                    self.log.printer("WIN", info)
                    #  (https://music.163.com/st/m#/lottery/detail?id={lottery_id})
                    # 中奖提醒
                    Notification().notice_handler('网易云互动抽奖', info)
                    return True
        return False


if __name__ == '__main__':
    net_ease = NetEaseLottery()
    tasks = [
        net_ease.client(),
        net_ease.users(),
        net_ease.mini_scan(),
        net_ease.full_scan()
    ]
    loop = asyncio.get_event_loop()
    loop.run_until_complete(asyncio.wait(tasks))
    loop.close()
