# coding: utf-8
import datetime
import random
import ujson as json
import requests
import hashlib
from flask import Blueprint, request, current_app, g
from sqlalchemy.sql import or_

from auth import login_required
from lib import redis_utils, wxauth
from lib.wx_crypt import WXBizMsgCrypt

from lib.buy import get_word_money
from lib.ios_special import is_ios_special
from lib.applet_special import is_applet_special

bp = Blueprint('customer_service', __name__)

def check_signature():
    timestamp = request.args.get('timestamp', '')
    nonce = request.args.get('nonce', '')
    signature = request.args.get('signature', '')
    if not (timestamp and nonce and signature):
        return False 

    token = current_app.config['WX_TOKEN']
    array = [token, timestamp, nonce]
    array_str = ''.join(sorted(array))
    if hashlib.sha1(array_str).hexdigest() == signature:
        return True
    else:
        return False 

@bp.route('/index', methods=['POST', 'GET'])
def index():
    if request.method == 'GET':
        if check_signature():
           return request.args.get('echostr', '')
        return 'error'
    elif request.method == 'POST':
        data = json.loads(request.data)
        print data
        msg_sign = request.args.get('msg_signature', '')
        timestamp = request.args.get('timestamp', '')
        nonce = request.args.get('nonce', '')
        decrypt = WXBizMsgCrypt(current_app.config['WX_TOKEN'], current_app.config['WX_AESKEY'], current_app.config['WXAPP_ID'])
        ret, data = decrypt.DecryptMsg(data, msg_sign, timestamp, nonce)
        data = json.loads(data)
        print ret, data
        if ret != 0:
            return 'error'
        if data['MsgType'] == 'event' and data['Event'] == 'user_enter_tempsession':
            print u'进入会话'
            if data['SessionFrom'] == 'download':
                send_download_custom_msg(data['FromUserName'])

        return 'success'
    else:
        return 'error'


def send_download_custom_msg(openid):
    """客服接口 发消息"""
    from services import async_req
    data = {
        "touser": openid,
        "msgtype": "link",
        "link": {
            "title": "点此进入",
            "description": "安装口袋有书客户端，海量免费书任看",
            "url": "http://app.kdyoushu.com/?channel_id=enua",
            "thumb_url": "http://ov2eyt2uw.bkt.clouddn.com/app_icon.png"
        }
    }
    async_req.send_custom_msg.delay(data)

