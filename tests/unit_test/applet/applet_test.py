#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Doc: 
@author: MT
@time: 2016/10/28
"""
import pytest
from webtest import TestApp
from applet_app import create_app_applet
from flask import url_for


# =====功能函数======
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


# =====fixtures========
@pytest.fixture
def app():
    """An application for the tests."""
    _app = create_app_applet("config.DebugAppletConfig")
    ctx = _app.test_request_context()
    ctx.push()
    yield _app
    ctx.pop()


@pytest.fixture
def test_app(app):
    """A Webtest app."""
    return TestApp(app)


# =====测试用例========
def test_user_info(test_app):
    resp = test_app.get(url_for('user.user_info'),  headers={"Authorization": 'zhysToken ' + gen_token()})
    assert 'id' in resp.json_body.get('data', {})


if __name__ == '__main__':
    args = ['-s', '-q', '--ignore=unit_test/app/*', '--disable-warnings', '-rfEsp', '--color=yes']
    pytest.main(args)
