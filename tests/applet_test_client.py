#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Doc: 
@author: MT
@time: 2016/10/28
"""
from timeit import timeit
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
    params['platform'] = 'applet'
    resp = getattr(session, method)(BASE_URL + path, params=params, data=data, **kwargs)
    pretty_print(resp)
    return resp


def get(path, params=None, data=None, sign=True, **kwargs):
    return rq('get', path, params, data, sign, **kwargs)


def post(path, params=None, data=None, sign=True, **kwargs):
    return rq('post', path, params, data, sign, **kwargs)


def gen_token():
    from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
    data = {
        'user_id': 1,
        'openid': 'oo-Py0Nq9JfFSLC86X3xTrEe9uTI',
        'session_key': 'ewYkMiC2LtV4Q7NKKmrdhQ==',
        'unionId': 'olzEZs7xVDCHLqWqHMa9fBT8E954',
    }
    s = Serializer('CmNDp9oi9uj2OeW2P0E1w932lk', expires_in=2000)
    return s.dumps(data)


# =====测试用例========
def test_user_info():
    resp = get('/user/user_info', headers={"Authorization": 'zhysToken ' + gen_token()})
    assert 'id' in resp.json().get('data', {})


if __name__ == '__main__':
    test_user_info()
