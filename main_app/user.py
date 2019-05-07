# coding: utf-8
import ujson as json
from flask import Blueprint, render_template, request, url_for, session
from models.user import User, db, UserBalance
from lib import utils, validators, redis_utils, pic_captcha, ios_special 
from flask_login import login_user, logout_user, current_user, login_required
import re
import time
import datetime
import auth
import requests
from models import Book
from models import BookShelf

user = Blueprint('user', __name__)

def get_act_times_key(act):
    return '%s-%s-%s' % (act, request.args.get('platform', '', unicode), utils.get_ip())


def need_pic_captcha(act):
    platform = request.args.get('platform', '', unicode)
    ip = utils.get_ip()

    key = get_act_times_key(act)
    times = get_act_times(key)
    if times >= 3:
        return 1
    return 0

def get_act_times(key):
    times = redis_utils.get_cache(key, refresh_expires=False)
    print 'get act times', times
    if not times:
        times = 0
    return int(times)

def update_act_times(key, action='default'):
    times = redis_utils.get_cache(key, refresh_expires=False)
    if not times:
        times = 0
    times = int(times)
    if action == 'reset_success':
        if times > 0:
            times = 2
    else:
        times += 1
    redis_utils.set_cache(key, times, 1800)


@user.route('/login', methods=['POST', 'GET'])
def login():
    
    if request.method == 'GET':
        return json.dumps({'code': 1, 'msg': u'请先登录'})

    phone = request.form.get('phone', '')
    user_pwd = request.form.get('password', '')
    #captcha = request.form.get('captcha')#图形验证预留

    if not phone or not user_pwd:
        return json.dumps({'code': 2, 'msg': u'填写信息错误'})

    #验证码暂时不验证
    if not ios_special.is_ios_special():
        if need_pic_captcha('login'):
            if not request.form.get('pic_captcha'):
                return json.dumps({'code': -999, 'msg': u'需要图形验证'})
            if not pic_captcha.validate_code('login', request.form.get('pic_captcha', '')):
                return json.dumps({'code': -2, 'msg': u'图片验证码错误'})

    pwd = utils.hash_pwd(user_pwd)
    user = User.query.filter_by(phone=phone, password=pwd).first()
    if not user:
        return json.dumps({'code': 5, 'msg': u'用户名或密码错误'})
    #user_info = auth.UserInfo(user)
    login_user(user)
    update_act_times(get_act_times_key('login'))
    return json.dumps({'code': 0, 'data': user.to_dict()})


@user.route('/auto/login', methods=['POST'])
def auto_login():
    """免登录"""
    platform = request.args.get('platform', '')
    device_id = request.args.get('idfa', '')
    print device_id

    # 审核模式自动登录固定ID
    if ios_special.is_ios_special():
        user = User.query.filter_by(id=25).first()
        login_user(user)
        return json.dumps({'code': 0, 'data': user.to_dict()})

    if not device_id or device_id == '02:00:00:00:00:00' or device_id == '00:00:00:00:00:00' or device_id == '00000000-0000-0000-0000-000000000000':
        return json.dumps({'code': -99, 'msg': u'网络异常'})

    user = User.query.filter_by(device_id=device_id).first()
    if not user:
        user = user_register(device_id, platform, utils.get_ip())
    login_user(user)
    update_act_times(get_act_times_key('login'))
    return json.dumps({'code': 0, 'data': user.to_dict()})


def user_register(device_id, platform, register_ip):
    """用户注册"""
    user = User(device_id=device_id, platform=platform, register_ip=register_ip)
    db.session.add(user)
    db.session.commit()
    # 增加余额记录
    db.session.add(UserBalance(user.id, 0))
    db.session.commit()
    # 注册后随机5本书放在书架

    sql = 'select book_id from book order by rand() limit 5'
    book_ids = db.session.execute(sql).fetchall()
    for book_id in book_ids:
        db.session.add(BookShelf(int(book_id[0]), 'myself', user.id,  0, 0, True, 0))
    db.session.commit()


    # 渠道注册统计
    utils.channel_collect({'a': 'register', 'user_id': user.id})
    return user


