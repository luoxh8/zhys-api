#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Doc: 支付宝原生
@author: 
@time: 
"""
import os

from alipay.aop.api.AlipayClientConfig import AlipayClientConfig
from alipay.aop.api.DefaultAlipayClient import DefaultAlipayClient
from flask import request

from main_app.recharge.channels.base import BasePay

ALIPAY_APPID = '2017100909208083'
CUR_DIR = os.path.dirname(os.path.realpath(__file__))
PRIVATE_KEY_PATH = os.path.join(CUR_DIR, 'app_private_key.pem')
PUBLIC_KEY_PATH = os.path.join(CUR_DIR, 'alipay_public_key.pem')


class OfficialAliPay(BasePay):
    SERVICE_CFG = ['alipay']

    def __init__(self):
        alipay_client_config = AlipayClientConfig()
        alipay_client_config.app_id = ALIPAY_APPID
        alipay_client_config.app_private_key = PRIVATE_KEY_PATH
        alipay_client_config.alipay_public_key = PUBLIC_KEY_PATH
        alipay_client_config.sign_type = "RSA"

        self.alipay = DefaultAlipayClient(alipay_client_config=alipay_client_config)

    def post_order(self, user_id, order_id, money, notify_url, pay_type, **kwargs):
        order_string = self.alipay.api_alipay_trade_app_pay(
            out_trade_no=order_id,
            total_amount=(money / 100),
            subject='阅币充值',
            body='阅币充值',
            notify_url=notify_url,  # 可选, 不填则使用默认notify url
        )
        rtn_data = {'rtn_json': order_string}
        return rtn_data

    def verify(self):
        rtn_data = {'code': 1, 'msg': '', 'order_id': '', 'money': 0, 'rtn_success': 'success', 'rtn_fail': 'fail'}
        data = request.form.to_dict()
        signature = data.pop("sign")

        print(data)
        print(signature)

        # verify
        success = self.alipay.verify(data, signature)
        if success and data["trade_status"] in ("TRADE_SUCCESS", "TRADE_FINISHED"):
            print("trade succeed")
            out_trade_no = request.form.get('out_trade_no')
            receipt_amount = request.form.get('receipt_amount')
            total_amount = request.form.get('total_amount')
            if out_trade_no and receipt_amount and total_amount and receipt_amount == total_amount:
                rtn_data['code'] = 0
                rtn_data['order_id'] = out_trade_no
                rtn_data['money'] = receipt_amount * 100
        return rtn_data


official_alipay = OfficialAliPay()
