# coding: utf-8
import datetime

from sqlalchemy.sql.schema import PrimaryKeyConstraint

from base import db
from book import Book, BookChapters
from flask_login import UserMixin
from sqlalchemy.sql import func
import json
import requests
from flask import current_app


class User(UserMixin, db.Model):
    """ 用户表 """
    id = db.Column(db.Integer(), primary_key=True)
    phone = db.Column(db.String(20), unique=True)
    password = db.Column(db.String(128))
    nickname = db.Column(db.String(50)) 
    email = db.Column(db.String(20))
    notify_phone = db.Column(db.String(20))  # 接收通知的手机号码, 可以和phone 不一致
    level = db.Column(db.Integer(), default=0)
    avatar = db.Column(db.String(200))
    sex = db.Column(db.Integer(), server_default='0')#1男2女

    platform = db.Column(db.String(20))
    device_id = db.Column(db.String(40), index=True, unique=True)  # 设备id 安卓:mac ios:idfa
    register_ip = db.Column(db.String(20))
    intro = db.Column(db.String(300))  # 个人简介
    aphorism = db.Column(db.String(200))  # 个人签名

    oauth_from = db.Column(db.String(20), server_default='')  # 认证来源 tel_pwd, weibo, wechat, qq
    oauth_openid = db.Column(db.String(128), unique=True)  # openid， 对于微信， 是unionid（用openid 会导致公众号和手机客户端不一致）
    oauth_userinfo = db.Column(db.Text)  # 来自第三方平台的用户额外信息
    oauth_time = db.Column(db.DateTime())  # 绑定第三方帐号时间
    oauth_nickname = db.Column(db.String(50)) 
    oauth_avatar = db.Column(db.String(200))

    modified = db.Column(db.DateTime(), server_default=func.now())
    created = db.Column(db.DateTime(), server_default=func.now())

    def get_channel_name(self):
        url = current_app.config['CHANNEL_URL'] + '/channel/get_user_info?user_id=%s' %(self.id)
        try:
            return requests.get(url).json()['data']['channel_name']
        except Exception as e:
            return 'unknow'

    def to_admin_dict(self):
        ub = UserBalance.query.filter_by(user_id=self.id).first()
        balance = ub.balance if ub else 0
        nickname = self.nickname if self.nickname else ''
        if self.oauth_from == 'tel_pwd':
            if self.phone:
                nickname = '%s****%s' %(self.phone[:3], self.phone[-4:])
        sex = u'男' if self.sex == 1 else u'女'
        return dict(
            id = self.id,
            phone = self.phone if self.phone else '',
            nickname = nickname,
            email = self.email if self.email else '',
            notify_phone = self.notify_phone if self.notify_phone else '',
            level  = self.level if self.level else '',
            avatar = self.avatar if self.avatar else 'http://ov2eyt2uw.bkt.clouddn.com/android_pre.jpg',
            platform = self.platform if self.platform else '',
            register_ip = self.register_ip,
            intro = self.intro if self.intro else '',
            aphorism = self.aphorism if self.aphorism else '',
            oauth_from = self.oauth_from if self.oauth_from else '',
            oauth_userinfo = self.oauth_userinfo,
            balance = balance,
            sex = sex,
            channel_name = self.get_channel_name(),
            created = self.created.strftime('%Y-%m-%d %H:%M:%S')
            )
    
    def to_dict(self):
        return dict(
            id = self.id,
            phone = self.phone if self.phone else '',
            nickname = self.nickname if self.nickname else self.id,
            avatar = self.avatar or 'http://ov2eyt2uw.bkt.clouddn.com/default_avatar.png',
            intro = self.intro if self.intro else '',
            aphorism = self.aphorism if self.aphorism else '',
            notify_phone = self.notify_phone if self.notify_phone else '',
            oauth_openid = self.oauth_openid if self.oauth_openid else '',
            oauth_userinfo = self.oauth_userinfo if self.oauth_userinfo else '',
            oauth_from = ('wechat' if self.oauth_from == 'applet' else self.oauth_from ) if self.oauth_from else '',
            oauth_time = self.oauth_time.__str__() if self.oauth_time else '',
            oauth_nickname = self.oauth_nickname or '',
            oauth_avatar = self.oauth_avatar or self.avatar or 'http://ov2eyt2uw.bkt.clouddn.com/default_avatar.png',
            sex = self.sex
        )


