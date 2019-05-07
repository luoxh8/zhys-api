# coding: utf-8
import ujson as json
from flask import Blueprint, render_template, request, url_for, session, current_app, g

from applet_app.auth import token_auth, is_authenticated
from models.activity import BindPhoneActivity, UserInvite
from models.user import User, db, UserBalance, UserDetail, UserBalanceLog
from lib import utils, validators, redis_utils, pic_captcha, ios_special, wxauth
import re
import time
import datetime
import auth
import requests
import copy
from book import *

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

@user.route('/test_login', methods=['POST', 'GET'])
def test_login():
    # code = request.args.get('code', '')
    # data = wxauth.get_wxapp_session_key(code)
    # print data
    # return json.dumps(data)
    print is_authenticated()
    return ''


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


@user.route('/user_info', methods=['POST', 'GET'])
@token_auth.login_required
def user_info():
    if request.method == 'GET':
        user_id = g.user_id
        platform = request.args.get('platform', 'android')

        user = User.query.get(user_id)
        if not user:
            return json.dumps({'code': 1, 'msg': u'用户不存在'})
        user_balance = UserBalance.query.filter_by(user_id=user_id).first()
        user_list = user.to_dict()
        if not user_balance:
            user_list["balance"] = 0
        else:
            user_list["balance"] = user_balance.balance
        return json.dumps({'code': 0, 'data': user_list})

    #post修改用户信息
    login_key = request.args.get('login_key', '')
    user_login = redis_utils.get_cache(login_key, refresh_expires=False)
    if not user_login:
        return json.dumps({'code': -99, 'msg': u'请登录'})
    
    
    user_id = json.loads(user_login)['user_id']
    user = User.query.get(user_id)
    bind_phone_activity = 0
    if not user:
        return json.dumps({'code': 1, 'msg': u'用户不存在'})
    if 'encryptedData' in request.form:
        iv = request.form.get('iv')
        encryptedData = request.form.get('encryptedData')
        user_info = wxauth.get_user_info(encryptedData, iv, json.loads(user_login)['session_key'])
        applet_user = User.query.filter_by(phone=user_info['purePhoneNumber']).first()
        print user_info
        if applet_user:
            return json.dumps({'code': -1, 'msg': u'该手机号码已绑定过其他账号'})
        elif user_info['purePhoneNumber']:
            join_log = BindPhoneActivity.query.filter_by(user_id=user_id).first()
            if not join_log:
                money = 288  # 奖励阅币数
                user_balance = UserBalance.query.filter_by(user_id=user_id).with_lockmode('update').first()
                user_balance.balance += money
                db.session.add(BindPhoneActivity(user_id))
                bind_phone_activity = 1

            # 渠道绑定统计
            user.phone = user_info['purePhoneNumber']
            utils.channel_collect({'a': 'bind', 'phone': user.phone, 'device_id': user.oauth_openid})
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
    try:
        db.session.commit()
    except:
        db.session.rollback()
    return json.dumps({'code': 0, 'data': {'bind_phone_activity': bind_phone_activity}})


#@user.route('/register', methods=['POST'])
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
    login_user(user)
    # 渠道注册统计
    utils.channel_collect({'a': 'register', 'user_id': user.id})
    return json.dumps({'code': 0, 'data': user.to_dict()})


#@user.route('/change_password', methods=['POST'])
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


#@user.route('/logout', methods=['GET', 'POST'])
def logout():
    ''' 退出 '''
    session.pop('userinfo',None)
    logout_user()
    return json.dumps({'code':0, 'msg':'ok'})


@user.route('/change_avatar', methods=[ 'POST'])
#@login_required
def change_avatar():
    ''' 修改头像 '''
    login_key = request.args.get('login_key', '')
    user_login = redis_utils.get_cache(login_key, refresh_expires=False)
    if not user_login:
        return json.dumps({'code': -99, 'msg': u'请登录'})
    user_id = json.loads(user_login)['user_id']
    files = request.files['avatar']
    img_url = utils.upload_img('accounts-avatar-%d-%d' %(user_id, int(time.time())), files.read())
    user = User.query.get(user_id)
    user.avatar = img_url

    db.session.add(user)
    try:
        db.session.commit()
    except:
        return json.dumps({'code': 4, 'msg': u'网络错误'})
    return json.dumps({'code': 0, 'data': {'avatar':img_url}})


