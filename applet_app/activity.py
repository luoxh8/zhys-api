# -*- coding: utf-8 -*-
"""
Doc:

Created on 2017/9/15
@author: MT
"""
import datetime
import ujson as json
from random import randint

from flask import Blueprint, request, g
from auth import login_required

from models.activity import SignIn
from models import db
from models.book import Book
from models.user import UserBalanceLog, UserBalance

bp = Blueprint('activity', __name__)

# ===================
# 签到
SIGN_IN_BONUS = 30  # 签到奖励
MULTI_SIGN_BONUS = {  # 连续签到奖励
    7: 50,
    14: 70,
    21: 100,
    28: 150,
}


@bp.route('/sign_in/info')
@login_required
def sign_in_info():
    """签到信息"""
    data = {
        "sign_days": [],
        "multi_sign_bonus": [],
    }
    user_sign = SignIn.query.filter_by(user_id=g.user_id).first()
    if user_sign:
        today = datetime.date.today()
        if user_sign.last_sign_day.year < today.year or user_sign.last_sign_day.month < today.month:
            user_sign.sign_days = '[]'
            user_sign.multi_sign_bonus = '[]'
        data = {
            "sign_days": json.loads(user_sign.sign_days),
            "multi_sign_bonus": json.loads(user_sign.multi_sign_bonus),
        }
    print data
    return json.dumps({"code": 0, "data": data})


@bp.route('/sign_in', methods=['POST'])
@login_required
def sign_in():
    """签到"""
    platform = request.args.get('platform')
    if platform not in ['ios', 'android', 'applet']:
        return json.dumps({'code': -1, 'msg': '参数错误'})

    user_sign = SignIn.query.filter_by(user_id=g.user_id).with_lockmode('update').first()
    today = datetime.date.today()
    if not user_sign:
        user_sign = SignIn(g.user_id, today, json.dumps([today.day]))
        db.session.add(user_sign)
    else:
        if user_sign.last_sign_day >= today:
            return json.dumps({"code": -1, "msg": "今日已签到"})

        if user_sign.last_sign_day.year < today.year or user_sign.last_sign_day.month < today.month:
            user_sign.sign_days = '[]'
            user_sign.multi_sign_bonus = '[]'

        sign_days = json.loads(user_sign.sign_days)
        if today.day in sign_days:
            return json.dumps({"code": -1, "msg": "今日已签到"})

        sign_days.append(today.day)
        user_sign.last_sign_day = today
        user_sign.sign_days = json.dumps(sign_days)

    # 记录用户流水
    money = randint(20, 40)
    log = UserBalanceLog(g.user_id, 1, money, "sign_in", '', "sign_in", platform)
    db.session.add(log)
    # 增加阅币
    db.session.query(UserBalance).filter_by(user_id=g.user_id).update({
        UserBalance.balance: UserBalance.balance + money
    })

    try:
        db.session.commit()
    except Exception:
        import traceback
        traceback.print_exc()
        db.session.rollback()
    return json.dumps({'code': 0, 'bonus': money})


# @bp.route('/sign_in/multi_bonus', methods=['POST'])
# @login_required
def sign_in_multi_bonus():
    """连续签到奖励领取"""
    platform = request.args.get('platform')
    if platform not in ['ios', 'android']:
        return json.dumps({'code': -1, 'msg': '参数错误'})

    user_sign = SignIn.query.filter_by(user_id=g.user_id).with_lockmode('update').first()
    if not user_sign:
        return json.dumps({'code': -1, 'msg': '未满足领取条件'})

    today = datetime.date.today()
    if user_sign.last_sign_day.year < today.year or user_sign.last_sign_day.month < today.month:
        return json.dumps({'code': -1, 'msg': '未满足领取条件'})

    day_num = request.form.get('day_num', 0, int)
    bonus = MULTI_SIGN_BONUS.get(day_num)
    if not bonus:
        return json.dumps({'code': -1, 'msg': '参数错误'})

    sign_day_num = len(json.loads(user_sign.sign_days))
    if sign_day_num < day_num:
        return json.dumps({'code': -1, 'msg': '未满足领取条件'})

    multi_sign_bonus = json.loads(user_sign.multi_sign_bonus)
    if day_num in multi_sign_bonus:
        return json.dumps({'code': -1, 'msg': '已领取'})

    multi_sign_bonus.append(day_num)
    user_sign.multi_sign_bonus = json.dumps(multi_sign_bonus)

    # 记录用户流水
    log = UserBalanceLog(g.user_id, 1, bonus, "multi_sign_bonus", day_num, "multi_sign_bonus", platform)
    db.session.add(log)
    # 增加阅币
    db.session.query(UserBalance).filter_by(user_id=g.user_id).update({
        UserBalance.balance: UserBalance.balance + bonus
    })

    try:
        db.session.commit()
    except Exception:
        import traceback
        traceback.print_exc()
        db.session.rollback()
    return json.dumps({'code': 0})


@bp.route('/invite/info')
@login_required
def invite_info():
    """好友邀请详情"""
    users = db.session.execute('select u.nickname,u.avatar,i.created from user_invite i,user u '
                               'where i.user_id=:user_id and i.invitee_id=u.id', {'user_id': g.user_id}).fetchall()
    invitee_info = [{'nickname': u.nickname,
                     'avatar': u.avatar or 'http://ov2eyt2uw.bkt.clouddn.com/default_avatar.png',
                     'created': u.created.strftime('%m月%d日 %H:%M')} for u in users]
    sum_prize = db.session.execute('select sum(money) as sm from user_balance_log where user_id=:user_id '
                                   'and corresponding_id="inviter_activity"', {'user_id': g.user_id}).fetchone()
    return json.dumps({'code': 0, 'data': {'invitees': invitee_info, 'prize_coin': int(sum_prize.sm)}})


@bp.route('/invite/share_book_list', methods=['GET'])
def share_book_list():
    """书籍分享列表"""
    book_ids = [5387733, 5387734, 5387735, 5387736]
    datas = {'male': [], 'female': [], 'comic': []}
    books = Book.query.filter(Book.book_id.in_(book_ids), Book.showed==True).all()
    for item in books:
        book_type = 'male' if item.channel_type == 1 else 'female'
        if item.is_comic:
            book_type = 'comic'
        datas[book_type].append({
            'book_id': item.book_id,
            'cover': item.cover,
            'book_name': item.book_name,
            'intro': item.intro,
            'author': item.author,
        })
    return json.dumps({'code': 0, 'data': datas})
