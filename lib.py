#!/usr/bin/env python3.6
# -*- coding: utf-8 -*-

import os
import json
import codecs
import base64
import hashlib
import re
import random
import time
import requests
from Crypto.Cipher import AES


# 格式化打印
def printer(genre, info, *args):
    at_now = int(time.time())
    time_arr = time.localtime(at_now)
    format_time = time.strftime("%Y-%m-%d %H:%M:%S", time_arr)
    # flag = "," if len(args) else " "
    content = f'[{format_time}] [{genre}] {info} {" ".join(f"{str(arg)}" for arg in args)}'
    print(content)


# 参数加解密
class EncryptParams:

    def __init__(self):
        self.modulus = '00e0b509f6259df8642dbc35662901477df22677ec152b5ff68ace615bb7b725152b3ab17a876aea8a5aa76d2e417629ec4ee341f56135fccf695280104e0312ecbda92557c93870114af6c9d05c4f7f0c3685b7a46bee255932575cce10b424d813cfe4875d3e82047b97ddef52741d546b8e289dc6935b3ece0462db0a22b8e7'
        self.nonce = '0CoJUm6Qyw8W8jud'
        self.pubKey = '010001'

    def get(self, text):
        text = json.dumps(text)
        secKey = self._createSecretKey(16)
        encText = self._aesEncrypt(self._aesEncrypt(text, self.nonce), secKey)
        encSecKey = self._rsaEncrypt(secKey, self.pubKey, self.modulus)
        post_data = {
            'params': encText,
            'encSecKey': encSecKey
        }
        return post_data

    def _aesEncrypt(self, text, secKey):
        pad = 16 - len(text) % 16
        if isinstance(text, bytes):
            text = text.decode('utf-8')
        text = text + str(pad * chr(pad))
        secKey = secKey.encode('utf-8')
        encryptor = AES.new(secKey, 2, b'0102030405060708')
        text = text.encode('utf-8')
        ciphertext = encryptor.encrypt(text)
        ciphertext = base64.b64encode(ciphertext)
        return ciphertext

    def _rsaEncrypt(self, text, pubKey, modulus):
        text = text[::-1]
        rs = int(codecs.encode(text.encode('utf-8'), 'hex_codec'), 16) ** int(
            pubKey, 16) % int(modulus, 16)
        return format(rs, 'x').zfill(256)

    def _createSecretKey(self, size):
        return (''.join(
            map(lambda xx: (hex(ord(xx))[2:]), str(os.urandom(size)))))[0:16]


class NeteaseLogin:

    def __init__(self, **kwargs):
        self.ua_list = [
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.12; rv:46.0) Gecko/20100101 Firefox/46.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_5) AppleWebKit/603.2.4 (KHTML, like Gecko) Version/10.1.1 Safari/603.2.4',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:46.0) Gecko/20100101 Firefox/46.0',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.135 Safari/537.36 Edge/13.10586'
        ]
        self.headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin': 'https://music.163.com',
            'Referer': 'https://music.163.com/',
            'Cookie': 'os=pc',
            'User-Agent': random.choice(self.ua_list)
        }
        self.enc = EncryptParams()
        self.session = requests.Session()

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
            printer("LOGIN", f"Account -> {username}, login successfully...")
            return self.session
        elif json_resp['code'] == 501:
            raise RuntimeError(
                f"[ERROR]: Account -> {username}, fail to login, {json_resp['msg']}..."
            )
        else:
            raise RuntimeError(
                f"[ERROR]: Account -> {username}, fail to login, {json_resp}..."
            )

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
