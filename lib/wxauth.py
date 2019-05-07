#coding:utf8
import requests
import datetime
import redis_utils
import uuid
import ujson as json
import redis_lock
from flask import current_app
from WXBizDataCrypt import WXBizDataCrypt
from flask import current_app

WXAPP_ID = 'wx28c8a74bd01f5e3a'
#WXAPP_ID = 'wx8e8fc77f7f2ef904'

WXAPP_SECRET = '1c7efd0054d7ac6aaa84b4205e6e3794'
#WXAPP_SECRET = '0624061fa7638f0538299c6973ff059a'


def get_wxapp_session_key(code):
    cache_key = 'cache:wx_session_key:%s' % code
    redis_data = current_app.redis.get(cache_key)
    if redis_data:
        return json.loads(redis_data)
    url = 'https://api.weixin.qq.com/sns/jscode2session?appid=%s&secret=%s&js_code=%s&grant_type=authorization_code' % \
          (WXAPP_ID, WXAPP_SECRET, code)
    data = requests.get(url).json()
    redis_utils.set_cache(cache_key, json.dumps(data), 7200)
    return data


def get_user_info(encryptedData, iv, session_key):
    pc = WXBizDataCrypt(WXAPP_ID, session_key)
    return pc.decrypt(encryptedData, iv)

def get_wxcode():
    key = 'access_token'
    redis_data = redis_utils.get_cache(key, refresh_expires=False)
    if redis_data:
        token_data = json.loads(redis_data)
    else:
        url = 'https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=%s&secret=%s'%(WXAPP_ID, WXAPP_SECRET)
        token_data = requests.get(url).json()
        redis_utils.set_cache(key, json.dumps(token_data), 7000)
    data = {
        #'path':'https://devzhysapi2.xiaoxianetwork.com/book/get_content?book_id=5373849&volume_id=2251&chapter_id=2199&platform=applet',
        #'path': u'pages/reader/reader?book_id=5387770&index=2&s=yjfs',
        #'path': u'pages/text/text?book_id=5387770&index=2&s=yjfs',
        #'path': u'activity/mind/mind?s=l6k4',
        'path': u'pages/recommend/recommend',
        'width': 430,
        'auto_color': False
        #'line_color': {"r":"0","g":"0","b":"0"}
    }
    url_a = 'https://api.weixin.qq.com/wxa/getwxacode?access_token=%s'%token_data['access_token']
    headers = {'content-type': 'application/json'}
    a = requests.post(url_a, data=json.dumps(data), headers=headers)
    open('qr_code.jpg', 'wb').write(a.content)
    print 111
    return 111

def get_muban_message(form_id, openid, book_name, book_id, chapter_id):
    import datetime
    key = 'access_token'
    redis_data = redis_utils.get_cache(key, refresh_expires=False)
    if redis_data:
        token_data = json.loads(redis_data)
    else:
        url = 'https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=%s&secret=%s'%(WXAPP_ID, WXAPP_SECRET)
        token_data = requests.get(url).json()
        redis_utils.set_cache(key, json.dumps(token_data), 7000)
    if book_id and chapter_id:
        page = 'pages/reader/reader?book_id=%s&chapter_id=%s&collection=reader_from_template'%(book_id, chapter_id)
    else:
        page = 'pages/recommend/recommend?collection=recommend_from_template'
    data = {
        'touser': openid,
        'template_id': 'I6sgTLk1Lw9Is4J81leD8l4ROMIekrSMWlgh5vdwpVg',
        'form_id': form_id,
        'page': page,
        'data': {
            'keyword1': {
                "value": book_name,
            },
            'keyword2': {
                "value": str(datetime.date.today()),
            },
            'keyword3': {
                "value": '火爆更新，立即观看！',
                "color": '#FF4040',
            },
        'color': '#5db4fe',

        },
        "emphasis_keyword": "keyword1.DATA",
    }
    print data
    url = 'https://api.weixin.qq.com/cgi-bin/message/wxopen/template/send?access_token=%s'%token_data['access_token']
    headers = {'content-type': 'application/json'}
    a = requests.post(url, data=json.dumps(data), headers=headers)


def send_custom_msg(data):
    """客服接口 发消息"""
    api_url = 'https://api.weixin.qq.com/cgi-bin/message/custom/send?access_token=' + get_access_token()
    resp = requests.post(api_url, data=json.dumps(data, ensure_ascii=False))
    print resp.text


def get_access_token():
    cache_key = 'access_token'
    with redis_lock.Lock(current_app.redis, cache_key, expire=10, auto_renewal=True):
        _get_access_token(cache_key)

def _get_access_token(cache_key):
    token = current_app.redis.get(cache_key)
    if not token:
        url = 'https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=%s&secret=%s' % \
            (WXAPP_ID, WXAPP_SECRET)
        token = requests.get(url).text
        assert 'access_token' in token
        current_app.redis.set(cache_key, token, ex=7000)
    return json.loads(token)['access_token']

