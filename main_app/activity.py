# -*- coding: utf-8 -*-
"""
Doc:

Created on 2017/9/15
@author: MT
"""
import datetime
import ujson as json
from flask import Blueprint, request
from flask_login import login_required, current_user

from models.activity import SignIn, BindPhoneActivity
from models import db
from models.user import UserBalanceLog, UserBalance, User

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
    user_sign = SignIn.query.filter_by(user_id=current_user.id).first()
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
    if platform not in ['ios', 'android']:
        return json.dumps({'code': -1, 'msg': '参数错误'})

    user_sign = SignIn.query.filter_by(user_id=current_user.id).with_lockmode('update').first()
    today = datetime.date.today()
    if not user_sign:
        user_sign = SignIn(current_user.id, today, json.dumps([today.day]))
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
    log = UserBalanceLog(current_user.id, 1, SIGN_IN_BONUS, "sign_in", '', "sign_in", platform)
    db.session.add(log)
    # 增加阅币
    db.session.query(UserBalance).filter_by(user_id=current_user.id).update({
        UserBalance.balance: UserBalance.balance + SIGN_IN_BONUS
    })

    try:
        db.session.commit()
    except Exception:
        import traceback
        traceback.print_exc()
        db.session.rollback()
    return json.dumps({'code': 0})


@bp.route('/sign_in/multi_bonus', methods=['POST'])
@login_required
def sign_in_multi_bonus():
    """连续签到奖励领取"""
    platform = request.args.get('platform')
    if platform not in ['ios', 'android']:
        return json.dumps({'code': -1, 'msg': '参数错误'})

    user_sign = SignIn.query.filter_by(user_id=current_user.id).with_lockmode('update').first()
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
    log = UserBalanceLog(current_user.id, 1, bonus, "multi_sign_bonus", day_num, "multi_sign_bonus", platform)
    db.session.add(log)
    # 增加阅币
    db.session.query(UserBalance).filter_by(user_id=current_user.id).update({
        UserBalance.balance: UserBalance.balance + bonus
    })

    try:
        db.session.commit()
    except Exception:
        import traceback
        traceback.print_exc()
        db.session.rollback()
    return json.dumps({'code': 0})


@bp.route('/bind_phone/info', methods=['GET'])
@login_required
def bind_phone_info():
    """获取活动信息（绑定手机送288阅币）"""
    user_id = current_user.id

    user = User.query.filter_by(id=user_id).first()
    if not user:
        return json.dumps({'code': -1, 'msg': u'用户不存在'})

    data = {'bind_phone': 0, 'received': 0}
    if user.phone:
        data['bind_phone'] = 1

    join_log = BindPhoneActivity.query.filter_by(user_id=user_id).first()
    if join_log:
        data['received'] = 1

    return json.dumps({'code': 0, 'data': data})


@bp.route('/bind_phone/receive', methods=['POST'])
@login_required
def bind_phone_receive():
    """领取奖励（绑定手机送288阅币）"""
    platform = request.args.get('platform', '', unicode)
    user_id = current_user.id
    money = 288  # 奖励阅币数

    join_log = BindPhoneActivity.query.filter_by(user_id=user_id).first()
    if join_log:
        return json.dumps({'code': -1, 'msg': u'您已领取过奖励'})

    if platform.lower() not in ['android', 'ios']:
        return json.dumps({'code': -1, 'msg': u'平台类型错误'})

    user = User.query.filter_by(id=user_id).first()
    if not user:
        return json.dumps({'code': -1, 'msg': u'用户不存在'})

    user_balance = UserBalance.query.filter_by(user_id=user_id).with_lockmode('update').first()
    user_balance.balance += money
    db.session.add(BindPhoneActivity(user_id))
    db.session.commit()

    return json.dumps({'code': 0})
