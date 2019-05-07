# -*- coding: utf-8 -*-
"""
Doc:

Created on 2017/8/30
@author: MT
"""
import ujson as json
from flask import Blueprint, request, render_template
from flask_login import login_required, current_user

from lib.buy import buy_book
from lib import ios_special, utils, redis_utils
from models.book import BookChapters, PurchasedBook, Book, BookChapterContent
from models import db
from models.user import UserBalance, UserBalanceLog
from models import Banner
from models import ChannelType

bp = Blueprint('other', __name__)


def get_pay_list(platform, version, way=None):
    """
    获取支付方式列表
    :param way:
    """
    pay_group = {
        "bfbpay_alipay": {
            'name': u'支付宝',  # 贝付宝-支付宝
            'selected': 0,
            'tip': '',
            'highlight': 0,
            'type': 'pay_1',
            'icon': 'http://ssl.kdyoushu.com/alipay.png',
        },
        "wftpay_wechat": {
            'name': u'微信',  # 威富通-微信h5
            'selected': 0,
            'tip': '',
            'highlight': 0,
            'icon': 'http://ssl.kdyoushu.com/weixin.png',
            'type': 'h5_1',  # h5_1 h5浏览器 h5_2 h5 webview
            'url': '/recharge/pre_order/wftpay/wechat_h5',  # h5 相对链接
        },
        "bfbpay_bank": {
            'name': u'银联支付',  # 贝付宝-银联
            'selected': 0,
            'tip': '支付随机立减',
            'highlight': 0,
            'icon': 'http://kdjp.1yt.me/yinlian.png',
            'type': 'h5_1',  # h5_1 h5浏览器 h5_2 h5 webview
            'url': '/recharge/recharge_by_bfbpay_bank',  # h5 相对链接
        },
        "bfbpay_qq": {
            'name': u'QQ支付',  # 贝付宝-qq
            'selected': 0,
            'tip': '推荐使用QQ支付的用户',
            'highlight': 0,
            'icon': 'https://issl.1yt.me/qqwallet.png',
            'type': 'h5_1',  # h5_1 h5浏览器 h5_2 h5 webview
            'url': '/recharge/recharge_by_bfbpay_qq',  # h5 相对链接
        },
        "bfbpay_gzh": {
            'name': u'微信支付',  # 贝付宝-公众号
            'selected': 0,
            'tip': '仅支持2元及以上金额',
            'highlight': 0,
            'icon': 'https://issl.1yt.me/weixin.png',
            'type': 'h5_1',  # h5_1 h5浏览器 h5_2 h5 webview
            'url': '/recharge/recharge_by_bfbpay_wechat_gzh',  # h5 相对链接
        },
    }


    pl = []  # 网页版
    # if request.headers.get('X-Host').find('wap.kdjingpai.com') != -1:
    #     pl = ['bfbpay_gzh']

    if platform == 'ios':
        pl = ['bfbpay_alipay']

    elif platform == 'android':
        pl = ['bfbpay_alipay']
        if version >= '1.0.9':
            pl = ['wftpay_wechat', 'bfbpay_alipay']

    # 第一个默认已选
    if pl:
        pay_group.get(pl[0], {})['selected'] = 1
    return [pay_group[pay] for pay in pl if pay in pay_group]


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

def get_channel_type(platform):
    channeltypes = ChannelType.query.filter_by(showed=1,
                    platform=platform).order_by(ChannelType.ranking.desc()).all()
    return [ i.to_dict() for i in channeltypes ]


