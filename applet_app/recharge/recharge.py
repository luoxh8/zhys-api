# -*- coding: utf-8 -*-
"""
Doc:

Created on 2017/8/30
@author: MT
"""
from uuid import uuid1

import ujson as json
from flask import Blueprint, abort, request, url_for, session, current_app
from flask_login import login_required, current_user

from lib.buy import next_auto_buy
from lib import utils, redis_utils
from models.recharge import RechargeOrder, RechargeTag, OrderBook
from models import db
import channels

bp = Blueprint('recharge', __name__)


@bp.route('/pre_order/<channel_name>/<pay_type>', methods=['POST'])
#@login_required
def pre_order(channel_name, pay_type):
    """
    预下单
    :param channel: 支付渠道
    :param pay_type: 支付类型
    """
    login_key = request.args.get('login_key', '')
    user_login = redis_utils.get_cache(login_key, refresh_expires=False)
    if not user_login:
        return json.dumps({'code': -99, 'msg': u'请登录'})

    channel = getattr(channels, channel_name)
    print channel
    #if not channel or pay_type not in channel.SERVICE_CFG:
    #    abort(404)

    next_auto_buy()  # 是否自动购买下一章设置
    user_id = json.loads(user_login)['user_id']
    #user_id = 70
    money = request.form.get("money", 0, int)  # 单位：分
    if money not in [x*100 for x in current_app.config['RECHARGE_OPTIONS']['applet']]:
        return json.dumps({'code': -999, 'msg': u'充值金额有误'})
    #money = 10
    book_id = request.form.get("book_id", 0, int)  # 书籍id
    volume_chapter = request.form.get('volume_chapter', '')  # 书籍卷id列表和章节id列表 卷id,章节id|...
    if money <= 0:
        return json.dumps({"code": 1, "msg": "params error"})

    ip = request.headers.get("X-Real-Ip", "")
    device_type = request.args.get("platform", "")
    if device_type.startswith("ios"):
        device_type = 2
    elif device_type.startswith("android"):
        device_type = 1
    elif device_type.startswith("applet"):
        device_type = 3

    _order_id = uuid1()
    order_id = _order_id.hex

    tag = request.form.get('activity_tag', '')
    if tag:
        bind_id = request.form.get('activity_id', 0, int)
        db.session.add(RechargeTag(order_id, tag, bind_id))

    _pay_type = '%s_%s' % (channel_name, pay_type)
    order = RechargeOrder(order_id, user_id, _pay_type, money, book_id, ip, device_type)
    db.session.add(order)
    if book_id and volume_chapter:
        db.session.add(OrderBook(order_id, book_id, volume_chapter))
    db.session.commit()

    rtn_data = {
        "amount": money,
        "query_key": "%d-%d" % (user_id, order.id),
        "recharge_order_id": order_id,
    }
    print ip
    notify_url = current_app.config['BASE_URL'] + "/notify/%s" % channel_name
    rtn_data.update(channel.post_order(user_id, order_id, money, notify_url, pay_type, device_type=device_type,
                                       _order_id=_order_id, ip=ip, open_id=json.loads(user_login)['openid']))

    # 渠道统计
    utils.channel_collect(dict(a='pay', order_id=order_id, user_id=user_id, money=money, status=0))
    return json.dumps({'code': 0, 'data': rtn_data})


@bp.route("/order/status", methods=["GET"])
@login_required
def recharge_order_status_query():
    """查询订单状态"""
    recharge_order_id = request.args.get("recharge_order_id")
    status = db.session.query(RechargeOrder.status).filter_by(order_id=recharge_order_id).scalar()
    if status is None:
        return json.dumps({"code": 1, "msg": u"订单不存在"})

    if status == 1:
        msg = u"支付成功"
    elif status == 3:
        msg = u"处理超时"
    else:
        msg = u"支付失败"
    print msg
    return json.dumps({"code": 0, "data": {"status": status}, "msg": msg})


@bp.route("/log", methods=["GET"])
#@login_required
def recharge_log():
    """充值记录"""
    login_key = request.args.get('login_key', '')
    user_login = redis_utils.get_cache(login_key, refresh_expires=False)
    if not user_login:
        return json.dumps({'code': -99, 'msg': u'请登录'})
    user_id = json.loads(user_login)['user_id']
    page_no = int(request.args.get("page_no", 1))
    num = int(request.args.get("num", 20))
    platform = request.args.get('platform', '')
    if platform.startswith("ios"):
        device_type = 2
    elif platform.startswith("android"):
        device_type = 1
    elif platform.startswith("applet"):
        device_type = 3
    else:
        return json.dumps({"code": 1, "msg": "platform error"})

    pagination = RechargeOrder.query.filter_by(
        user_id=user_id, status=1).order_by(
        RechargeOrder.id.desc()).paginate(page_no, per_page=num, error_out=False)
    logs = pagination.items
    log_data = []
    for log in logs:
        log_data.append({
            "order_id": log.order_id,
            "money": float(log.money)/100,
            "created": log.created.__str__(),
            "result": "充值成功",
        })
    return json.dumps({"code": 0, "data": log_data})