@user.route('/phone/bind', methods=['POST'])
@login_required
def bind_phone():
    """绑定手机号"""
    phone = request.form.get('phone', '')
    if not validators.validate_phone(phone):
        return json.dumps({'code': -1, 'msg': u'错误的手机号'})

    captcha = request.form.get('captcha')
    code, message = validators.validate_captcha(phone, 'bind_phone', captcha)
    if message != 'pass':
        return json.dumps({'code': -1, 'msg': message})

    # 判断是否该手机号已绑定
    if User.query.filter_by(phone=phone).first():
        return json.dumps({'code': -1, 'msg': u'当前号码已绑定其他帐号'})

    user_pwd = request.form.get('password', '')
    pwd = utils.hash_pwd(user_pwd)
    user = User.query.get(current_user.id)
    if user.phone:
        return json.dumps({'code': -1, 'msg': u'当前帐号已绑定手机'})
    user.phone = phone
    user.password = pwd
    db.session.commit()

    # 渠道绑定统计
    utils.channel_collect({'a': 'bind', 'phone': phone})
    return json.dumps({'code': 0, 'data': user.to_dict()})


@user.route('/phone/bind/modify/verify', methods=['POST'])
@login_required
def bind_phone_modify_verify():
    """修改绑定手机号 验证旧手机"""
    user = User.query.get(current_user.id)
    captcha = request.form.get('captcha')
    code, message = validators.validate_captcha(user.phone, 'modify_phone_verify', captcha)
    if message != 'pass':
        return json.dumps({'code': -1, 'msg': message})
    return json.dumps({'code': 0})


@user.route('/phone/bind/modify', methods=['POST'])
@login_required
def bind_phone_modify():
    """修改绑定手机号"""
    phone = request.form.get('phone', '')
    if not validators.validate_phone(phone):
        return json.dumps({'code': -1, 'msg': u'错误的手机号'})

    captcha = request.form.get('captcha')
    code, message = validators.validate_captcha(phone, 'modify_phone', captcha)
    if message != 'pass':
        return json.dumps({'code': -1, 'msg': message})

    # 判断是否该手机号已绑定
    if User.query.filter_by(phone=phone).first():
        return json.dumps({'code': -1, 'msg': u'当前号码已绑定其他帐号'})

    user = User.query.get(current_user.id)
    user.phone = phone
    db.session.commit()

    # 渠道绑定统计
    utils.channel_collect({'a': 'bind', 'phone': phone})
    return json.dumps({'code': 0})


@user.route('/oauth/bind/cancel', methods=['POST'])
@login_required
def bind_oauth_cancel():
    """取消绑定第三方"""
    user = User.query.get(current_user.id)
    captcha = request.form.get('captcha')
    phone = request.form.get('phone')
    if not user.phone:
        if not phone:
            return json.dumps({'code': -1, 'msg': u'手机号不能为空'})
        # 判断是否该手机号已绑定
        if User.query.filter_by(phone=phone).first():
            return json.dumps({'code': -1, 'msg': u'当前号码已绑定其他帐号'})

    code, message = validators.validate_captcha(user.phone or phone, 'oauth_bind_cancel', captcha)
    if message != 'pass':
        return json.dumps({'code': -1, 'msg': message})

    if not user.phone:
        user.phone = phone
    user.oauth_from = ''
    user.oauth_openid = None
    user.oauth_userinfo = ''
    user.oauth_nickname = ''
    user.oauth_avatar = ''
    user.oauth_time = None
    db.session.commit()
    return json.dumps({'code': 0})


@user.route('/switch_by/phone', methods=['POST'])
@login_required
def switch_by_phone():
    """切换帐号"""
    phone = request.form.get('phone')
    if not validators.validate_phone(phone):
        return json.dumps({'code': -1, 'msg': u'错误的手机号'})

    user = User.query.filter_by(phone=phone).first()
    if not user:
        return json.dumps({'code': -1, 'msg': u'帐号不存在'})
    user_pwd = request.form.get('password', '')
    if user_pwd:
        pwd = utils.hash_pwd(user_pwd)
        if user.password != pwd:
            return json.dumps({'code': -1, 'msg': u'密码错误'})
    else:
        captcha = request.form.get('captcha')
        code, message = validators.validate_captcha(phone, 'switch_user', captcha)
        if message != 'pass':
            return json.dumps({'code': -1, 'msg': message})

    cur_user = User.query.get(current_user.id)
    if cur_user.phone == phone:
        return json.dumps({'code': -1, 'msg': u'无法切换到当前帐号'})
    device_id = cur_user.device_id
    cur_user.device_id = None
    db.session.commit()
    user.device_id = device_id
    db.session.commit()

    login_user(user)
    update_act_times(get_act_times_key('login'))
    return json.dumps({'code': 0, 'data': user.to_dict()})