@bp.route('/config.json')
def config():
    platform = request.args.get('platform')
    v = request.args.get('v')
    m_id = request.args.get('m_id', 0, int)
    if platform == 'ios':
        res = {
            'ios_test': 1 if ios_special.is_ios_special() else 0,
            'novice_guide': 1,  # 新手引导开关
            'preload_image': 'http://ov2eyt2uw.bkt.clouddn.com/qy_ios1.png',   #默认加载图
            'preload_time': 3,
            'preload_expires': 1936988528,
            'timestamp': 32,
            'preload_data': {
            	'params':{
                     'book_id': 153920,
                     'book_name': '庶女不为后'
                 },
                 'ios_activity':'',
                 'url': ''
             },
            'check_update':{
                'lateset_version': '1.0.0',
		'force_update': False,
                'change_log': '1.更新基本功能',
                'download_url': 'http://www.baidu.com',
            }
        }
        if m_id == 1:
            res['preload_image'] = 'http://ov2eyt2uw.bkt.clouddn.com/kdxs.png'
        if m_id == 2:
            res['preload_image'] = 'http://ov2eyt2uw.bkt.clouddn.com/kdydw.PNG'
    elif platform == 'android':
        res = {
            'lateset_version': '1.1.0',
            'change_log': u'新增漫画专栏',
            'download_url': 'http://dl.kdyoushu.com/downloads/kdys.apk',
            'latest_version': 10,
            'force_update': False,
            'preload_image': 'http://ov2eyt2uw.bkt.clouddn.com/android_pre.png',  #默认加载图
            'preload_time': 3,
            'preload_expires': 1936988528,
            'timestamp': 9,
            'update_showed': 1,  # 首页更新框是否显示
        }
    else:
        res = {}
    res['channel_types'] = get_channel_type(platform)
    return json.dumps({'code':0, 'msg':'ok', 'data': res})


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

@bp.route('/landing_page', methods=['GET'])
def landing_page():
    book_id = request.args.get('book_id', '')
    if not book_id:
        return json.dumps({'code': -1, 'msg': u'信息不足'})
    print book_id
    key = 'landing_page_%s'%book_id
    redis_data = redis_utils.get_cache(key, refresh_expires=False)

    if redis_data:
        return json.dumps({'code': 0, 'data': json.loads(redis_data)})

    book = Book.query.filter_by(book_id=book_id).first()

    chapter = BookChapters.query.order_by(BookChapters.id.asc()).filter(BookChapters.book_id==book_id)[:2]
    chapter_list = []
    for ch in chapter:
        data = {
            'chapter_name': ch.chapter_name
        }
        chapter_list.append(data)
    print chapter
    content = BookChapterContent.query.filter_by(book_id=book_id, volume_id=chapter[0].volume_id, chapter_id=chapter[0].chapter_id).first()

    book_content_list = []
    data = {
        'content': content.content
    }
    book_content_list.append(data)

    last_data = {
        'book_info': book.to_dict(),
        'chapter_list': chapter_list,
        'book_content_list': book_content_list
    }
    redis_utils.set_cache(key, json.dumps(last_data), 3600)
    return json.dumps({'code': 0, 'data': last_data})


@bp.route('/tmp_proxy', methods=['GET'])
def tmp_proxy():
    url = request.args.get('url')
    import requests
    args = request.args.to_dict()
    del args['url']
    resp = requests.get(url, params=args)
    print resp.text
    return resp.text


@bp.route('/get_test_comic_images', methods=['GET'])
def get_test_comic_images():
    image_pre = 'https://ssl.kdyoushu.com/test_comic_0_%d.jpg'
    l = []
    tmp_l = []
    for i in range(1, 22):
        tmp_l.append(image_pre % i)
    for i in range(5):
        l += tmp_l
    return json.dumps({'code': 0, 'data': l})

@bp.route('/update_banner', methods=['GET'])
def update_banner():
    banners = Banner.query.all()
    for b in banners:
        b.update_channel_list()
        print b.sex, b.channel_list
        db.session.add(b)
    db.session.commit()
    return 'ok.'

@bp.route('/delete_user')
def delete_user():
    user_id = request.args.get('user_id', -1, int)
    if not user_id:
        return json.dumps({'code': -1, 'msg': u'用户不存在'})

    from models import User, db
    user = User.query.filter_by(id=user_id).first()
    if not user:
        return json.dumps({'code': -1, 'msg': u'用户不存在'})
    
    user.phone = None
    user.oauth_openid = None
    user.device_id = None

    db.session.commit()
    return json.dumps({'code': 0})

