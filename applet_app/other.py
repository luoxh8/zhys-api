# -*- coding: utf-8 -*-
"""
Doc:

Created on 2017/8/30
@author: MT
"""
import ujson as json
from flask import Blueprint, request, render_template, current_app
from flask_login import login_required, current_user

from lib.buy import buy_book
from lib import ios_special, utils, redis_utils, applet_special
from models.book import BookChapters, PurchasedBook
from models import db
from models.user import UserBalance, UserBalanceLog
import datetime
import copy
from models import ChannelType

bp = Blueprint('other', __name__)


def get_pay_list(platform, version, way=None):
    """
    获取支付方式列表
    :param way:
    """
    pay_group = [
        {
            'name': u'微信支付',  # 威富通
            'selected': [1, 3, 5, 10, 30, 50, 100, 200],
            'tip': '',
            'highlight': 0,
            'icon': 'https://issl.1yt.me/weixin.png',
            'type': 'wxpay',  #y
            'url': '',  # h5 相对链接
            'rate': 100
        },
    ]


    return pay_group


@bp.route('/pay/list')
def pay_list():
    """获取支付列表"""
    platform = request.args.get('platform', '')
    version = request.args.get('v', '')
    way = request.args.get('way')  # 支付列表用途
    data = {
        'pay_list': get_pay_list(platform, version, way),
    }
    return json.dumps({"code": 0, "data": data})

def get_channel_type():
    channeltypes = ChannelType.query.filter_by(showed=1,
                        platform='applet').order_by(ChannelType.ranking.desc()).all()
    data = [ i.to_dict() for i in channeltypes ]
    return  data

@bp.route('/config.json')
def config():
    res = {
        'timestamp': 5,
        'applet_test': 1 if applet_special.is_applet_special() else 0,
        'recharge_options': current_app.config['RECHARGE_OPTIONS']['applet'],
        'channel_types': get_channel_type(),
    }
    return json.dumps({'code':0, 'data': res})


@bp.route('/upload_img', methods=['GET', 'POST'])
def upload_img():
    
    if request.method == 'GET':
        return render_template('upload_img.html')
    else:
        icon = request.files['avatar']
        icon_url = ''
        if icon and allowed_file(icon.filename):
             icon_url = upload_qiniu(icon)
        return json.dumps({'code':0, 'data': icon_url})
        

def allowed_file(filename):
    ALLOWED_EXTENSIONS = set(['png', 'PNG', 'jpg', 'JPG', 'jpeg', 'JPEG', 'gif', 'GIF'])
    return '.' in filename and \
        filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

def upload_qiniu(upload_file):
    '''七牛图片上传'''
    return utils.upload_img(upload_file.filename, upload_file.read())


@bp.route('/collating_message', methods=['GET', 'POST'])
def collating_message():
    ''' 保存formid '''
    form_id = request.args.get('form_id', '')
    login_key = request.args.get('login_key', '')
    user_login = redis_utils.get_cache(login_key, refresh_expires=False)
    if not user_login:
        return json.dumps({'code': -99, 'msg': u'请登录'})

    if not form_id:
        return json.dumps({'code': -1, 'msg': u'参数有误'})
    key = 'collating_message_form_list'
    now = datetime.datetime.now()
    end_date = (datetime.datetime.now() + datetime.timedelta(days = 7))
    data = {
        'form_id': form_id,
        'open_id': json.loads(user_login)['openid'],
        'unionId': json.loads(user_login)['unionId'],
        'user_id': json.loads(user_login)['user_id'],
        'start_date': now.strftime("%Y-%m-%d %H:%M:%S"),
        'end_date': end_date.strftime("%Y-%m-%d %H:%M:%S")
    }
    redis_data = redis_utils.get_cache(key, refresh_expires=False)
    if redis_data:
        form_list = json.loads(redis_data)
        for f in copy.copy(form_list):
            if f['end_date'] < now.strftime("%Y-%m-%d %H:%M:%S"):
                form_list.remove(f)
        form_list.append(data)
    else:
        form_list = [data]
    redis_utils.set_cache(key, json.dumps(form_list), 600000)
    return json.dumps({'code': 0, 'msg': u'ok'})
