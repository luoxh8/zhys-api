#coding:utf8

from datetime import datetime, timedelta
from flask import current_app

import re
import utils
from models.user import SmsCaptcha


def validate_captcha(phone, action, captcha):
    action = utils.get_define('SMSCAPTCHA_ACTION', action)
    if is_empty(captcha):
        return 4, '请填写验证码'
    captcha_log = SmsCaptcha.query.filter_by(phone=phone, action=action).order_by(SmsCaptcha.created.desc()).first()
    if not captcha_log:
        return 1, u'验证码错误'
    if captcha_log.captcha != captcha:
        return 3, u'验证码错误'
    return 0, 'pass'


def is_empty(val):
    return val == '' or val == None


def validate_phone(phone):
    if not phone or len(phone) != 11 or not phone.isdigit() or not phone.startswith('1'):
        return False
    return True