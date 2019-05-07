#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Doc: 
@author: MT
@time: 2016/10/28
"""
import pytest
from webtest import TestApp
import time
import hashlib
import urllib
import config
from main_app import create_app_main
from flask import url_for

API_SECRET_KEYS = config.BaseConfig.API_SECRET_KEYS


# =====功能函数======
def params_add(params=None, data=None, sign=True, **kwargs):
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
    return params


# =====fixtures========
@pytest.fixture
def app():
    """An application for the tests."""
    _app = create_app_main("config.DebugAppletConfig")
    ctx = _app.test_request_context()
    ctx.push()
    yield _app
    ctx.pop()


@pytest.fixture
def test_app(app):
    """A Webtest app."""
    return TestApp(app)


# =====测试用例========
def test_login(test_app):
    data = {'idfa': '111333'}
    resp = test_app.post(url_for('user.auto_login', **params_add(params=data)))
    assert 'id' in resp.json_body.get('data', {})


def test_error():
    assert False


if __name__ == '__main__':
    args = ['-s', '-q', '--ignore==unit_test/applet/*', '--disable-warnings', '-rfEsp', '--color=yes']
    pytest.main(args)
