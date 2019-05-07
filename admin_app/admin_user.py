# coding=utf-8

from flask import Blueprint, request, redirect, render_template, url_for, get_flashed_messages
from flask.views import MethodView
from flask_login import login_user, logout_user, current_user, login_required, current_app
from models import AdminUser, AdminUserGroup, AdminUrl, AdminGroupUrl, Image
from models import db
import hashlib
import json
from lib import utils, admin_utils

bp = Blueprint("admin_user", __name__)

@bp.route('/check_login', methods=['GET', 'POST'])
@login_required
def check_login():
    return json.dumps({'code':0})

@bp.route('/not_logined')
def not_logined():
    next = request.args.get('next','')
    return json.dumps({'code': -111, 'msg': 'need login.', 'next': next})

@bp.route('/login', methods=['POST', 'GET'])
def login():
    email = request.form.get("email")
    password = request.form.get("password")
    if not (email and password):
        email = request.args.get('email', '')
        password = request.args.get('password', '')
    pwd = utils.hash_pwd(password)
    user = AdminUser.query.filter_by(email=email).first()
    if not user:
        return json.dumps({'code':1, 'msg':'The user does not exist'})
    elif user.password != pwd and user.password != password:
        return json.dumps({'code':2, 'msg':'password error.'})

    login_user(user)
    return json.dumps({'code':0, 'data': user.to_admin_dict()})
    


@bp.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect('http://dev.admin.kdyoushu.com:7000/login.html')

@bp.route('/admin_user_list')
@login_required
def admin_user_list():
    users = AdminUser.query.all()
    user_list = [user.to_admin_dict() for user in users]
    return json.dumps({'code': 0, 'data': user_list})

@bp.route('/update_password')
@login_required
def update_password():
    if current_user.email != 'developer':
        return json.dumps({'code': 1, 'msg': 'Access denied for user.'})
    password = request.args.get('password', '')
    user_id = request.args.get('user_id', 0, int)
    if user_id and password:
        au = AdminUser.query.filter_by(id=user_id).first()
        if au:
            au.password = utils.hash_pwd(password)
            db.session.add(au)
            db.session.commit()
            return json.dumps({'code': 0, 'msg': 'ok.'})
        else:
            return json.dumps({'code':1, 'msg': 'user_id: %s, is not exist.' %(user_id)})
    else:
        return json.dumps({'code':1, 'msg': 'error, user_id: %s, password: %s' %(user_id, password)})

@bp.route('/add_user', methods=['POST', 'GET'])
@login_required
def add_user():
    if current_user.email != 'developer':
        return json.dumps({'code': 1, 'msg': 'Access denied for user.'})
    email = request.form.get('email', '')
    password = request.form.get('password', '')
    group_id = request.form.get('group_id', -1)
    if not (email and password):
        email = request.args.get('email', '')
        password = request.args.get('password', '')
        group_id = request.args.get('group_id', -1)
    if not (email and password):
        return json.dumps({'code':1, 'msg': 'miss email or password. email= %s, password=%s' %(email, password)})
    user = AdminUser.query.filter_by(email=email).first()
    if not user:
        db.session.add(AdminUser(email, utils.hash_pwd(password), group_id))
        db.session.commit()
        return json.dumps({'code':0, 'msg': 'success. email= %s, password=%s' %(email, password)})
    else:
        return json.dumps({'code':1, 'msg': 'user is exist.'})

@bp.route('/del_user', methods=['POST'])
@login_required
def del_user():
    if current_user.email != 'developer':
        return json.dumps({'code': 1, 'msg': 'Access denied for user.'})
    id = request.form.get('id', 0, int) or request.args.get('id', 0, int)
    user = AdminUser.query.filter_by(id=id).first()
    if user:
        if user.email in ['developer']:
            return json.dumps({'code': 1, 'msg': '%s can not be deleted.' %(user.email)})
        else:
            db.session.delete(user)
            db.session.commit()
            return json.dumps({'code': 0, 'msg': '%s is deleted.' %(user.email)})
    else:
        return json.dumps({'code': 1, 'msg': 'id: %s, user is not exist' %(id)})




def upload_qiniu(upload_file):
    '''七牛图片上传'''
    img = Image(upload_file.filename)
    img.url = utils.upload_img(img.filename, upload_file.read())
    db.session.add(img)
    db.session.commit()
    return img.url 

@bp.route('/upload_img', methods=['POST'])
def upload_img():
    icon = request.files['icon']
    icon_url = ''
    if icon and utils.allowed_file(icon.filename):
         icon_url = upload_qiniu(icon)
    return json.dumps({'code':0, 'data': icon_url})



@bp.route('/add_group', methods=['POST', 'GET'])
@login_required
def add_group():
    name = request.form.get('name', '') or request.args.get('name', '')
    if not name:
        return json.dumps({'code': 1, 'msg': 'name is null'})
    else:
        db.session.add(AdminUserGroup(name))
        db.session.commit()
        return json.dumps({'code': 0, 'msg': 'ok.'})

