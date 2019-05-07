#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Doc: 
@author: MT
@time: 2016/10/28
"""
from timeit import timeit
import pytest
import requests
import json
import datetime
import time
import hashlib
import urllib
import config

# BASE_URL = 'http://dev.api.kdyoushu.com:7000'
BASE_URL = 'http://127.0.0.1:5000'
session = requests.session()
API_SECRET_KEYS = config.BaseConfig.API_SECRET_KEYS


# =====功能函数======
def pretty_print(resp):
    """打印字典美化"""
    try:
        print json.dumps(resp.json(), indent=4, ensure_ascii=False)
    except:
        print resp.text


def rq(method, path, params=None, data=None, sign=True, **kwargs):
    if not params:
        params = {}
    if not data:
        data = {}
    params['t'] = int(time.time())
    params['v'] = '1.0.4'
    params['platform'] = 'ios'
    key = API_SECRET_KEYS.get(params['platform']).get(params['v'])
    if sign:
        arg_group = []
        for args in [params, data]:
            for k, v in args.iteritems():
                arg_group.append('%s=%s' % (k, v))
        arg_group = sorted(arg_group)
        arg_group.append(key)
        args = ''.join(arg_group)
        m = hashlib.md5()
        m.update(urllib.unquote(args.encode('UTF-8')))
        new_key = m.hexdigest()[:7]
        params['sn'] = new_key.lower()
    resp = getattr(session, method)(BASE_URL + path, params=params, data=data, **kwargs)
    pretty_print(resp)
    return resp


def get(path, params=None, data=None, sign=True, **kwargs):
    return rq('get', path, params, data, sign, **kwargs)


def post(path, params=None, data=None, sign=True, **kwargs):
    return rq('post', path, params, data, sign, **kwargs)


def login():
    post('/user/login', data={'phone': '17690288801', 'password': '3269696'})


# =====fixtures========
def setup_module(module):
    login()
    import traceback
    traceback.print_exc()


def teardown_module(module):
    pass


def setup_function(function):
    pass


def teardown_function(function):
    pass


# =====测试用例========

def _test_get_content_multi():
    resp = post('/book/get_content/multi', data={'book_id': 225657, 'volume_chapter': '2220,1927'})
    print resp.headers
    data = resp.json()['data'][0]['content']
    print data


def test_user_info():
    resp = get('/user/user_info', params={'login_key': 222}, headers={"Authorization": 'ZHYSToken eyJhbGciOiJIUzI1NiIsImV4cCI6MTUxMDgyMzE1NSwiaWF0IjoxNTEwODIzMTM1fQ.eyJvcGVuaWQiOiJvby1QeTBOcTlKZkZTTEM4NlgzeFRyRWU5dVRJIiwic2Vzc2lvbl9rZXkiOiJld1lrTWlDMkx0VjRRN05LS21yZGhRPT0iLCJ1c2VyX2lkIjoxLCJ1bmlvbklkIjoib2x6RVpzN3hWRENITHFXcUhNYTlmQlQ4RTk1NCJ9.kYuwovk9Xb6mWNEYmNS4YXUsPf3ru4IVjxKY1JdS0S8'})
    # resp = get('/user/user_info', params={'login_key': 222})
    # resp = get('/user/user_info', params={'login_key': 223})


def test_sign_in():
    get('/balance/get_balance', params={'login_key': 111})
    get('/activity/sign_in/info', params={'login_key': 111})
    post('/activity/sign_in', params={'login_key': 111})
    get('/balance/get_balance', params={'login_key': 111})


def gen_token():
    from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
    data = {
        'user_id': 1,
        'openid': 'oo-Py0Nq9JfFSLC86X3xTrEe9uTI',
        'session_key': 'ewYkMiC2LtV4Q7NKKmrdhQ==',
        'unionId': 'olzEZs7xVDCHLqWqHMa9fBT8E954',
    }
    s = Serializer('CmNDp9oi9uj2OeW2P0E1w932lk', expires_in=20)
    return s.dumps(data)

if __name__ == '__main__':
    # print gen_token()
    test_user_info()
