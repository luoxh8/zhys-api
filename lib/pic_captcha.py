#coding:utf8
'''
     图形验证码
'''
import random
import time

from flask import session, current_app, make_response, abort, request
from flask_login import LoginManager, current_user
from captcha.image import ImageCaptcha



def refresh_code(act):
    code = '%04d' %random.randint(0,9999)
    print '=================Refresh code', session
    key = 'captcha_%s'%(act)
    session[key] = session.get(key,{})
    session[key]['code'] = code
    session[key]['ts'] = int(time.time())
    #print "refresh_code", code
    print session
    return code


def make_captcha(act): 
    cfg = current_app.config['CAPTCHA_SETTINGS']
    #assert act in cfg['acts']
    if act not in cfg['acts']:
        abort(400)
    code = refresh_code(act) # 先刷新 再生成
    image = ImageCaptcha()
    data = image.generate(code)
    resp = make_response(data.read())
    resp.content_type = 'image/png'
    return resp


def validate_code(act, code):
    cfg = current_app.config['CAPTCHA_SETTINGS']
    #assert act in cfg['acts']
    if act not in cfg['acts']:
        abort(400)
    key = 'captcha_%s'%(act)
    s_info = session.get(key,{})
    old_code = s_info.get('code')
    ts = s_info.get('ts',0)

    print '===============validate code', session
    print request.form
    #print ts+cfg['expires'], time.time()
    if ts + cfg['expires'] < time.time(): # 过期时间
        #print "验证码超时", old_code, code
        refresh_code(act)
        return False

    refresh_code(act)
    print ">>>>>>>>>>>>>", old_code, code

    return old_code == code

