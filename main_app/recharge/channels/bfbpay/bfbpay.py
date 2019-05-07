#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Doc: 
@author: MT
@time: 2017/2/28
"""
import hashlib
import base64
import binascii
import requests
from flask import request
from main_app.recharge.channels.base import BasePay

#APP_ID = '11147'  # 产品编号
#PARA_ID = '11000'  # 商户编号
#SECRET_KEY = 'ffb4ca96bde4bd67ff7c1bff168db265'
# 新建账号-20170928-linjf
APP_ID = '11246'  # 产品编号
PARA_ID = '11054'  # 商户编号
SECRET_KEY = 'd3a7d450d3aa0ea96b9af5ee485350b6'
API_URL_BANK = 'http://lftpay.jieshenkj.com/Kuaijie/shortpay'
API_URL_QQ = 'http://pay.jieshenkj.com:8080/shouq_pay/pfqq_h5pay'
API_URL_WECHAT = 'http://lftpay.jieshenkj.com/wx_pay/pufawxh5'
API_URL_NEW = 'http://lftpay.jieshenkj.com/sdk_transform/Pay_api'


class BfbPay(BasePay):
    SERVICE_CFG = ['alipay', 'wechat', 'bank', 'qq']

    def post_order(self, user_id, order_id, money, notify_url, pay_type, **kwargs):
        order_id = compact_order_id(kwargs.get('_order_id').bytes)
        post_data = {
            'body': "书币充值",
            'total_fee': money,
            'version': "Pa2.5",
            'app_id': APP_ID,
            'para_id': PARA_ID,
            'order_no': order_id,
            'notify_url': notify_url,
            'pay_type': 1,
            'userIdentity': user_id,
            'child_para_id': 1,
            'device_id': kwargs.get('device_type', ''),
            'device_info': user_id,
            'mch_app_id': 'kdjp',
            'mch_app_name': 'kdjp',
            'attach': '',
        }
        post_data['sign'] = get_sign(post_data, SECRET_KEY)
        rtn_data = {}
        if pay_type == 'bank':
            rtn_data['pay_url'] = post_bank_order(post_data)
        elif pay_type == 'qq':
            rtn_data['pay_url'] = post_qq_order(post_data)
        elif pay_type == 'wechat':
            rtn_data['pay_url'] = post_wechat_order(post_data)
        elif pay_type == 'alipay':
            rtn_data['rtn_json'] = post_alipay_order(post_data)
        return rtn_data

    def verify(self):
        rtn_data = {'code': 1, 'msg': '', 'order_id': '', 'money': 0, 'rtn_success': 'ok', 'rtn_fail': 'fail'}

        sign = request.args.get('sign')
        order_id = request.args.get('orderno', '', str)
        money = request.args.get('fee', 0, int)

        if not order_id or not money:
            rtn_data['msg'] = 'args error'
            return rtn_data

        _sign = get_str_sign(order_id + str(money) + SECRET_KEY)
        if sign != _sign:
            print _sign
            rtn_data['msg'] = 'sign error'
            return rtn_data

        order_id = extract_order_id(order_id)
        rtn_data['code'] = 0
        rtn_data['order_id'] = order_id
        rtn_data['money'] = money
        return rtn_data


def get_sign(params_map, key):
    """ 生成签名 """
    sign_str = ''.join([str(params_map[k]) for k in ['para_id', 'app_id', 'order_no', 'total_fee']]) + key
    print sign_str
    return get_str_sign(sign_str)


def get_str_sign(sign_str):
    sign_str = hashlib.md5(sign_str).hexdigest()
    return sign_str.lower()


def compact_order_id(order_id):
    """压缩订单id"""
    return base64.urlsafe_b64encode(order_id)


def extract_order_id(order_id):
    """提取订单id"""
    return binascii.hexlify(base64.urlsafe_b64decode(order_id))


def post_bank_order(data):
    """提交订单"""
    post_data = {
        "body": data['body'],
        "total_fee": data['total_fee'],
        "para_id": data['para_id'],
        "app_id": data['app_id'],
        "order_no": data['order_no'],
        "notify_url": data['notify_url'],
        "attach": data['attach'],
        "child_para_id": 1,
        "pay_type": 1,
        "sign": data['sign']
    }
    resp = requests.post(API_URL_BANK, data=post_data)
    print resp.text
    return resp.json()['pay_url']


def post_qq_order(data):
    """提交订单"""
    post_data = {
        "body": data['body'],
        "total_fee": data['total_fee'],
        "para_id": data['para_id'],
        "app_id": data['app_id'],
        "order_no": data['order_no'],
        "service": '00',
        "notify_url": data['notify_url'],
        "attach": data['attach'],
        "type": 1,
        "child_para_id": 1,
        "sign": data['sign']
    }
    resp = requests.post(API_URL_QQ, data=post_data)
    print resp.text
    return resp.json()['pay_url']


def post_wechat_order(data):
    """提交订单"""
    post_data = {
        "body": data['body'],
        "total_fee": data['total_fee'],
        "para_id": data['para_id'],
        "app_id": data['app_id'],
        "order_no": data['order_no'],
        "notify_url": data['notify_url'],
        "attach": data['attach'],
        "child_para_id": 1,
        "device_id": 4,
        "sign": data['sign']
    }
    resp = requests.post(API_URL_WECHAT, data=post_data)
    print resp.text
    return resp.json()['pay_url']


def post_alipay_order(data):
    """提交订单"""
    resp = requests.post(API_URL_NEW, data=data)
    print resp.text
    return resp.text


bfbpay = BfbPay()