@user.route('/switch_by/oauth', methods=['POST'])
@login_required
def switch_by_oauth():
    """ 第三方登录切换 """
    oauth_from = request.form['oauth_from'].lower()
    oauth_openid = request.form['open_id']
    access_token = request.form['token']
    nickname = request.form.get('user_name')
    avatar = request.form.get('avatar')
    if oauth_from not in ['sinaweibo', 'qzone', 'wechat']:
        return json.dumps({'code': 3, 'msg': u'暂不支持此方式登录'})

    def validate_and_get_userinfo():
        if oauth_from == 'sinaweibo':
            ret = requests.get('https://api.weibo.com/2/users/show.json',
                               params={'access_token': access_token, 'uid': int(oauth_openid)})
            ret = ret.json()
            return ret.get('error_code', 0) == 0, ret
        elif oauth_from == 'qzone':
            ret = requests.get('https://graph.qq.com/user/get_user_info',
                               params={'access_token': access_token, 'openid': oauth_openid,
                                       'oauth_consumer_key': '1106176184', 'format': 'json'})
            print ret.text
            ret = ret.json()
            return ret['ret'] == 0, ret
        elif oauth_from == 'wechat':
            ret = requests.get('https://api.weixin.qq.com/sns/userinfo',
                               params={'access_token': access_token, 'openid': oauth_openid})
            print ret.text
            ret = ret.json()
            return ret.get('errcode', 0) == 0, ret
    import time
    _s1 = time.time()
    is_valid, oauth_userinfo = validate_and_get_userinfo()
    _s2 = time.time()
    print 'validate', _s2 - _s1

    print oauth_userinfo
    if not is_valid:
        return json.dumps({'code': 3, 'msg': 'err'})

    if oauth_from == 'wechat':
        oauth_openid = oauth_userinfo['unionid']
    elif oauth_from == 'qzone':
        avatar = oauth_userinfo.get('figureurl_qq_2') or avatar
    
    if oauth_from == 'wechat':
        raw_user = User.query.filter_by(oauth_openid=oauth_openid).first()
    else:
        raw_user = User.query.filter_by(oauth_openid=oauth_openid, oauth_from=oauth_from).first()
    print 'raw_user >>>>>>>>>>>>>>>>>>>>>>>>>>>>>', raw_user

    _s3 = time.time()
    print 'query', _s3 - _s2

    cur_user = User.query.get(current_user.id)
    if raw_user:  # 用户存在， 登陆
        device_id = cur_user.device_id
        cur_user.device_id = None
        db.session.commit()
        raw_user.device_id = device_id
        db.session.commit()

        login_user(raw_user)
        update_act_times(get_act_times_key('login'))
        return json.dumps({'code': 0, 'data': {'user_info': raw_user.to_dict()}})
    else:
        # 剔除表情等特殊字符
        name_group = []
        for c in nickname:
            regex = ur'''^[( )(\u4e00-\u9fa5)(\u0030-\u0039)(\u0041-\u005a)(\u0061-\u007a)(~！@#￥%…&（）—“”：？》《·=、】【‘’；、。，!_:`;/,<>})(\-\*\+\|\{\$\^\(\)\?\.\[\])]+$'''
            if not re.match(regex, c):
                name_group.append('*')
            else:
                name_group.append(c)
        nickname = ''.join(name_group)
        cur_user.oauth_from = oauth_from
        cur_user.oauth_openid = oauth_openid
        cur_user.nickname = nickname
        cur_user.avatar = avatar
        cur_user.oauth_userinfo = json.dumps(oauth_userinfo)
        cur_user.oauth_time = datetime.datetime.now()
        cur_user.oauth_nickname = nickname
        cur_user.oauth_avatar = avatar
        try:
            db.session.commit()
        except:
            return json.dumps({'code': -1, 'msg': u'网络错误'})

        _s4 = time.time()
        print 'bind oauth', _s4 - _s3
        return json.dumps({'code': 0, 'data': {'user_info': cur_user.to_dict()}})


