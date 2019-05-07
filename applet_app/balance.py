# coding: utf-8
import ujson as json
from flask import Blueprint, request
from flask_login import login_user, logout_user, current_user, login_required
from lib import sina, redis_utils
from models.user import *

balance = Blueprint('balance', __name__)


@balance.route('/get_balance')
#@login_required
def get_balance():
    ''' 获取钱包信息 '''
    login_key = request.args.get('login_key', '')
    user_login = redis_utils.get_cache(login_key, refresh_expires=False)
    if not user_login:
        return json.dumps({'code': -99, 'msg': u'请登录'})
    platform = request.args.get('platform', 'android')
    user_id = json.loads(user_login)['user_id']
    user_balance = UserBalance.query.filter_by(user_id=user_id).first()
    if not user_balance:
        balance = 0
    else:
        balance = user_balance.balance    
    data = {
        'balance': balance,
    }

    return json.dumps({'code': 0, 'data': data})


@balance.route('/log')
#@login_required
def buy_log():
    """消费记录"""
    login_key = request.args.get('login_key', '')
    user_login = redis_utils.get_cache(login_key, refresh_expires=False)
    if not user_login:
        return json.dumps({'code': -99, 'msg': u'请登录'})
    page_no = int(request.args.get("page_no", 1))
    num = int(request.args.get("num", 20))
    platform = request.args.get('platform', '')
    user_id = json.loads(user_login)['user_id']
    pagination = UserBalanceLog.query.filter(
        UserBalanceLog.user_id == user_id, UserBalanceLog.exec_type == 2,
        ).order_by(
        UserBalanceLog.id.desc()).paginate(page_no, per_page=num, error_out=False)
    logs = pagination.items
    if not logs:
        return json.dumps({"code": 0, "data": []})

    log_book_dict = {}
    log_chapter_dict = {}
    log_data_group = []
    for log in logs:
        data = {
            'title': '',
            'content': '',
            'created': log.created_time.__str__(),
            'money': log.money,
            'id': log.id,
            'corresponding': log.corresponding,
        }
        if log.corresponding == 'buy_book':
            corresponding_id = log.corresponding_id.split('-')
            book_id, chapter_table_ids = int(corresponding_id[0]), corresponding_id[1]
            if book_id:
                log_book_dict[log.id] = book_id
            if chapter_table_ids:
                chapter_table_ids = chapter_table_ids.split('|')
                log_chapter_dict[log.id] = int(chapter_table_ids[-1])
                if len(chapter_table_ids) > 1:
                    data['is_group'] = True  # 是否批量购买
        log_data_group.append(data)

    # 获取书籍名
    book_group = db.session.execute('select book_id, book_name from book where book_id in (%s)' %
                                    str(log_book_dict.values())[1:-1]).fetchall()
    book_group = {b.book_id: b.book_name for b in book_group}

    # 获取章节名
    chapter_group = db.session.execute(
        'select id, chapter_name from book_chapters where id in (%s)' %
        str(log_chapter_dict.values())[1:-1]).fetchall()
    chapter_group = {c.id: c.chapter_name for c in chapter_group}

    for log in log_data_group:
        if log['corresponding'] == 'buy_book':
            log['title'] = book_group.get(log_book_dict.get(log['id'], 0), '')
            log['content'] = '批量购买至 ' if log.get('is_group') else ''
            log['content'] += chapter_group.get(log_chapter_dict.get(log['id'], 0), '')
        del log['id']
        del log['corresponding']

    return json.dumps({"code": 0, "data": log_data_group})
