# -*- coding: utf-8 -*-
"""
Doc:

Created on 2017/8/30
@author: MT
"""
import datetime
import ujson as json
from flask import Blueprint, abort, request
from flask_login import login_required, current_user

from lib.buy import buy_book, next_auto_buy
from models.activity import SignIn
from models.recharge import RechargeOrder
from models import db
import channels
from models.user import UserBalanceLog, UserBalance
from lib import utils
from lib.xmltojson import xmltojson

bp = Blueprint('notify', __name__)


@bp.route('/<channel_name>', methods=['GET', 'POST'])
def _notify(channel_name):
    """支付回调"""
    xtj=xmltojson()
    data = xtj.main(request.data)
    print 11111111111111
    channel = getattr(channels, channel_name)
    if not channel:
        abort(404)

    rst = channel.verify(data)
    print rst
    if int(rst['code']) != 0:
        return 'fail'
    order_id = rst['order_id']
    money = rst['money']
    order = RechargeOrder.query.filter_by(order_id=order_id).with_lockmode('update').first()
    print 2222
    if not order:
        return 'fail'
    print 3333
    if order.money != int(money):
        return 'fail'
    print 4444
    if order.status == 1:
        return 'fail'
    print 5555
    update_recharge_order(order)

    # 渠道统计
    utils.channel_collect(dict(a='pay', order_id=order_id, user_id=order.user_id, money=money, status=1))
    return 'success'


@bp.route('/iappay', methods=['POST'])
@login_required
def _notify_iap():
    """ios内购支付回调"""
    next_auto_buy()  # 是否自动购买下一章设置
    return _notify('iappay')


def update_recharge_order(order):
    order_full_money = order.money

    # 更改支付订单状态
    order.status = 1

    # 活动相关
    recharge_tag = db.session.execute('select * from recharge_tag where order_id="%s" limit 1' %
                                      order.order_id).fetchone()
    if recharge_tag and recharge_tag.tag == 're_sign_in':  # 补签
        re_sign_in(order.user_id, recharge_tag.bind_id)

    if order.device_type == 2:
        platform = 'ios' 
    elif order.device_type == 1:
        platform = 'android'
    elif order.device_type == 3:
        platform = 'applet'

    # 充值赠送阅币活动
    extra_money_cfg = {
        3000: 1000,  # 充30送1000阅币
        5000: 2000,
        9800: 5000,
        19800: 10000,
    }
    extra_money = extra_money_cfg.get(order_full_money, 0)
    if extra_money:
        order_full_money += extra_money
        log1 = UserBalanceLog(order.user_id, 1, extra_money, "recharge_extra", order.order_id, "recharge_extra", platform)
        db.session.add(log1)

    # 记录用户流水
    log = UserBalanceLog(order.user_id, 1, order.money, "recharge", order.order_id, "recharge", platform)
    db.session.add(log)
    db.session.query(UserBalance).filter_by(user_id=order.user_id).update({
        UserBalance.balance: UserBalance.balance + order_full_money,
        UserBalance.total: UserBalance.total + order.money,
    })

    try:
        db.session.commit()
    except Exception:
        import traceback
        traceback.print_exc()
        db.session.rollback()

    # 直接购买
    if order.book_id:
        volume_chapter = db.session.execute('select volume_chapter from order_book where order_id=%s limit 1' %
                                            order.order_id).scalar() or ''
        if volume_chapter:
            buy_book(order.book_id, volume_chapter, platform)


def re_sign_in(user_id, day):
    """补签"""
    today = datetime.date.today()
    if day <= 0 or day >= today.day or day < today.day - 2:
        return

    user_sign = SignIn.query.filter_by(user_id=user_id).with_lockmode('update').first()
    that_day = datetime.date(today.year, today.month, day)
    if not user_sign:
        user_sign = SignIn(current_user.id, that_day, json.dumps([day]))
        db.session.add(user_sign)
    else:
        last_sign_day = max(user_sign.last_sign_day, that_day)
        if user_sign.last_sign_day.year < today.year or user_sign.last_sign_day.month < today.month:
            user_sign.sign_days = '[]'
            user_sign.multi_sign_bonus = '[]'
            last_sign_day = that_day

        sign_days = json.loads(user_sign.sign_days)
        if day in sign_days:
            return

        sign_days.append(day)
        user_sign.last_sign_day = last_sign_day
        user_sign.sign_days = json.dumps(sign_days)