@user.route('/user_info', methods=['POST', 'GET'])
@login_required
def user_info():
    if request.method == 'GET':
        user_id = current_user.id
        platform = request.args.get('platform', 'android')

        user = User.query.get(user_id)
        if not user:
            return json.dumps({'code': 1, 'msg': u'用户不存在'})
        user_balance = UserBalance.query.filter_by(user_id=current_user.id).first()
        user_list = user.to_dict()
        if not user_balance:
            user_list["balance"] = 0
        else:
            user_list["balance"] = user_balance.balance
        return json.dumps({'code': 0, 'data': user_list})

    #post修改用户信息
    user_id = current_user.id
    user = User.query.get(user_id)
    if not user:
        return json.dumps({'code': 1, 'msg': u'用户不存在'})
    if 'notify_phone' in request.form:
        
        captcha = request.form.get('captcha', '')
        code, msg = validators.validate_captcha(request.form.get('notify_phone'), 'SET_NOTIFY_PHONE', captcha)
        if code != 0:
            return json.dumps({'code': 3, 'msg': u'验证码输入不正确'})

        if re.match("^1(3|4|5|7|8)\d{9}$", request.form.get('notify_phone')) != None:
            user.notify_phone = request.form.get('notify_phone')
    if 'nickname' in request.form:
        if len(request.form.get('nickname')) < 50:
            user.nickname = request.form.get('nickname')
    if 'intro' in request.form:
        if len(request.form.get('intro')) < 300:
            user.intro = request.form.get('intro')
    if 'aphorism' in request.form:
        if len(request.form.get('aphorism')) < 200:
            user.aphorism = request.form.get('aphorism')
    if 'sex' in request.form:
        if int(request.form.get('sex')) in [1, 2]:
            user.sex = int(request.form.get('sex'))

    db.session.add(user)
    db.session.commit()
    return json.dumps({'code': 0, 'data': {}})


@user.route('/register', methods=['POST'])
def register():
    phone = request.form.get('phone', '')
    password = request.form.get('password', '')
    #new_password = request.form.get('new_password', '')#是否有重复输入需求
    #nickname = request.form.get('nickname', '')
    platform = request.args.get('platform', '')
    register_ip = utils.get_ip()
    if not phone or re.match("^1(3|4|5|7|8)\d{9}$", phone) == None:
        return json.dumps({'code': 1, 'msg': u'电话号码格式不正确'})
    if not password or len(password)<6 or len(password)>30:
        return json.dumps({'code': 2, 'msg': u'密码不符'})
    #if not nickname or len(nickname)>50:
    #    return json.dumps({'code': 3, 'msg': u'昵称太长'})
    
    captcha = request.form.get('captcha', '')
    code, msg = validators.validate_captcha(phone, 'REGISTER', captcha)
    if code != 0:
        return json.dumps({'code': 3, 'msg': u'验证码输入不正确'})

    pwd = utils.hash_pwd(password)
    user =  User(phone=phone, platform=platform, register_ip=register_ip, password=pwd)

    db.session.add(user)
    try:
        db.session.commit()
    except:
        return json.dumps({'code': 4, 'msg': u'网络错误'})
    # 增加余额记录
    db.session.add(UserBalance(user.id, 0))
    db.session.commit()

    login_user(user)
    # 渠道注册统计
    utils.channel_collect({'a': 'register', 'user_id': user.id})
    return json.dumps({'code': 0, 'data': user.to_dict()})


@user.route('/change_password', methods=['POST'])
def change_password():
    phone = request.form.get('phone', '')
    new_password = request.form.get('new_password', '')
    if not phone or not new_password or len(new_password)<6 or len(new_password)>30:
        return json.dumps({'code': 1, 'msg': u'修改信息有误'})
    user = User.query.filter_by(phone=phone).first()
    if not user:
        return json.dumps({'code': 2, 'msg': u'用户不存在'})
    
    captcha = request.form.get('captcha', '')
    code, msg = validators.validate_captcha(phone, 'RESETPWD', captcha)
    if code != 0:
        return json.dumps({'code': 3, 'msg': u'验证码输入不正确'})

    user.password = utils.hash_pwd(new_password)
    db.session.add(user)
    try:
        db.session.commit()
    except:
        return json.dumps({'code': 4, 'msg': u'网络错误'})
    return json.dumps({'code': 0, 'data': {}})


@user.route('/pic_captcha', methods=['GET'])
def user_pic_captcha():
    act = request.args.get('act')
    return pic_captcha.make_captcha(act)


