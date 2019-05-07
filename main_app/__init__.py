# coding: utf-8
from flask import Flask, render_template, request, abort
from lib.flask_logging import enable_logging

from models import db
import auth
from lib import redis_utils, utils
import ujson as json


# def create_app_api(pyfile=None, debug=False):
#	config = APIDebugSettings if debug else APIReleaseSettings
#	return init_app(init_base_api, config, template_folder=APIBase.TEMPLATE_FOLDER)
#
#
# def create_app_admin(pyfile=None):
#	return init_app(init_base_admin, AdminSettings, template_folder=AdminSettings.TEMPLATE_FOLDER)
#
#
# def init_app(init, config=None, template_folder='templates'):
#	app = Flask(__name__, template_folder=template_folder)
#	if config:
#		app.config.from_object(config)
#	app.static_folder = app.config.get('STATIC_FOLDER')
#	init(app)
#	if config.DEBUG == False:
#		enable_logging(app)
#	return app
#

def create_app_main(config=None):
    app = Flask(__name__)
    config = config or 'config.ReleaseConfig'
    app.config.from_object(config)

    register_db(app)

    if not app.debug:
        enable_logging(app)

    register_blueprints(app)
    register_auth(app)
    register_redis(app)
    register_check_sn(app)
    return app


def register_db(app):
    db.init_app(app)
    db.app = app
    # db.create_all()


def register_blueprints(app):
    from main_app import test
    from main_app import book
    from main_app import user
    from main_app import captcha
    from main_app import category
    from main_app import balance
    from main_app.recharge import recharge, notify
    from main_app import other
    from main_app import buy
    from main_app import activity
    from main_app.activity_v2 import bonus_acitivty

    app.register_blueprint(test.test)
    app.register_blueprint(book.book, url_prefix='/book')
    app.register_blueprint(user.user, url_prefix='/user')
    app.register_blueprint(test.test, url_prefix='/test')
    app.register_blueprint(captcha.captcha, url_prefix='/captcha')
    app.register_blueprint(category.category, url_prefix='/category')
    app.register_blueprint(balance.balance, url_prefix='/balance')
    app.register_blueprint(recharge.bp, url_prefix='/recharge')
    app.register_blueprint(notify.bp, url_prefix='/notify')
    app.register_blueprint(other.bp, url_prefix='/other')
    app.register_blueprint(buy.bp, url_prefix='/buy')
    app.register_blueprint(activity.bp, url_prefix='/activity')
    app.register_blueprint(bonus_acitivty.bp, url_prefix='/activity/v2/bonus')


def register_auth(app):
    auth.login_manager.init_app(app)
    auth.login_manager.login_view = "user.login"


def register_redis(app):
    redis_utils.init_app(app)


def register_check_sn(app):
    # sn参数校验
    @app.before_request
    def verify():
        # 本地调试不需要校验
        if utils.get_ip() in ['127.0.0.1']:
            return

        version = request.args.get('v', '', unicode)
        old_key = request.args.get('sn', '', unicode)
        platform = request.args.get('platform', '', unicode).lower()

        if platform == 'ios':
            m_id = request.args.get('m_id', -1, int)
            if m_id != -1:
                platform = 'ios_other'

        # 白名单urls
        white_list = [
            '/accounts/avatar',
            '/accounts/_avatar',
            '/accounts/not_logined',
            '/accounts/logout',
            '/accounts/pic_captcha',
            '/user/login',
            '/other/landing_page',
            '/other/upload_img',
            '/other/tmp_proxy',
            '/other/get_test_comic_images',
            '/user/change_avatar',
        ]
        if request.path in white_list or '/notify/' in request.path:
            return

        if (platform == 'android' and version < '1.0.5') or (platform == 'ios' and version < '1.0.3'):
            return

        if not request.args.get('t') or not old_key or platform not in ['android', 'ios', 'ios_other'] or not app.config['API_SECRET_KEYS'].get(platform, {}).has_key(version):
            abort(400)

        # strat verify
        import hashlib, urllib
        api_key = app.config['API_SECRET_KEYS'].get(platform).get(version)
        args = list()
        get_args = request.args
        post_args = request.form

        for key in get_args:
            if key.lower() != 'sn':
                for v in get_args.getlist(key):
                    arg_str = '%s=%s' % (key, v)
                    args.append(arg_str)
        for key in post_args:
            if key.lower() != 'sn':
                for v in post_args.getlist(key):
                    arg_str = '%s=%s' % (key, v)
                    args.append(arg_str)
        
        sorted_args = sorted(args)
        sorted_args.append(api_key)

        params = ''.join(sorted_args)
        m = hashlib.md5()
        m.update(urllib.unquote(params.encode('UTF-8')))
        md5_str = m.hexdigest()
        new_key = md5_str[:7]

        if old_key.lower() != new_key.lower():
            tmp_s = json.dumps({
                'get_params': request.args.to_dict(),
                'post_params': request.form.to_dict(),
                'sorted_params': params,
                'sorted_params_encoded': urllib.unquote(params.encode('UTF-8')),
                'server_sn': new_key.lower(),
                'client_sn': old_key.lower(),
                'server_md5': md5_str,
            })
            print '\r\n Error Verify >>>', tmp_s
            # 线下调试打开，线上生产环境注释掉。
            #return tmp_s
            abort(400)

