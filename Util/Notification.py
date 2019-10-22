#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
- author: Lkeme
- contact: Useri@live.cn
- file: Notification
- time: 2019/10/21 20:33
- desc: 
"""
import requests
from Config.ConfigGetter import config
from Util import Printer
from retry import retry


class NotificationError(BaseException):
    pass


class Notification:
    def __init__(self):
        self.session = requests.Session()
        self.log = Printer()
        self.time_out = 30
        self.title = ''
        self.content = ''

    # 通知分发
    @retry(NotificationError, tries=5, delay=60)
    def notice_handler(self, title, content):
        notification = config.notification
        if not notification['enable']:
            return
        if notification['type'] not in notification.keys():
            return
        for key, value in notification[notification['type']].items():
            if not value:
                return
        self.title = title
        self.content = content
        if notification['type'] == 'server_chan':
            self.server_chan(
                notification['server_chan']['key']
            )
        elif notification['type'] == 'tg_bot':
            self.tg_bot(
                notification['tg_bot']['api'],
            )
        elif notification['type'] == 'personal':
            self.personal(
                notification['personal']['url'],
                notification['personal']['channel']
            )
        else:
            pass

    # server酱
    def server_chan(self, sc_key):
        try:
            url = f'https://sc.ftqq.com/{sc_key}.send'
            data = {
                'text': self.title,
                'desp': self.content
            }
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'Referer': 'http://sc.ftqq.com/?c=code',
            }
            response = self.session.post(
                url, headers=headers, data=data, timeout=self.time_out
            ).json()

            self.log.printer('SERVERCHAN', response)
            if response['errmsg'] == 'success':
                return
        except Exception as e:
            pass
        raise NotificationError("NotificationError")

    # tg_bot
    def tg_bot(self, url):
        try:
            data = {
                'text': f"{self.title}\r\n{self.content}"
            }
            response = self.session.post(
                url, data=data, timeout=self.time_out
            )
            self.log.printer('TGBOT', response.text)
            if response.status_code == 200:
                return True
        except Exception as e:
            pass
        raise NotificationError("NotificationError")

    # 自用
    def personal(self, url, channel):
        try:
            json = {
                "channelName": channel,
                "text": f"{self.title}\r\n{self.content}"
            }
            headers = {
                'content-type': 'application/json'
            }
            response = self.session.post(
                url, headers=headers, json=json, timeout=self.time_out
            ).json()
            # {"error":0,"message":"Done!"}
            self.log.printer('PERSONAL', response)
            if response['message'] == 'Done!':
                return True
        except Exception as e:
            pass
        raise NotificationError("NotificationError")


if __name__ == '__main__':
    n = Notification()
    n.notice_handler("测试标题", "测试内容")
