#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
import codecs
import base64
import hashlib
import time
import requests
from Crypto.Cipher import AES


def printer(info, *args):
    at_now = int(time.time())
    time_arr = time.localtime(at_now)
    format_time = time.strftime("%Y-%m-%d %H:%M:%S", time_arr)
    # flag = "," if len(args) else " "
    content = f'[{format_time}] {info} {" ".join(f"{str(arg)}" for arg in args)}'
    print(content)


class EncryptParams():

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


class NeteaseLogin():
    def __init__(self, **kwargs):
        self.login_headers = {
            'Accept': '*/*',
            'Accept-Language': 'zh-CN,zh;q=0.8,gl;q=0.6,zh-TW;q=0.4',
            'Connection': 'keep-alive',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Referer': 'http://music.163.com',
            'Host': 'music.163.com',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.119 Safari/537.36'
        }
        self.login_url_email = 'http://music.163.com/weapi/login?csrf_token='
        self.login_url_phone = 'http://music.163.com/weapi/login/cellphone?csrf_token='
        self.enc = EncryptParams()
        self.session = requests.Session()

    '''登录函数'''

    def login(self, username, password, version='pc'):
        printer(username, password)
        if version == 'mobile':
            return None
        elif version == 'pc':
            account_type = self.__getAccountType(username)
            md5 = hashlib.md5()
            md5.update(password.encode('utf-8'))
            password = md5.hexdigest()
            data = {
                'password': password,
                'rememberLogin': True
            }
            if account_type == 'phone':
                data['phone'] = username
                data = self.enc.get(data)
                res = self.session.post(self.login_url_phone,
                                        headers=self.login_headers, data=data)
            else:
                data['username'] = username
                data = self.enc.get(data)
                res = self.session.post(self.login_url_phone,
                                        headers=self.login_headers, data=data)
            if res.json()['code'] == 200:
                print(
                    '[INFO]: Account -> %s, login successfully...' % username)
                return self.session
            else:
                raise RuntimeError(
                    'Account -> %s, fail to login, username or password error...' % username)
        else:
            raise ValueError(
                'Unsupport argument in music163.login -> version %s, expect <mobile> or <pc>...' % version)

    '''获取账号类型(手机号/邮箱)'''

    def __getAccountType(self, username):
        try:
            int(username)
            account_type = 'phone'
        except:
            account_type = 'email'
        return account_type


if __name__ == '__main__':
    session = NeteaseLogin().login('', '')
    params = EncryptParams().get('')
