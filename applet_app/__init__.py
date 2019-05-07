# coding: utf-8
from flask import Flask, render_template, request
from lib.flask_logging import enable_logging

from models import db
import auth
from lib import redis_utils


def create_app_applet(config=None):
    app = Flask(__name__)
    config = config or 'config.AppletConfig'
    app.config.from_object(config)

    register_db(app)

    if not app.debug:
        enable_logging(app)

    register_blueprints(app)
    # register_auth(app)
    register_redis(app)
    register_check_sn(app)
    return app


def register_db(app):
    db.init_app(app)
    db.app = app


def register_blueprints(app):
    from applet_app import book
    from applet_app import user
    from applet_app import captcha
    from applet_app import category
    from applet_app import balance
    from applet_app.recharge import recharge, notify
    from applet_app import other
    from applet_app import buy
    from applet_app import activity
    from applet_app import customer_service

    app.register_blueprint(book.book, url_prefix='/book')
    app.register_blueprint(user.user, url_prefix='/user')
    app.register_blueprint(captcha.captcha, url_prefix='/captcha')
    app.register_blueprint(category.category, url_prefix='/category')
    app.register_blueprint(balance.balance, url_prefix='/balance')
    app.register_blueprint(recharge.bp, url_prefix='/recharge')
    app.register_blueprint(notify.bp, url_prefix='/notify')
    app.register_blueprint(other.bp, url_prefix='/other')
    app.register_blueprint(buy.bp, url_prefix='/buy')
    app.register_blueprint(activity.bp, url_prefix='/activity')
    app.register_blueprint(customer_service.bp, url_prefix='/customer_service')


# def register_auth(app):
#     auth.login_manager.init_app(app)
#     auth.login_manager.login_view = "user.login"


def register_redis(app):
    redis_utils.init_app(app)


def register_check_user(app):
    # 校验用户(未使用)
    @app.before_request
    def check_user():
        code = request.args.get('code', '')
        login_key = request.args.get('login_key', '')
        oauth_openid = data['openid']
        data, key = wxauth.get_wxapp_session_key(code, login_key)
        if data.get('user_id'):
            return
        raw_user = User.query.filter_by(oauth_openid=oauth_openid, oauth_from='applet').first()
        if not raw_user:
            return json.dumps({'code': -1, 'msg': u'请重新登录'})
        data['user_id'] = raw_user.id
        redis_utils.set_cache(key, json.dumps(data), 86400)


        
def register_check_sn(app):
    @app.before_request
    def check_sn():
        return