@bp.route('/del_group', methods=['POST', 'GET'])
@login_required
def del_group():
    id = request.form.get('id', 0, int) or request.args.get('id', 0, int)
    sql = 'delete from admin_user_group where id=%s' %(id)
    db.session.execute(sql)
    db.session.commit()
    return json.dumps({'code': 0, 'msg': 'ok.'})

        
@bp.route('/group_list')
@login_required
def group_list():
    groups = AdminUserGroup.query.all()
    group_list = [group.to_admin_dict() for group in groups]
    return json.dumps({'code': 0, 'data': group_list})



@bp.route('/add_url', methods=['POST', 'GET'])
@login_required
def add_url():
    path = request.form.get('path', '') or request.args.get('path', '')
    name = request.form.get('name', '') or request.args.get('name', '')
    if path and name:
        db.session.add(AdminUrl(path, name))
        db.session.commit()
        return json.dumps({'code': 0, 'msg': 'ok.'})
    else:
        return json.dumps({'code': 1, 'msg': 'path: %s -- name: %s.' %(path, name)})

@bp.route('/del_url', methods=['POST', 'GET'])
@login_required
def del_url():
    id = request.form.get('id', 0, int) or request.args.get('id', 0, int)
    sql = 'delete from admin_url where id=%s' %(id)
    db.session.execute(sql)
    db.session.commit()
    return json.dumps({'code': 0, 'msg': 'ok.'})

@bp.route('/url_list')
@login_required
def url_list():
    urls = AdminUrl.query.all()
    url_list = [url.to_admin_dict() for url in urls]
    return json.dumps({'code': 0, 'data': url_list})

@bp.route('/copy_group_url', methods=['POST', 'GET'])
@login_required
def copy_group_url():
    group_id = request.form.get('group_id', 0, int) or request.args.get('group_id', 0, int)
    copy_group_id = request.form.get('copy_group_id', 0, int) or request.args.get('copy_group_id', 0, int)
    for agu in AdminGroupUrl.query.filter_by(group_id=copy_group_id).all():
        gu = AdminGroupUrl.query.filter_by(group_id=group_id, url_id=agu.url_id).first()
        if not gu:
            db.session.add(AdminGroupUrl(group_id, agu.url_id))
    db.session.commit()
    return json.dumps({'code': 0, 'msg': 'ok.'})

@bp.route('/add_group_url', methods=['POST', 'GET'])
@login_required
def add_group_url():
    is_all = request.form.get('all', 0, int) or request.args.get('all', 0, int)
    group_id = request.form.get('group_id', 0, int) or request.args.get('group_id', 0, int)
    if is_all:
        for au in AdminUrl.query.all():
            gu = AdminGroupUrl.query.filter_by(group_id = group_id, url_id=au.id).first()
            if not gu:
                db.session.add(AdminGroupUrl(group_id, au.id))
        db.session.commit()
        admin_utils.del_group_urls_redis(group_id)
        return json.dumps({'code': 0, 'msg': 'ok.'})

    url_id = request.form.get('url_id', 0, int) or request.args.get('url_id', 0, int)
    if not (group_id and url_id):
        return json.dumps({'code': 1, 'msg': 'group_id: %s -- url_id: %s' %(group_id, url_id)})

    gu = AdminGroupUrl.query.filter_by(group_id = group_id, url_id=url_id).first()
    if not gu:
        db.session.add(AdminGroupUrl(group_id, url_id))
        db.session.commit()
        admin_utils.del_group_urls_redis(group_id)
    return json.dumps({'code': 0, 'msg': 'ok.'})

@bp.route('/del_group_url', methods=['POST', 'GET'])
@login_required
def del_group_url():
    id = request.form.get('id', 0, int) or request.args.get('id', 0, int)
    agu = AdminGroupUrl.query.filter_by(id=id).first()
    if agu:
        group_id = agu.group_id
    else:
        group_id = -1

    sql = 'delete from admin_group_url where id=%s' %(id)
    db.session.execute(sql)
    db.session.commit()
    admin_utils.del_group_urls_redis(group_id)
    return json.dumps({'code': 0, 'msg': 'ok.'})

@bp.route('/group_url_list')
@login_required
def group_url_list():
    group_id = request.form.get('group_id', 0, int) or request.args.get('group_id', 0, int)
    group_urls = AdminGroupUrl.query.filter_by(group_id=group_id).all()
    group_url_list = [group_url.to_admin_dict() for group_url in group_urls]
    return json.dumps({'code': 0, 'data': group_url_list})

@bp.route('/add_auto_url')
@login_required
def add_auto_url():
    for i in current_app.url_map.iter_rules():
        au = AdminUrl.query.filter_by(path=i).first()
        if not au:
            db.session.add(AdminUrl(i, 'auto'))
            print i
    db.session.commit()
    return 'add_auto_url is ok.'
