#!/usr/bin/env python
# -*- coding: utf-8 -*-
import requests
import os
import time
import re


class login(object):

    def __init__(self):
        print u'登录初始化……'
        self.qrcodepath = './qrcode.png'
        headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; MSIE 10.0; Windows Phone 8.0; Trident/6.0; IEMobile/10.0; ARM; Touch; NOKIA; Lumia 520)'
        }
        self.requesr_session = requests.Session()
        self.requesr_session.headers.update(headers)

        payload = {
            'daid': 5,
            'hide_title_bar': 1,
            'low_login': 0,
            'qlogin_auto_login': 1,
            'no_verifyimg': 1,
            'link_target': 'blank',
            'appid': 549000912,
            'style': 22,
            'target': 'self',
            's_url': 'http://qzs.qq.com/qzone/v5/loginsucc.html?para=izone',
            'daid': 5,
            'hide_title_bar': 1,
            'low_login': 0,
            'qlogin_auto_login': 1,
            'no_verifyimg': 1,
            'link_target': 'blank',
            'appid': 549000912,
            'style': 22,
            'target': 'self',
            's_url': 'http://qzs.qq.com/qzone/v5/loginsucc.html?para=izone'
        }
        init_request = self.requesr_session.get(
            'http://xui.ptlogin2.qq.com/cgi-bin/xlogin', params=payload)
        init_request.raise_for_status()
        self.requesr_session.headers.update({'Referer': init_request.url})

    def _getqrcode(self):
        print u'获取二维码……'
        path = self.qrcodepath
        payload = {
            'appid': 549000912,
            'e': 2,
            'l': 'M',
            's': 3,
            'd': 72,
            'v': 4,
            'daid': 5
        }
        qrcode_request = self.requesr_session.get(
            'http://ptlogin2.qq.com/ptqrshow', params=payload, stream=True)
        qrcode_request.raise_for_status()
        if qrcode_request.status_code == 200:
            with open(path, 'wb') as data:
                for chunk in qrcode_request.iter_content(chunk_size=1024):
                    data.write(chunk)

    def _polling(self):
        payload = {
            'u1': 'http://qzs.qq.com/qzone/v5/loginsucc.html?para=izone',
            'ptredirect': 0,
            'h': 1,
            't': 1,
            'g': 1,
            'from_ui': 1,
            'ptlang': 2052,
            'js_ver': 10140,
            'js_type': 1,
            'pt_uistyle': 32,
            'aid': 549000912,
            'daid': 5,
            'login_sig': self.requesr_session.cookies['pt_login_sig']
        }
        startime = int(time.time()) * 1000
        while True:
            payload['action'] = '0-0-%s' % (int(time.time()) * 1000 - startime)
            polling_request = self.requesr_session.get(
                'http://ptlogin2.qq.com/ptqrlogin', params=payload)
            ret = polling_request.text.split("'")[1]
            # 66 未失效 67 验证中 65 失效 0 成功
            if ret == '66':
                print u'请扫描二维码……'
            elif ret == '0':
                print u'验证成功,登录中……'
                callbackurl = polling_request.text.split("'")[5]
                return callbackurl
            elif ret == '65':
                print u'二维码已失效'
                return
            time.sleep(2)

    def getg_tk(self):
        skey = self.requesr_session.cookies['skey']
        hash = 5381
        for x in xrange(len(skey)):
            hash += (hash << 5) + ord(skey[x])
        self.g_tk = int(hash & 2147483647)
        return self.g_tk  # 0x7FFFFFFF

    def run(self):
        while True:
            self._getqrcode()
            callbackurl = self._polling()
            if callbackurl:
                os.remove(self.qrcodepath)
                break
        callback = self.requesr_session.get(callbackurl)
        if callback.history:  # 没有两步验证 直接302跳转
            self.uin = re.compile('uin=(\d+)').search(callbackurl).group(1)
            self.getg_tk()
            print u'登录成功。'
        else:  # 等待二次验证 不会跳转
            print u'不支持二次验证'
