# coding: utf-8
from flask import Flask, render_template, request, redirect, url_for
from lib.flask_logging import enable_logging
from flask_login import current_user

import auth
from models import AdminLog
from models import db
from lib import redis_utils, admin_utils
import json


def create_app_admin(config=None):
    app = Flask(__name__)
    config = config or 'config.ReleaseAdminConfig'
    app.config.from_object(config)

    db.init_app(app)

    if not app.debug:
        enable_logging(app)

    register_before_request(app)
    register_blueprints(app)
    register_auth(app)
    register_redis(app)
    return app


def register_blueprints(app):
    from admin_app import admin_user 
    from admin_app import channel 
    from admin_app import user 
    from admin_app import book 
    from admin_app import other
    from admin_app import book_shelf 
    from admin_app import statistics 
    from admin_app import bd_manage 
    app.register_blueprint(admin_user.bp, url_prefix='/admin_user')
    app.register_blueprint(channel.bp, url_prefix='/channel')
    app.register_blueprint(user.bp, url_prefix='/user')
    app.register_blueprint(book.bp, url_prefix='/book')
    app.register_blueprint(other.bp, url_prefix='/other')
    app.register_blueprint(book_shelf.bp, url_prefix='/book_shelf')
    app.register_blueprint(statistics.bp, url_prefix='/statistics')
    app.register_blueprint(bd_manage.bp, url_prefix='/bd_manage')


def register_auth(app):
    auth.login_manager.init_app(app)
    auth.login_manager.login_view = 'admin_user.not_logined' 
    
def register_redis(app):
    redis_utils.init_app(app)

def register_before_request(app):
    @app.before_request
    def before_request():
        return_url = ['/admin_user/login', '/admin_user/logout']
        path = request.path
        if path in return_url:
            return
        if current_user.is_authenticated:
            db.session.add(AdminLog(current_user.id, path))
            db.session.commit()
            if current_user.email == 'developer':
                return
            allow_paths = admin_utils.get_urls(current_user.group_id)
            if path not in allow_paths:
                return json.dumps({'code': 1, 'msg': 'Insufficient permissions'})
