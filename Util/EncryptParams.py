#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
- author: Lkeme
- contact: Useri@live.cn
- file: EncryptParams
- time: 2019/10/21 17:47
- desc: 
"""
import os
import json
import codecs
import base64
from Crypto.Cipher import AES


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
