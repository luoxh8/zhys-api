# -*- coding: utf-8 -*-
"""
Doc: 
Created by MT at 2017/11/28
"""
import requests
from flask import Blueprint, request, jsonify
from flask_login import login_required

bp = Blueprint("bd_manage", __name__)
BD_HOST = 'http://bd-host:7016'


@bp.route('/user/list')
@login_required
def user_list():
    """bd用户列表"""
    page_no = request.args.get('page_no', 1)
    num = request.args.get('num', 100)
    params = {'page_no': page_no, 'num': num}
    ret = requests.get(BD_HOST + '/user/userlist', params)
    return jsonify(ret.json())


@bp.route('/user/info')
@login_required
def user_info():
    """bd用户信息"""
    _id = request.args.get('id', 0, int)
    params = {'id': _id}
    ret = requests.get(BD_HOST + '/user/user_info', params)
    return jsonify(ret.json())


@bp.route('/user/add', methods=['POST'])
@login_required
def user_add():
    """添加bd用户"""
    ret = requests.post(BD_HOST + '/user/add_user', data=request.form.to_dict())
    return jsonify(ret.json())


@bp.route('/user/edit', methods=['POST'])
@login_required
def user_update():
    """更新用户"""
    ret = requests.post(BD_HOST + '/user/update_user_info', data=request.form.to_dict())
    print ret.json()
    return jsonify(ret.json())


@bp.route('/user/del', methods=['POST'])
@login_required
def user_del():
    """删除用户"""
    _id = request.form.get('id', 0, int)
    params = {'user_id': _id}
    ret = requests.post(BD_HOST + '/user/delete_user', params)
    return jsonify(ret.json())
