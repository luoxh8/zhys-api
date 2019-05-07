#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
@Time    : 2017/10/19 下午3:52
@Author  : linjf
@File    : wftpay.py

Desc: app支付，威富通，微信支付，h5形式
'''

import hashlib
import random
import requests
import xml.etree.ElementTree as ET

from flask import request
from main_app.recharge.channels.base import BasePay


MCH_ID = '101510144553'  # 商户号
SECRET_KEY = 'ac8bdd9916e5c81c6e18606ac9d42c3c'  # 密钥
URL = 'https://pay.swiftpass.cn/pay/gateway'  # 请求URL

class WftPay(BasePay):
    SERVICE_CFG = ['wechat_h5']

    def post_order(self, user_id, order_id, money, notify_url, pay_type, **kwargs):
        post_data = {
            'service': 'pay.weixin.wappay',
            'mch_id': MCH_ID,
            'out_trade_no': order_id,
            'body': u'书币充值',
            'total_fee': money,
            'mch_create_ip': kwargs.get('ip', ''),
            'notify_url': notify_url,
            'device_info': 'AND_WAP' if kwargs.get('device_type') == 1 else 'iOS_WAP',
            'mch_app_id': 'http://www.kdyoushu.com',
            'mch_app_name': u'智慧有书',
            'nonce_str': get_nonce_str(),
        }
        post_data['sign'] = get_sign(post_data, SECRET_KEY)

        headers = {'content-type': 'application/xml'}
        resp = requests.post(URL, data=dict_to_xml(post_data), headers=headers)
        resp_data = xml_to_dict(resp.text)

        rtn_data = {}
        if resp_data['status'] == '0' and resp_data['result_code'] == '0':
            rtn_data['pay_url'] = resp_data['pay_info']

        return rtn_data

    def verify(self):
        rtn_data = {'code': 1, 'msg': '', 'order_id': '', 'money': 0, 'rtn_success': 'success', 'rtn_fail': 'fail'}

        data = xml_to_dict(request.data)

        if data.get('status', '') != '0' or data.get('result_code', '') != '0':
            rtn_data['msg'] = u'交易出错'
            return rtn_data

        local_sign = get_sign(data, SECRET_KEY)
        if local_sign != data.get('sign', ''):
            rtn_data['msg'] = u'签名出错'
            return rtn_data

        rtn_data['code'] = 0
        rtn_data['order_id'] = data.get('out_trade_no', '')
        rtn_data['money'] = int(data.get('total_fee', '0'))
        return rtn_data


def get_sign(params_map, key):
    """ 生成签名 """
    sort_list = []
    for key in params_map:
        if params_map.get(key) and key != 'sign':
            sort_list.append('%s=%s' % (key, params_map.get(key)))

    a = sorted(sort_list)
    sign_str = '&'.join(a) + '&key=%s' % SECRET_KEY
    return get_str_sign(sign_str)


def get_notify_sign(params_map, key):
    """ 生成签名 """
    sort_list = []
    if int(params_map.get('pay_result')) == 0:
        try:
            del params_map['token_id']
            del params_map['pay_info']
            del params_map['appid']
        except:
            pass

    for key in params_map:
        if params_map.get(key) and key != 'sign':
            sort_list.append('%s=%s' % (key, params_map.get(key)))

    a = sorted(sort_list)
    sign_str = '&'.join(a) + '&key=%s' % SECRET_KEY
    print sign_str
    return get_str_sign(sign_str)


def get_str_sign(sign_str):
    sign_str = hashlib.md5(sign_str).hexdigest()
    return sign_str.upper()


def dict_to_xml(data_dict):
    """ 字典转xml """
    xml = ['<xml>']
    for key, value in data_dict.iteritems():
        xml.append('<{0}>{1}</{0}>'.format(key, value))
    xml.append('</xml>')
    return ''.join(xml)


def xml_to_dict(xml):
    """ xml转字典 """
    data = {}
    root = ET.fromstring(xml)
    for child in root:
        data[child.tag] = child.text
    return data


def get_nonce_str(length=32):
    """ 生成随机字符串，不长于32位 """
    chars = "abcdefghijklmnopqrstuvwxyz0123456789"
    strs = []
    for x in range(length):
        strs.append(chars[random.randrange(0, len(chars))])
    return ''.join(strs)


wftpay = WftPay()
