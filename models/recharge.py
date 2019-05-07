# -*- coding: utf-8 -*-
"""
Doc:

Created on 2017/8/30
@author: MT
"""
import datetime
from base import db
from sqlalchemy.sql import func


class RechargeOrder(db.Model):
    """充值订单表"""
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'}

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.String(64), nullable=False, index=True)  # 充值订单ID
    user_id = db.Column(db.Integer, nullable=False, index=True)  # 用户ID
    pay_type = db.Column(db.String(20), nullable=False)  # 支付类型（微信，京东，支付宝，银联...）
    money = db.Column(db.BigInteger, nullable=False)  # 充值金额（单位：分）
    status = db.Column(db.SmallInteger, nullable=False, index=True)  # 订单状态（3：未处理，2：充值失败，1：成功）
    book_id = db.Column(db.Integer, default=0)  # 如果是直接购买记录书籍ID，当充值回调时自动去购买
    ip = db.Column(db.String(20), default='')  # 用户发起充值时ip
    device_type = db.Column(db.SmallInteger, index=True)  # 设备类型(1:android, 2:ios)
    created = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now, index=True)  # 订单创建时间

    def __init__(self, order_id, user_id, pay_type, money, book_id, ip, device_type):
        self.order_id = order_id
        self.user_id = user_id
        self.pay_type = pay_type
        self.money = money
        self.book_id = book_id
        self.ip = ip
        self.device_type = device_type
        # default params:
        self.status = 3


class OrderBook(db.Model):
    """订单购买书籍表"""
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'}

    order_id = db.Column(db.String(64), primary_key=True)  # 充值订单ID
    book_id = db.Column(db.Integer, default=0)  # 如果是直接购买记录书籍ID，当充值回调时自动去购买
    volume_chapter = db.Column(db.String(1024), default='')  # 书籍卷id列表和章节id列表 卷id,章节id|...

    def __init__(self, order_id, book_id, volume_chapter):
        self.order_id = order_id
        self.book_id = book_id
        self.volume_chapter = volume_chapter


class RechargeTag(db.Model):
    """充值订单所属活动标签"""
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.String(64), nullable=True, index=True)  # 订单id
    tag = db.Column(db.String(32))  # 订单标签
    bind_id = db.Column(db.Integer)  # 关联id

    def __init__(self, order_id, tag, bind_id):
        self.order_id = order_id
        self.tag = tag
        self.bind_id = bind_id


class IapOrder(db.Model):
    """ios内购订单"""
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'}

    iap_id = db.Column(db.String(64), primary_key=True)  # iap订单id
    order_id = db.Column(db.String(64))  # 充值订单ID

    def __init__(self, iap_id, order_id):
        self.iap_id = iap_id
        self.order_id = order_id


class TransferOrder(db.Model):
    """支付宝转账订单"""
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'}

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.String(64), nullable=False, index=True)  # 转账订单ID
    money = db.Column(db.BigInteger, nullable=False)  # 充值金额（单位：分）
    account = db.Column(db.String(50))  # 支付宝账号
    real_name = db.Column(db.String(50))  # 支付宝真实姓名
    status = db.Column(db.SmallInteger, nullable=False, index=True)  # 订单状态（3：未处理，2：充值失败，1：成功）
    remark = db.Column(db.String(100), index=True)  # 备注信息
    bind_id = db.Column(db.Integer)  # 绑定ID
    created = db.Column(db.DateTime, server_default=func.now())  # 创建时间

    def __init__(self, order_id, money, account, real_name, bind_id, remark=''):
        self.order_id = order_id
        self.money = money
        self.account = account
        self.real_name = real_name
        self.bind_id = bind_id
        self.status = 3
        self.remark = remark
