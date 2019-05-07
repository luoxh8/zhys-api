# -*- coding: utf-8 -*-
"""
Doc:

Created on 2017/8/30
@author: MT
"""
import ujson as json
from flask import Blueprint, request
from flask_login import login_required, current_user

from lib.applet_buy import buy_book, get_word_money, next_auto_buy
from models.book import BookChapters, PurchasedBook
from models import db
from lib import sina, redis_utils

bp = Blueprint('buy', __name__)


@bp.route('/chapter/group', methods=['POST'])
#@login_required
def _buy_group():
    """购买"""
    login_key = request.args.get('login_key', '')
    user_login = redis_utils.get_cache(login_key, refresh_expires=False)
    if not user_login:
        return json.dumps({'code': -99, 'msg': u'请登录'})
    next_auto_buy()  # 是否自动购买下一章设置
    book_id = request.form.get('book_id', 0, int)
    volume_chapter = request.form.get('volume_chapter', '')  # vid,cid|vid,cid
    platform = request.args.get('platform', '')
    rtn = buy_book(book_id, volume_chapter, platform)
    return json.dumps(rtn)


@bp.route('/chapter/info')
def chapter_info():
    """获取章节价格信息"""
    book_id = request.args.get('book_id', 0, int)
    volume_id = request.args.get('volume_id', 0, int)
    chapter_id = request.args.get('chapter_id', 0, int)
    if not book_id or volume_id or chapter_id:
        return json.dumps({"code": -1, "msg": u"参数错误"})

    chapter = BookChapters.query.filter_by(book_id=book_id, volume_id=volume_id, chapter_id=chapter_id).first()
    if not chapter:
        return json.dumps({"code": -1, "msg": u"章节不存在"})

    money = get_word_money(chapter.word_count)
    return json.dumps({"code": 0, "data": {"cost_money": money}})


@bp.route('/next/auto', methods=['POST'])
#@login_required
def next_auto():
    """是否自动购买下一章"""
    login_key = request.args.get('login_key', '')
    user_login = redis_utils.get_cache(login_key, refresh_expires=False)
    if not user_login:
        return json.dumps({'code': -99, 'msg': u'请登录'})
    next_auto_buy()
    return json.dumps({"code": 0})


@bp.route('/next/auto/list')
#@login_required
def next_auto_list():
    """自动购买列表"""
    login_key = request.args.get('login_key', '')
    user_login = redis_utils.get_cache(login_key, refresh_expires=False)
    if not user_login:
        return json.dumps({'code': -99, 'msg': u'请登录'})
    user_id = json.loads(user_login)['user_id']
    auto_list = PurchasedBook.query.filter_by(user_id=user_id, auto_buy=1).all()
    if not auto_list:
        return json.dumps({"code": 0, "data": []})
    book_id = [str(a.book_id) for a in auto_list]
    print auto_list
    book_group = db.session.execute('select book_name, book_id from book where book_id in (%s)' % str(book_id)[1:-1]).fetchall()
    book_group = {b.book_id: b.book_name for b in book_group}
    data = []
    for auto in auto_list:
        data.append({'book_id': auto.book_id, 'auto_buy': 1 if auto.auto_buy else 0,
                     'book_name': book_group.get(auto.book_id, '')})
    print data
    return json.dumps({"code": 0, "data": data})
