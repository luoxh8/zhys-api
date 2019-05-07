# -*- coding: utf-8 -*-
"""
Doc:

Created on 2017/9/1
@author: MT
"""
from uuid import uuid1

import requests
from flask import request, current_app
from flask_login import current_user

from main_app.recharge.channels.base import BasePay
import ujson as json
from models import db
from models.recharge import IapOrder, RechargeOrder, RechargeTag, OrderBook
from lib.ios_special import is_ios_special


class IapPay(BasePay):
    SERVICE_CFG = ['iappay']

    def verify(self):
        rtn_data = {'code': 1, 'msg': '', 'order_id': '', 'money': 0, 'rtn_success': '', 'rtn_fail': ''}
        receipt = request.form.get('receipt', '')
        if not receipt:
            rtn_data['rtn_fail'] = json.dumps({"code": 1, "msg": u'订单不存在'})
            return rtn_data

        print current_user.id, receipt

        # 向app store验证
        verify_url = 'https://buy.itunes.apple.com/verifyReceipt'  # 正式环境
        if is_ios_special():
            verify_url = 'https://sandbox.itunes.apple.com/verifyReceipt'  # 测试环境
        resp = requests.post(verify_url, data=json.dumps({"receipt-data": receipt}))
        print resp.text
        resp_json = resp.json()
        if resp_json.get('status') != 0:  # or resp_json.get('environment') == 'Sandbox':
            rtn_data['rtn_fail'] = json.dumps({"code": 1, "msg": u'支付失败'})
            return rtn_data

        # 验证是否自家产品内购
        m_id = request.args.get('m_id', -1, int)
        bundle_ids = current_app.config['IOS_BUNDLE_ID'].get(m_id)
        bundle_id = resp_json['receipt']['bundle_id']
        if not bundle_ids or bundle_id not in bundle_ids:
            print "刷单 bid", bundle_id
            rtn_data['rtn_fail'] = json.dumps({"code": 1, "msg": u'支付失败'})
            return rtn_data

        pay = sorted(resp_json['receipt']['in_app'], key=lambda x:x['purchase_date_ms'])[-1]
        product_id = pay['product_id'].replace(bundle_id, '') if pay['product_id'].startswith(bundle_id) else ''
        per_money = current_app.config['IAP_PRODUCT_CFG'].get(product_id)
        if not per_money:
            print "刷单 pid", product_id
            rtn_data['rtn_fail'] = json.dumps({"code": 1, "msg": u'支付失败'})
            return rtn_data

        # 验证是否已充值过
        iap_id = pay['transaction_id']
        if not iap_id or IapOrder.query.filter_by(iap_id=iap_id).first():
            print "刷单 tid", iap_id
            rtn_data['rtn_fail'] = json.dumps({"code": 1, "msg": u'支付失败'})
            return rtn_data

        # 生成订单
        order_id = uuid1().hex
        _pay_type = 'iappay'
        money = per_money
        book_id = request.form.get('book_id', 0, int)
        ip = request.headers.get("X-Real-Ip", "")
        volume_chapter = request.form.get('volume_chapter', '')  # 书籍卷id列表和章节id列表 卷id,章节id|...
        tag = request.form.get('activity_tag', '')
        db.session.add(IapOrder(iap_id, order_id))
        order = RechargeOrder(order_id, current_user.id, _pay_type, money, book_id, ip, 2)
        db.session.add(order)
        if tag:
            bind_id = request.form.get('activity_id', 0, int)
            db.session.add(RechargeTag(order_id, tag, bind_id))
        if book_id and volume_chapter:
            db.session.add(OrderBook(order_id, book_id, volume_chapter))
        try:
            db.session.commit()
        except Exception:
            import traceback
            traceback.print_exc()
            db.session.rollback()
            rtn_data['rtn_fail'] = json.dumps({"code": 1, "msg": u'支付失败'})
            return rtn_data

        rtn_data['code'] = 0
        rtn_data['order_id'] = order_id
        rtn_data['money'] = money
        rtn_data['rtn_success'] = json.dumps({"code": 0, "order_id": order_id, "money": money})
        return rtn_data


iappay = IapPay()