@user.route('/oauth_login', methods=['POST', 'GET'])
def oauth_login():
    """ 第三方登录 """
    code = request.form.get('code', '')
    userInfo = request.form.get('userInfo', '')
    rawData = request.form.get('rawData', '')
    signature = request.form.get('signature', '')
    encryptedData = request.form.get('encryptedData', '')
    iv = request.form.get('iv', '')
    if not iv or not encryptedData or not code:
        return json.dumps({'code': -1, 'msg': u'参数有误'})
    is_register = 0
    redis_key = code
    redis_data = redis_utils.get_cache(redis_key, refresh_expires=False)
    if redis_data:
        return json.dumps({'code': 0, 'data': {'user_info': json.loads(redis_data), 'is_register': is_register}})

    data = wxauth.get_wxapp_session_key(code)
    if 'session_key' not in data:
        return json.dumps({'code': -1, 'msg': u'网络错误'})
    user_info = wxauth.get_user_info(encryptedData, iv, data['session_key'])
    oauth_openid = user_info.get('unionId')
    if not oauth_openid:
        return json.dumps({'code': -1, 'msg': u'网络错误'})
    data['unionId'] = oauth_openid
    raw_user = User.query.filter_by(oauth_openid=oauth_openid).first()
    if not raw_user:  # 用户存在， 登陆
        is_register = 1
        # 剔除表情等特殊字符
        ip = request.headers.get('X-Real-Ip')
        nickname = _filter_str(user_info['nickName'])
        user_ra_data = json.loads(rawData)
        user_ra_data.pop('nickName', '')

        raw_user = User(
            platform='applet',
            oauth_from='applet',
            nickname=nickname,
            avatar=user_info['avatarUrl'],
            oauth_userinfo=json.dumps(user_ra_data),
            oauth_openid=oauth_openid,
            register_ip=ip,
            sex=user_info['gender'])
        raw_user.oauth_time = datetime.datetime.now()
        raw_user.oauth_nickname = nickname
        raw_user.oauth_avatar = user_info['avatarUrl']
        db.session.add(raw_user)
        db.session.flush()
        balance = UserBalance(raw_user.id, 0)
        db.session.add(balance)  # 增加余额记录
        user_detail = UserDetail(
            raw_user.id, user_ra_data.get('language'), user_ra_data.get('city'), user_ra_data.get('province'),
            user_ra_data.get('country'), data['openid'], data['unionId'])
        db.session.add(user_detail)
        # 书架增加书籍
        _add_book_shelf(raw_user.id, raw_user.sex)

        # 好友邀请
        invite(raw_user.id, balance)
        try:
            db.session.commit()
        except Exception as e:
            print 'Error', e
            db.session.rollback()
            return json.dumps({'code': -1, 'msg': u'网络错误'})

        # 渠道注册统计
        utils.channel_collect({'a': 'register', 'user_id': raw_user.id})
    data['user_id'] = raw_user.id
    raw_user_data = raw_user.to_dict()
    raw_user_data['token'] = auth.generate_auth_token(data)
    redis_utils.set_cache(redis_key, json.dumps(raw_user_data), 7200)
    return json.dumps({'code': 0, 'data': {'user_info': raw_user.to_dict(), 'is_register': is_register}})


def invite(user_id, balance):
    """好友邀请"""
    inviter_id = request.form.get('inviter_id', 0, int)
    if not inviter_id:
        return
    db.session.add(UserInvite(inviter_id, user_id))
    # 被邀请者送100阅币
    invitee_money = 100
    balance.balance += invitee_money
    log = UserBalanceLog(user_id, 1, invitee_money, "invitee_activity", inviter_id, "invite_activity")
    db.session.add(log)
    # 邀请者送30阅币
    inviter_money = 30
    row_count = db.session.query(UserBalance).filter_by(user_id=inviter_id).update({
        UserBalance.balance: UserBalance.balance + inviter_money}).count()
    print 'row_count', row_count
    if row_count == 1:
        log = UserBalanceLog(inviter_id, 1, inviter_money, "inviter_activity", user_id, "invite_activity")
        db.session.add(log)


def _filter_str(string):
    # 剔除表情等特殊字符
    char_group = []
    for c in string:
        regex = ur'^[( )(\u4e00-\u9fa5)(\u0030-\u0039)(\u0041-\u005a)(\u0061-\u007a)(~！@#￥%…&（）—“”：？》《·=、】' \
                ur'【‘’；、。，!_:`;/,<>})(\-\*\+\|\{\$\^\(\)\?\.\[\])]+$'
        if not re.match(regex, c):
            char_group.append('*')
        else:
            char_group.append(c)
    return ''.join(char_group)


