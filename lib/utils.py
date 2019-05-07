#coding:utf8

import hashlib
from qiniu import Auth, put_data
from flask import request, current_app
import requests

def hash_pwd(pwd):
    return hashlib.sha1(pwd).hexdigest()


def get_ip():
    return request.headers.get('X-Real-Ip') or request.remote_addr


def get_define(group, name, config=None):
    if not config:
        config = current_app.config

    defines = config['DEFINES']
    return defines[group][name]

def upload_img(filename, data, bucket_name='zhys', config=None):
    if not config:
        config = current_app.config
    cfg = config['QINIU_SETTINGS']
    access_key = cfg['access_key']
    secret_key = cfg['secret_key']
    q = Auth(access_key, secret_key)
    token = q.upload_token(bucket_name, filename)
    ret, info = put_data(token, filename, data)
    assert ret['key'] == filename
    host = cfg['buckets'][bucket_name]
    return 'http://%s/%s'%(host, filename)


def upload_img_by_url(name, img_url, retry=3):
    """上传图片到七牛"""
    resp = requests.get(img_url)
    if resp.status_code != 200:
        if retry > 1:
            resp = upload_img_by_url(name, img_url, retry=retry - 1)
        else:
            print 'Bad img url:', img_url
            return img_url
    return upload_img(name, resp.content)


def channel_collect(p):
    ''' 渠道数据收集 '''
    url = current_app.config['CHANNEL_URL'] + '/channel/collect'
    params = request.args.to_dict()
    params.update(p)
    try:
        requests.get(url, params, timeout=0.5)
    except:
        import traceback
        current_app.logger.info(traceback.format_exc())
        current_app.logger.info(str(params))

def allowed_file(filename):
    ALLOWED_EXTENSIONS = set(['png', 'PNG', 'jpg', 'JPG', 'jpeg', 'JPEG', 'gif', 'GIF'])
    return '.' in filename and \
        filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


def get_kick_key(user_id):
    return 'kick:%s' % user_id


def kick_out(user_id, exclude=''):
    """踢出某个用户"""
    current_app.redis.set(get_kick_key(user_id), exclude, ex=36000)
