#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Doc: 
@author: 
@time: 
"""
import hashlib
import base64
import binascii
import requests
from flask import request
from main_app.recharge.channels.base import BasePay
import json
from lib.xmltojson import xmltojson

#MCH_ID = '101510144553'  # 商户编号
MCH_ID = '105510036138'  # 商户编号 口袋阅读王
#SECRET_KEY = 'ac8bdd9916e5c81c6e18606ac9d42c3c'
SECRET_KEY = '857d7e04bc4883d85653f12cbf68f720'
API_URL = 'https://pay.swiftpass.cn/pay/gateway'
WXAPP_ID = 'wx28c8a74bd01f5e3a'#阅读王
#WXAPP_ID = 'wxa2d464602063a5b8'
#WXAPP_ID = 'wx8e8fc77f7f2ef904'

class WftPay(BasePay):

    def post_order(self, user_id, order_id, money, notify_url, pay_type, **kwargs):
        order_id = compact_order_id(kwargs.get('_order_id').bytes)
        post_data = {
            'service': "pay.weixin.jspay",
            'mch_id': MCH_ID,
            'is_minipg': 1,
            'out_trade_no': order_id,
            'body': u'阅币充值',
            'sub_openid': kwargs.get('open_id', ''),
            'sub_appid': WXAPP_ID,
            'total_fee': money,
            'mch_create_ip': kwargs.get('ip', ''),
            'notify_url': notify_url,
            'nonce_str': user_id,
        }
        post_data['sign'] = get_sign(post_data, SECRET_KEY)
        rtn_data = {}
        print post_data
        print '==========================wft================================='
        headers = {'content-type': 'application/xml'}
        s = requests.post(API_URL, data=trans_dict_to_xml(post_data), headers=headers)
        xtj=xmltojson()

        print xtj.main(s.text)
        rtn_data['rtn_json'] = xtj.main(s.text)
        return rtn_data

    def verify(self, data):
        args = data
        sign = args.get('sign')
        order_id = args.get('out_trade_no')
        money = args.get('total_fee')
        _sign = get_notify_sign(args, SECRET_KEY)
        if sign != _sign:
            print('====================')
            print _sign
            print sign
            return {"code": 1, "msg": 'code error'}
        if int(args.get('result_code')) != 0:
            return {"code": 1, "msg": 'code error'}

        order_id = extract_order_id(order_id)
        return {"code": 0, "order_id": order_id, "money": money}


def get_sign(params_map, key):
    """ 生成签名 """
    sort_list = []
    for key in params_map:
        if params_map.get(key):
            sort_list.append('%s=%s'%(key, params_map.get(key)))

    a = sorted(sort_list)
    sign_str = '&'.join(a)+ '&key=%s'%SECRET_KEY
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
            sort_list.append('%s=%s'%(key, params_map.get(key)))

    a = sorted(sort_list)
    sign_str = '&'.join(a)+ '&key=%s'%SECRET_KEY
    print sign_str
    return get_str_sign(sign_str)

def get_str_sign(sign_str):
    sign_str = hashlib.md5(sign_str).hexdigest()
    return sign_str.upper()


def compact_order_id(order_id):
    """压缩订单id"""
    return base64.urlsafe_b64encode(order_id)


def extract_order_id(order_id):
    """提取订单id"""
    return binascii.hexlify(base64.urlsafe_b64decode(order_id))

def trans_dict_to_xml(data):
    xml = []
    for k in sorted(data.keys()):
        v = data.get(k)
        if k == 'detail' and not v.startswith('<![CDATA['):
            v = '<![CDATA[{}]]>'.format(v)
        xml.append('<{key}>{value}</{key}>'.format(key=k, value=v))
    return '<xml>{}</xml>'.format(''.join(xml))

def trans_xml_to_dict(xml):
    soup = BeautifulSoup(xml, features='xml')
    xml = soup.find('xml')
    if not xml:
        return {}
    data = dict([(item.name, item.text) for item in xml.find_all()])
    return data


wftpay = WftPay()
