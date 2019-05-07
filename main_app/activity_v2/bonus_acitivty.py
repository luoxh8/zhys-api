#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
@Time    : 2017/10/31 下午3:44
@Author  : linjf
@File    : bonus_acitivty

Desc: 红包现金活动

实现思路：
    1、分享落地页链接带邀请者用户ID，如：123.com?uid=1；
    2、落地页方面下载app时将uid附带传入rp域名下载链接；
    3、渠道方面进行内部域名访问，api子系统对ip，邀请者ID进行匹配记录，缓存4小时；
    4、当有新设备激活时，进行IP匹配，双方进行奖励。

'''
from flask import Blueprint, request
from flask_login import login_required, current_user

from models import db, Book, BonusActivityUserBalance, BonusActivityUserBalanceLog, User, UserBalance, UserBalanceLog
from lib import redis_utils

import ujson as json
import datetime


bp = Blueprint('bonus_activity', __name__)

REDIS_KEY = 'bonus_activity-%s'
ACTIVITY_PRICE = 100


@bp.route('/share_book_list', methods=['GET'])
def share_book_list():
    """书籍分享列表"""
    book_ids = []
    datas = []
    books = Book.query.filter(Book.book_id.in_(book_ids), Book.showed==True).all()
    for item in books:
        datas.append({
            'book_id': item.book_id,
            'cover': item.cover,
            'book_name': item.book_name,
            'intro': item.intro,
        })
    return json.dumps({'code': 0, 'data': datas})


@bp.route('/get_user_income', methods=['GET'])
@login_required
def get_user_income():
    """获取用户收益汇总（累计、今日、本周）"""
    data = {'total': 0, 'today': 0, 'week': 0}

    user_id = current_user.id

    today = datetime.date.today()
    tomorrow = today + datetime.timedelta(days=1)
    monday = today + datetime.timedelta(-today.weekday())
    next_monday = today + datetime.timedelta(7-today.weekday())

    # 查询用户累计收入
    user_balance = BonusActivityUserBalance.query.filter_by(user_id=user_id).first()
    if user_balance:
        data['total'] = user_balance.total

    # 查询用户当天收入
    sql = 'select ifnull(sum(money), 0) from bonus_activity_user_balance_log where user_id=:user_id' \
          ' and exec_type=1 and created between :start_date and :end_date'
    datetime_format = '%Y-%m-%d'

    query_today_data = {
        'user_id': user_id,
        'start_date': today.strftime(datetime_format),
        'end_date': tomorrow.strftime(datetime_format)
    }
    data['today'] = int(db.session.execute(sql, query_today_data).scalar())

    query_week_data = {
        'user_id': user_id,
        'start_date': monday.strftime(datetime_format),
        'end_date': next_monday.strftime(datetime_format),
    }
    data['week'] = int(db.session.execute(sql, query_week_data).scalar())

    return json.dumps({'code': 0, 'data': data})


@bp.route('/download_notify', methods=['GET'])
def download_notify():
    """下载通知，供渠道子系统使用"""
    ip = request.args.get('ip', '', unicode)
    inviter_id = request.args.get('uid', -1, int)

    if not ip or not inviter_id:
        return json.dumps({'code': -1, 'msg': u'data error.'})

    # 设置缓存，匹配邀请者id及下载者IP
    redis_utils.set_cache(REDIS_KEY % ip, inviter_id, 86400)
    return json.dumps({'code': 0, 'msg': 'success'})


@bp.route('/activate_notify', methods=['GET'])
def activate_notify():
    """激活通知，供渠道子系统使用"""
    ip = request.args.get('ip', '', unicode)
    idfa = request.args.get('idfa', '', unicode)
    if not ip or not idfa:
        return json.dumps({'code': -1, 'msg': 'data error.'})

    # 查询邀请者是否参与活动
    inviter_id = redis_utils.get_cache(REDIS_KEY % ip, refresh_expires=False)
    if not inviter_id:
        return json.dumps({'code': -1, 'msg': 'ip not match'})

    # 查询被邀请者账户
    invited = User.query.filter_by(device_id=idfa).first()
    if not invited:
        return json.dumps({'code': -1, 'msg': 'invited id not found'})

    invited_id = invited.id

    # 邀请者发放奖励
    inviter_user_balance = BonusActivityUserBalance.query.filter_by(user_id=inviter_id).with_lockmode('update').first()
    if not inviter_user_balance:
        inviter_user_balance = BonusActivityUserBalance(inviter_id, ACTIVITY_PRICE, ACTIVITY_PRICE)
        db.session.add(inviter_user_balance)
    else:
        inviter_user_balance.balance += ACTIVITY_PRICE
        inviter_user_balance.total += ACTIVITY_PRICE

    db.session.add(BonusActivityUserBalanceLog(inviter_id, 1, ACTIVITY_PRICE, 'invite', -1))

    # 被邀请者发放奖励
    invited_user_balance = BonusActivityUserBalance.query.filter_by(user_id=invited_id).with_lockmode('update').first()
    if not invited_user_balance:
        invited_user_balance = BonusActivityUserBalance(invited_id, ACTIVITY_PRICE, ACTIVITY_PRICE)
        db.session.add(invited_user_balance)
    else:
        invited_user_balance.balance += ACTIVITY_PRICE
        invited_user_balance.total += ACTIVITY_PRICE

    db.session.add(BonusActivityUserBalanceLog(invited_id, 1, ACTIVITY_PRICE, 'invited', -1))

    db.session.commit()
    return json.dumps({'code': 0, 'msg': 'success'})


@bp.route('/invite_log')
@login_required
def invite_log():
    """邀请记录列表"""
    user_id = current_user.id

    datas = []
    logs = BonusActivityUserBalanceLog.query.filter_by(user_id=user_id, remark='invite')\
        .order_by(BonusActivityUserBalanceLog.id.desc()).all()
    for item in logs:
        datas.append({
            'id': item.id,
            'money': item.money,
            'description': u'邀请好友下载',
            'created': item.created.strftime('%Y-%m-%d %H:%M:%S'),
        })
    return json.dumps({'code': 0, 'data': datas})


@bp.route('/operation_log')
@login_required
def operation_log():
    """用户操作提现记录"""
    user_id = current_user.id

    datas = []
    logs = BonusActivityUserBalanceLog.query.filter_by(user_id=user_id, exec_type=2)\
        .order_by(BonusActivityUserBalanceLog.id.desc()).all()

    for item in logs:
        desc = ''
        if item.remark == 'exchange_balance':
            desc = u'转阅币'
        elif item.remark == 'exchange_alipay':
            desc = u'支付宝提现'

        datas.append({
            'id': item.id,
            'money': item.money,
            'description': desc,
            'created': item.created.strftime('%Y-%m-%d %H:%M:%S'),
        })

    return json.dumps({'code': 0, 'data': datas})


@bp.route('/operation_index')
@login_required
def operation_index():
    """用户操作记录总计"""
    user_id = current_user.id

    data = {'total': 0, 'exchange_money': 0, 'exchange_balance': 0, 'balance': 0}

    # 查询用户累计收入
    user_balance = BonusActivityUserBalance.query.filter_by(user_id=user_id).first()
    if user_balance:
        data['total'] = user_balance.total
        data['balance'] = user_balance.balance

    sql_exchange = 'select ifnull(sum(money), 0) from bonus_activity_user_balance_log where remark="%s" and user_id=%d'

    # 查询用户累计提现金额
    data['exchange_money'] = db.session.execute(sql_exchange % ('exchange_alipay', user_id)).scalar()

    # 查询用户累计提现阅币总额
    data['exchange_balance'] = db.session.execute(sql_exchange % ('exchange_balance', user_id)).scalar()

    return json.dumps({'code': 0, 'data': data})


@bp.route('/exchange_balance', methods=['POST'])
@login_required
def exchange_balance():
    """提现到账户阅币余额"""
    user_id = current_user.id

    activity_user_balance = BonusActivityUserBalance.query.filter_by(user_id=user_id).with_lockmode('update').first()
    if not activity_user_balance or activity_user_balance.balance <= 0:
        return json.dumps({'code': -1, 'msg': u'账户余额不足'})

    money = activity_user_balance.balance

    # 活动账户余额清空
    activity_user_balance.balance = 0
    db.session.add(BonusActivityUserBalanceLog(user_id, 2, money, 'exchange_balance', -1))

    # 用户阅币余额转入
    user_balance = UserBalance.query.filter_by(user_id=user_id).with_lockmode('update').first()
    if not user_balance:
        db.session.add(UserBalance(user_id, money))
    else:
        user_balance.balance += money

    db.session.add(UserBalanceLog(user_id, 1, money, 'bonus_activity', -1, 'bonus_activity', ''))
    db.session.commit()

    return json.dumps({'code': 0, 'msg': 'success'})


@bp.route('/exchange_alipay', methods=['POST'])
@login_required
def exchange_alipay():
    """提现到支付宝账户"""
    user_id = current_user.id
    account = request.form.get('account', '', unicode)
    real_name = request.form.get('real_name', '', unicode)
    money = request.form.get('money', -1, int)  # 提现金额，单位为分

    if not account or not real_name: # or money < 3000:
        return json.dumps({'code': -1, 'msg': 'params error'})

    # 扣除活动账户余额
    activity_user_balance = BonusActivityUserBalance.query.filter_by(user_id=user_id).with_lockmode('update').first()
    if not activity_user_balance or activity_user_balance.balance < money:
        return json.dumps({'code': -1, 'msg': u'账户余额不足'})

    activity_user_balance.balance -= money
    log = BonusActivityUserBalanceLog(user_id, 2, money, 'exchange_alipay', -1)
    db.session.add(log)
    db.session.commit()

    from services.alipay_transfer import execute_alipay_transfer
    res = execute_alipay_transfer(account, real_name, money / 100, log.id)

    res_decode = json.loads(res)
    if res_decode['code'] != 0:
        return json.dumps({'code': -1, 'msg': u'请确保支付宝账号与真实姓名信息正确'})

    return json.dumps({'code': 0, 'msg': 'success'})
