# coding: utf-8
from flask import g, current_app
from flask_httpauth import HTTPTokenAuth
from itsdangerous import (TimedJSONWebSignatureSerializer as Serializer,
                          BadSignature, SignatureExpired)
import ujson as json

token_auth = HTTPTokenAuth(scheme='ZHYSToken')


def generate_auth_token(data, expiration=7200):
    """生成带用户信息的token"""
    if 'user_id' not in data:
        raise Exception('Wrong auth data!')
    s = Serializer(current_app.config['SECRET_KEY'], expires_in=expiration)
    return s.dumps(data)


@token_auth.error_handler
def error_back():
    return json.dumps({'code': -999, 'msg': u'请登录'})


@token_auth.verify_token
def verify_auth_token(token):
    """验证Token"""
    g.is_auth = False
    s = Serializer(current_app.config['SECRET_KEY'])
    try:
        data = s.loads(token)
    except SignatureExpired:
        return False # valid token, but expired
    except BadSignature:
        return False # invalid token
    g.user = data
    g.user_id = data['user_id']
    g.is_auth = True
    return True


def is_authenticated():
    is_auth = getattr(g, 'is_auth', None)
    if is_auth is not None:
        return is_auth
    return token_auth.login_required(lambda: None)() is None

from functools import wraps
from flask import request
import json
def login_required(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        login_key = request.args.get('login_key', '')
        user_login = current_app.redis.get(login_key)
        if not user_login:
            return json.dumps({'code': -99, 'msg': u'请登录'})
        g.user_id = json.loads(user_login)['user_id']
        return func(*args, **kwargs)
    return decorated_view
