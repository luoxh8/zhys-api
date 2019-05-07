# -*- coding: utf-8 -*-
"""
Doc:

Created on 2017/9/15
@author: MT
"""
from base import db
from sqlalchemy.sql import func


class UserInvite(db.Model):
    """好友邀请表"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, index=True, nullable=False)  # 用户id
    invitee_id = db.Column(db.Integer, index=True, nullable=False)  # 被邀请者id
    created = db.Column(db.DateTime, server_default=func.now())

    def __init__(self, user_id, invitee_id):
        self.user_id = user_id
        self.invitee_id = invitee_id


class SignIn(db.Model):
    """签到记录表"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, unique=True)
    last_sign_day = db.Column(db.Date)  # 上次签到日
    sign_days = db.Column(db.String(100), default='[]')  # 当月签到日列表
    multi_sign_bonus = db.Column(db.String(15), default='[]')  # 累计签到奖励领取列表
    created = db.Column(db.DateTime, server_default=func.now())

    def __init__(self, user_id, last_sign_day, sign_days):
        self.user_id = user_id
        self.last_sign_day = last_sign_day
        self.sign_days = sign_days


class BindPhoneActivity(db.Model):
    """绑定手机送288阅币活动"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, unique=True)
    created = db.Column(db.DateTime, server_default=func.now())

    def __init__(self, user_id):
        self.user_id = user_id


class BonusActivityUserBalance(db.Model):
    """红包现金活动，用户余额表"""
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'}

    user_id = db.Column(db.Integer, primary_key=True)  # 用户ID
    balance = db.Column(db.BigInteger, nullable=False)  # 余额
    total = db.Column(db.BigInteger, nullable=False, default=0)  # 累计收入

    def __init__(self, user_id, balance, total=0):
        self.user_id = user_id
        self.balance = balance
        self.total = total


class BonusActivityUserBalanceLog(db.Model):
    """红包现金活动，用户余额记录表"""
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'}

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False, index=True)  # 用户ID
    exec_type = db.Column(db.SmallInteger, nullable=False)  # 操作类型（1增加，2减少）
    money = db.Column(db.Integer, nullable=False)  # 金额（单位：分）
    remark = db.Column(db.String(45))  # 备注
    bind_id = db.Column(db.Integer)
    created = db.Column(db.DateTime, nullable=False, server_default=func.now())  # 记录时间

    def __init__(self, user_id, exec_type, money, remark, bind_id):
        self.user_id = user_id
        self.exec_type = exec_type
        self.money = money
        self.remark = remark
        self.bind_id = bind_id
