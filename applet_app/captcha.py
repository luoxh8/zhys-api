#coding:utf8
import random
from datetime import datetime, timedelta

from flask import Blueprint, request
import config
import json
from lib import utils, validators, redis_utils, pic_captcha
from models.user import User, SmsCaptcha, db
import re

captcha = Blueprint('captcha', __name__)

def gen_captcha():
    return str(random.randint(100000, 999999))


def get_act_times_key(act):
    return '%s-%s-%s' % (act, request.args.get('platform', '', unicode), utils.get_ip())


def need_pic_captcha(act):
    platform = request.args.get('platform', '', unicode)
    ip = utils.get_ip()

    key = get_act_times_key(act)
    times = get_act_times(key)
    if times >= 3:
        return 1
    return 0

def get_act_times(key):
    times = redis_utils.get_cache(key, refresh_expires=False)
    print 'get act times', times
    if not times:
        times = 0
    return int(times)


def update_act_times(key, action='default'):
    times = redis_utils.get_cache(key, refresh_expires=False)
    if not times:
        times = 0
    times = int(times)
    if action == 'reset_success':
        if times > 0:
            times = 2
    else:
        times += 1
    redis_utils.set_cache(key, times, 1800)


@captcha.route('/send/<action>')
def send(action):
    
    o_action = action
    phone = request.args.get('phone')
    
    if not phone or re.match("^1(3|4|5|7|8)\d{9}$", phone) == None:
        return json.dumps({'code': 1, 'msg': u'手机号码有误'})
    user = User.query.filter_by(phone=phone).first()

    if action == 'register':
        action = utils.get_define('SMSCAPTCHA_ACTION', 'REGISTER')

        if need_pic_captcha('register'):
            if not request.args.get('pic_captcha'):
                return json.dumps({'code': -999, 'msg': u'需要图形验证'})
            if not pic_captcha.validate_code('register', request.args.get('pic_captcha', '')):
                return json.dumps({'code': -2, 'msg': u'图片验证码错误'})
        
        if user:
            return json.dumps({'code': 1, 'msg': u'用户已经存在'})
        update_act_times(get_act_times_key('register'))
    elif action == 'reset_pwd':
        action = utils.get_define('SMSCAPTCHA_ACTION', 'RESETPWD')
        
        if need_pic_captcha('resetpwd'):
            if not request.args.get('pic_captcha'):
                return json.dumps({'code': -999, 'msg': u'需要图形验证'})
            if not pic_captcha.validate_code('resetpwd', request.args.get('pic_captcha', '')):
                return json.dumps({'code': -2, 'msg': u'图片验证码错误'})
        
        if not user:
            return json.dumps({'code': 2, 'msg': u'用户不存在'})
        update_act_times(get_act_times_key('resetpwd'))
    elif action == 'set_notify_phone':
        
        if need_pic_captcha('set_notify_phone'):
            if not request.args.get('pic_captcha'):
                return json.dumps({'code': -999, 'msg': u'需要图形验证'})
            if not pic_captcha.validate_code('set_notify_phone', request.args.get('pic_captcha', '')):
                return json.dumps({'code': -2, 'msg': u'图片验证码错误'})
        
        action = utils.get_define('SMSCAPTCHA_ACTION', 'SET_NOTIFY_PHONE')
        update_act_times(get_act_times_key('set_notify_phone'))

    last_sent = SmsCaptcha.query.filter_by(phone=phone, action=action).order_by(SmsCaptcha.created.desc()).first()
    if last_sent and (datetime.now() - last_sent.created) < timedelta(seconds=60):
        return json.dumps({'code': 5, 'msg': u'已发送请等待'})
    captcha = gen_captcha()

    from services.sms import send_sms
    send_sms.delay(phone, u'您的验证码是：%s 请不要将验证码透露给其他人，如非本人操作，请忽略' %captcha)
    print captcha
    db.session.add(SmsCaptcha(phone=phone, captcha=captcha, action=action ))
    db.session.commit()

    return json.dumps({'code': 0, 'data': {}})




    


