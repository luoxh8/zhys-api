# coding=utf-8

from flask import Blueprint, request, redirect, render_template, url_for, get_flashed_messages, current_app
from flask.views import MethodView
from flask_login import login_user, logout_user, current_user, login_required
from models import AdminUser
from models import db
import hashlib
import json
from lib.admin_utils import requests_all

bp = Blueprint("channel", __name__)

@bp.route('/channel_list')
@login_required
def channel_list():
    url = current_app.config['CHANNEL_URL'] + '/admin/channel_list'
    return requests_all(url, request.args.to_dict(),'get').text

@bp.route('/add_channel', methods=['POST'])
@login_required
def add_channel():
    url = current_app.config['CHANNEL_URL'] + '/admin/add_channel'
    return requests_all(url, request.form.to_dict(),'post').text


##################################################################
# 渠道数据展示
##################################################################

@bp.route('/channel_data_detail')
@login_required
def channel_data_detail():
    url = current_app.config['CHANNEL_URL'] + '/statistics/channel_data_detail'
    return requests_all(url, request.args.to_dict(),'get').text

@bp.route('/realtime')
@login_required
def realtime():
    url = current_app.config['CHANNEL_URL']
    realtime_type = request.args.get('type', '')
    type_list = ['bind_realtime','activate_realtime', 'regist_realtime', 'pay_realtime', 'pay_number', 'click_realtime', 'display_realtime', 'newcommer_pay_number', 'newcommer_pay_realtime']
    if realtime_type not in type_list:
        return json.dumps({'code': 1, 'msg': 'type error. type=%s' %(realtime_type)})
    else:
        tmp_url = url + '/statistics/' + realtime_type
        return requests_all(tmp_url, request.args.to_dict(),'get').text

@bp.route('/get_channels')
@login_required
def get_channels():
    url = current_app.config['CHANNEL_URL'] + '/analysis/channels'
    return requests_all(url, request.args.to_dict(),'get').text


@bp.route('/get_recharge_num')
@login_required
def get_recharge_num():
    url = current_app.config['CHANNEL_URL'] + '/analysis/get_recharge_num'
    return requests_all(url, request.args.to_dict(),'get').text

@bp.route('/get_recharge_detail_info')
@login_required
def get_recharge_detail_info():
    url = current_app.config['CHANNEL_URL'] + '/analysis/get_recharge_detail_info'
    return requests_all(url, request.args.to_dict(),'get').text

@bp.route('/get_remain_num')
@login_required
def get_remain_num():
    url = current_app.config['CHANNEL_URL'] + '/analysis/get_remain_num'
    return requests_all(url, request.args.to_dict(),'get').text

@bp.route('/get_activate_recharge')
@login_required
def get_activate_recharge():
    url = current_app.config['CHANNEL_URL'] + '/analysis/get_activate_recharge'
    return requests_all(url, request.args.to_dict(),'get').text