class UserBalance(db.Model):
    """ 用户余额 """
    user_id = db.Column(db.Integer, primary_key=True)  # 用户ID
    balance = db.Column(db.BigInteger, nullable=False)  # 余额
    total = db.Column(db.BigInteger, nullable=False, default=0)  # 累计充值

    def __init__(self, user_id, balance, total=0):
        self.user_id = user_id
        self.balance = balance
        self.total = total


class UserBalanceLog(db.Model):
    """ 用户余额记录 """
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False, index=True)  # 用户ID
    exec_type = db.Column(db.SmallInteger, nullable=False)  # 操作类型（1增加，2减少）
    money = db.Column(db.BigInteger, nullable=False)  # 金额（单位：分）
    corresponding = db.Column(db.String(20), nullable=False)
    corresponding_id = db.Column(db.String(500), nullable=False)  # 对应ID
    book_id = db.Column(db.String(45), nullable=False, index=True, server_default='0')  # 购买书籍ID
    remark = db.Column(db.String(45))  # 备注
    created_time = db.Column(db.DateTime, nullable=False, server_default=func.now())  # 记录时间
    platform = db.Column(db.String(20))
    
    def __init__(self, user_id, exec_type, money, corresponding, corresponding_id, remark, platform='', book_id=0):
        self.user_id = user_id
        self.exec_type = exec_type
        self.money = money
        self.corresponding = corresponding
        self.corresponding_id = corresponding_id
        self.remark = remark
        self.platform = platform
        self.book_id = book_id
    
    def to_admin_dict(self):
        book = Book.query.filter_by(book_id=self.book_id).first()
        user = User.query.filter_by(id=self.user_id).first()

        tmp = self.corresponding_id
        if tmp.find('-') >= 0:
            tmp = tmp[tmp.index('-')+1: ]
            tmp = tmp.split('|')
            if len(tmp) == 1 and book:
                corresponding_id = u'%s | %s' %(book.book_name, self.get_chapter_name(int(tmp[0])))
            elif len(tmp) >= 2 and book:
                corresponding_id = u'%s | %s——%s' %(book.book_name, self.get_chapter_name(int(tmp[0])), self.get_chapter_name(int(tmp[1])))
            else:
                corresponding_id = self.corresponding_id

            return dict(user = user.to_admin_dict() if user else {},
                        user_id = self.user_id,
                        money = self.money,
                        corresponding_id = corresponding_id,
                        created_time = self.created_time.strftime('%Y-%m-%d %H:%M:%S'),
                        book_id = self.book_id,
                        platform = self.platform)
        else:
            return dict(user = user.to_admin_dict() if user else {},
                        user_id = self.user_id,
                        money = self.money,
                        corresponding_id = self.corresponding_id,
                        created_time = self.created_time.strftime('%Y-%m-%d %H:%M:%S'),
                        book_id = self.book_id,
                        platform = self.platform)


    def get_chapter_name(self, chapter_id):
        chapter = BookChapters.query.filter_by(book_id=self.book_id, id=chapter_id).first()
        if chapter:
            return chapter.chapter_name
        else:
            return ''


class SmsCaptcha(db.Model):
    """ 验证码记录 """
    id = db.Column(db.Integer, primary_key=True)
    phone = db.Column(db.String(20))
    captcha = db.Column(db.String(10))
    action = db.Column(db.Integer) # 0 - unknown, 1 - register 2 - reset pwd
    created = db.Column(db.DateTime, server_default=func.now())


class UserDetail(db.Model):
    """ 小程序用户其他信息 """
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False, index=True)  # 用户ID
    language = db.Column(db.String(20))  # 语言
    city = db.Column(db.String(120))  #
    province = db.Column(db.String(120))  #
    country = db.Column(db.String(120))  #
    open_id = db.Column(db.String(150))  #openid
    union_id = db.Column(db.String(150))  #

    def __init__(self, user_id, language, city, province, country, open_id, union_id):
        self.user_id = user_id
        self.language = language
        self.city = city
        self.province = province
        self.country = country
        self.open_id = open_id
        self.union_id = union_id