@user.route('/logout', methods=['GET', 'POST'])
def logout():
    ''' 退出 '''
    session.pop('userinfo',None)
    logout_user()
    return json.dumps({'code':0, 'msg':'ok'})


@user.route('/change_avatar', methods=[ 'POST'])
@login_required
def change_avatar():
    ''' 修改头像 '''
    files = request.files['avatar']
    img_url = utils.upload_img('accounts-avatar-%d-%d' %(current_user.id, int(time.time())), files.read())
    user = User.query.get(current_user.id)
    user.avatar = img_url

    db.session.add(user)
    try:
        db.session.commit()
    except:
        return json.dumps({'code': 4, 'msg': u'网络错误'})
    return json.dumps({'code': 0, 'data': {'avatar':img_url}})


@user.route('/oauth_login', methods=['POST'])
def oauth_login():
    """ 第三方登录 """
    oauth_from = request.form['oauth_from'].lower()
    oauth_openid = request.form['open_id']
    access_token = request.form['token']
    nickname = request.form.get('user_name')
    avatar = request.form.get('avatar')

    if oauth_from not in ['sinaweibo', 'qzone', 'wechat']:
        return json.dumps({'code': 3, 'msg': u'暂不支持此方式登录'})

    def validate_and_get_userinfo():
        if oauth_from == 'sinaweibo':
            ret = requests.get('https://api.weibo.com/2/users/show.json',
                               params={'access_token': access_token, 'uid': int(oauth_openid)})
            ret = ret.json()
            return ret.get('error_code', 0) == 0, ret
        elif oauth_from == 'qzone':
            ret = requests.get('https://graph.qq.com/user/get_user_info',
                               params={'access_token': access_token, 'openid': oauth_openid,
                                       'oauth_consumer_key': '1106176184', 'format': 'json'})
            print ret.text
            ret = ret.json()
            return ret['ret'] == 0, ret
        elif oauth_from == 'wechat':
            ret = requests.get('https://api.weixin.qq.com/sns/userinfo',
                               params={'access_token': access_token, 'openid': oauth_openid})
            print ret.text
            ret = ret.json()
            return ret.get('errcode', 0) == 0, ret
    import time
    _s1 = time.time()
    is_valid, oauth_userinfo = validate_and_get_userinfo()
    _s2 = time.time()
    print 'validate', _s2 - _s1

    print oauth_userinfo
    if not is_valid:
        return json.dumps({'code': 3, 'msg': 'err'})

    if oauth_from == 'wechat':
        oauth_openid = oauth_userinfo['unionid']

    raw_user = User.query.filter_by(oauth_openid=oauth_openid).first()
    print 'raw_user >>>>>>>>>>>>>>>>>>>>>>>>>>>>>', raw_user

    _s3 = time.time()
    print 'query', _s3 - _s2
    
    if raw_user:  # 用户存在， 登陆
        login_user(raw_user)
        return json.dumps({'code': 0, 'data': {'user_info': raw_user.to_dict()}})
    else:
        # 剔除表情等特殊字符
        name_group = []
        for c in nickname:
            regex = ur'''^[( )(\u4e00-\u9fa5)(\u0030-\u0039)(\u0041-\u005a)(\u0061-\u007a)(~！@#￥%…&（）—“”：？》《·=、】【‘’；、。，!_:`;/,<>})(\-\*\+\|\{\$\^\(\)\?\.\[\])]+$'''
            if not re.match(regex, c):
                name_group.append('*')
            else:
                name_group.append(c)
        nickname = ''.join(name_group)
        ip = request.headers.get('X-Real-Ip')
        user = User(
            oauth_from=oauth_from,
            oauth_openid=oauth_openid,
            nickname=nickname,
            avatar=avatar,
            register_ip=ip,
            oauth_userinfo=json.dumps(oauth_userinfo))
        db.session.add(user)

        try:
            db.session.commit()
            # 渠道注册统计
            utils.channel_collect({'a': 'register', 'user_id': user.id})
        except:
            return json.dumps({'code': -1, 'msg': u'网络错误'})
        
        # 增加余额记录
        db.session.add(UserBalance(user.id, 0))
        db.session.commit()

        _s4 = time.time()
        print 'regist', _s4 - _s3
        
        login_user(user)
        return json.dumps({'code': 0, 'data': {'user_info': user.to_dict()}})