def _add_book_shelf(user_id, sex):
    """书架增加默认书籍"""
    cache_key = 'cache:applet:book_ids:%s' % sex
    book_ids = current_app.redis.get(cache_key)
    if not book_ids:
        books = db.session.query(Book.book_id).filter(
            Book.free_collect==0, Book.showed==1, Book.channel_type==sex,
            Book.source.in_(current_app.config['ALLOW_SOURCE'])).all()
        book_ids = [b.book_id for b in books]
        choice_book_ids = random.sample(book_ids, 5)
        current_app.redis.set(cache_key, json.dumps(book_ids), ex=86400)
    else:
        choice_book_ids = random.sample(json.loads(book_ids), 5)
    for book_id in choice_book_ids:
        db.session.add(BookShelf(book_id, 'myself', user_id, 0, 0, True, 0))


@user.route('/get_wxcode', methods=['GET'])
def get_wxcode():
    wxauth.get_wxcode()
    return json.dumps({'code': 0, 'msg': '1'})

#批量推送接口
@user.route('/send_group_message', methods=['GET'])
def send_group_message():
    flag_key = 'send_group_message'
    args_value = request.args.get('value', '')
    flag_value = redis_utils.get_cache(flag_key, refresh_expires=False)
    if not flag_value or flag_value != args_value:
        return json.dumps({'code':0, 'msg': 'ok.'})
    redis_utils.set_cache(flag_key, '1', 10) 

    key = 'collating_message_form_list'
    redis_data = redis_utils.get_cache(key, refresh_expires=False)
    form_list = json.loads(redis_data)
    finish_list = []
    for f in copy.copy(form_list):
        if f['form_id'] == 'the formId is a mock one':
            form_list.remove(f)
            continue
        if f['open_id'] not in finish_list:
            user = User.query.filter_by(oauth_openid=f['unionId']).first()
            if user and user.created.date() == datetime.date.today():
                with open('send_group_message_new_user.log', 'a') as f:
                    f.write('%s\n' %(user.id))
                continue
            user_id = user.id if user else 0
            send_message(user_id, f)
            finish_list.append(f['open_id'])
            form_list.remove(f)
    redis_utils.set_cache(key, json.dumps(form_list), 600000) 
    return json.dumps({'code': 0, 'msg': '1'})

def send_message(user_id, f):
    book_data = requests.get('%s/user/recently_read?user_id=%s'%(current_app.config['STATS_URL'], user_id)).json()
    if not book_data['code']:
        book = Book.query.filter_by(book_id=book_data['data']['book_id']).first()
        if book and book.source in current_app.config['ALLOW_SOURCE']:
            wxauth.get_muban_message(f['form_id'], f['open_id'], book.book_name, book_data['data']['book_id'], book_data['data']['chapter_id'])
            return
    wxauth.get_muban_message(f['form_id'], f['open_id'], u'口袋阅读王', 0, 0)

#单人推送
#@user.route('/get_message', methods=['GET'])
#def get_message():
#    #form_id = request.args.get('form_id', '')
#    login_key = request.args.get('login_key', '')
#    user_login = redis_utils.get_cache(login_key, refresh_expires=False)
#    #form_id
#    key = 'collating_message_form_list'
#    redis_data = redis_utils.get_cache(key, refresh_expires=False)
#    form_list = json.loads(redis_data)
#    finish_list = []
#    for f in copy.copy(form_list):
#        if f['form_id'] == 'the formId is a mock one':
#            form_list.remove(f)
#            continue
#        if f['open_id'] not in finish_list:
#            if not f.get('user_id'):
#                user = User.query.filter_by(oauth_openid=json.loads(user_login)['unionId']).first()
#                user_id = user.id
#            else:
#                user_id = f['user_id']
#            book_data = requests.get('%s/user/recently_read?user_id=%s'%(current_app.config['STATS_URL'], user_id)).json()
#            if not book_data['code']:
#                book = Book.query.filter_by(book_id=book_data['data']['book_id']).first()
#                wxauth.get_muban_message(f['form_id'], json.loads(user_login)['openid'], book.book_name, book_data['data']['book_id'], book_data['data']['chapter_id'])
#            else:
#                wxauth.get_muban_message(f['form_id'], json.loads(user_login)['openid'], u'口袋阅读王', 0, 0)
#            finish_list.append(f['open_id'])
#            form_list.remove(f)
#    redis_utils.set_cache(key, json.dumps(form_list), 600000) 
#    return json.dumps({'code': 0, 'msg': '1'})
