#!/usr/bin/env python3.6
# -*- coding: utf-8 -*-

import hashlib
import re
import random
import requests
from Util import EncryptParams, Printer
import faker

fake = faker.Faker(locale='zh_CN')


class NetEaseLogin:

    def __init__(self):
        self.ua_list = [
            'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_9_7 rv:2.0; ff-SN) AppleWebKit/531.5.1 (KHTML, like Gecko) Version/5.0.2 Safari/531.5.1',
            'Mozilla/5.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.1)',
            'Opera/8.14.(X11; Linux i686; lzh-TW) Presto/2.9.176 Version/10.00',
            'Opera/8.18.(Windows NT 5.01; ku-TR) Presto/2.9.181 Version/12.00',
            'Mozilla/5.0 (compatible; MSIE 5.0; Windows NT 4.0; Trident/4.1)',
            'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_9_5; rv:1.9.5.20) Gecko/2012-08-22 13:50:54 Firefox/11.0',
            'Opera/8.44.(Windows NT 4.0; da-DK) Presto/2.9.189 Version/11.00',
            'Mozilla/5.0 (Windows NT 6.0) AppleWebKit/5341 (KHTML, like Gecko) Chrome/35.0.899.0 Safari/5341',
            'Mozilla/5.0 (Windows; U; Windows 98; Win 9x 4.90) AppleWebKit/534.50.5 (KHTML, like Gecko) Version/5.1 Safari/534.50.5',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.12; rv:46.0) Gecko/20100101 Firefox/46.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_5) AppleWebKit/603.2.4 (KHTML, like Gecko) Version/10.1.1 Safari/603.2.4',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:46.0) Gecko/20100101 Firefox/46.0',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.135 Safari/537.36 Edge/13.10586',
            'Mozilla/5.0 (iPod; U; CPU iPhone OS 3_0 like Mac OS X; fr-CH) AppleWebKit/535.40.2 (KHTML, like Gecko) Version/4.0.5 Mobile/8B113 Safari/6535.40.2',
        ]
        self.headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin': 'https://music.163.com',
            'Referer': 'https://music.163.com/',
            'Cookie': 'os=pc',
            'User-Agent': random.choice(self.ua_list),
        }
        self.enc = EncryptParams()
        self.log = Printer()
        self.session = requests.Session()

    # 更新 Session
    def update_session(self):
        self.session.headers.update(
            {
                'Origin': 'https://music.163.com',
                'Referer': 'https://music.163.com/',
                'User-Agent': fake.user_agent(),
            }
        )
        # 利用RequestsCookieJar获取
        jar = requests.cookies.RequestsCookieJar()
        jar.set('os', random.choice(['pc', 'osx', 'android']))
        self.session.cookies.update(jar)
        return self.session

    # 邮箱登录
    def email_login(self, username, password):
        url = 'https://music.163.com/weapi/login?csrf_token='
        text = {
            'username': username,
            'password': password,
            'rememberLogin': 'true',
            'csrf_token': ''
        }
        payload = self.enc.get(text)
        try:
            return self.session.post(url, headers=self.headers, data=payload)
        except Exception as e:
            # print(e)
            return {'code': 501, 'msg': str(e)}

    # 手机登录
    def phone_login(self, username, password):
        url = 'https://music.163.com/weapi/login/cellphone'
        text = {
            'phone': username,
            'password': password,
            'rememberLogin': 'true',
            'csrf_token': ''
        }
        payload = self.enc.get(text)
        try:
            return self.session.post(url, headers=self.headers, data=payload)
        except Exception as e:
            return {'code': 501, 'msg': str(e)}

    # 登录
    def login(self, username, password):
        # printer(username, password)
        account_type = self.match_login_type(username)
        md5 = hashlib.md5()
        md5.update(password.encode('utf-8'))
        password = md5.hexdigest()

        # 为了后期考虑，暂时拆分登陆
        if account_type == 'phone':
            response = self.phone_login(username, password)
        else:
            response = self.email_login(username, password)
        # 判断字典
        if not isinstance(response, dict):
            json_resp = response.json()
        else:
            json_resp = response
        if json_resp['code'] == 200:
            self.log.printer(
                "LOGIN",
                f"Account -> {username}, login successfully..."
            )
            return self.update_session()
        elif json_resp['code'] == 501:
            self.log.printer(
                "LOGIN",
                f"[ERROR]: Account -> {username}, fail to login, {json_resp['msg']}..."
            )
        else:
            self.log.printer(
                "LOGIN",
                f"[ERROR]: Account -> {username}, fail to login, {json_resp}..."
            )
        return False

    # 匹配登录类型
    def match_login_type(self, username):
        # 正则方案
        pattern = re.compile(r'^1\d{2,3}\d{7,8}$|^1[34578]\d{9}$')
        return 'phone' if pattern.match(username) else 'email'
        # int报错方案
        # try:
        #     int(username)
        #     login_type = 'phone'
        # except:
        #     login_type = 'email'
        # return login_type


if __name__ == '__main__':
    pass
