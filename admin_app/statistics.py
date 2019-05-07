# coding=utf-8

from flask import Blueprint, request, redirect, render_template, url_for, get_flashed_messages, current_app
from flask_login import login_user, logout_user, current_user, login_required
from models import Book, BookCategory, BookVolume, BookChapters
from models import db
import json
from lib import utils
from lib.admin_utils import requests_all

bp = Blueprint("statistics", __name__)

@bp.route('/book_data')
@login_required
def book_data():
    sort_by = request.args.get('sort_by', '')
    page_no = int(request.args.get("page_no", 1))
    num = int(request.args.get("num", 20))

    url = current_app.config['STATS_URL'] + '/admin/book_data'
    ret = requests_all(url, request.args.to_dict(),'get').json()
    if ret['code'] != 0:
        return json.dumps(ret)
    else:
        ret = ret['data']
        if sort_by in ('read_people', 'buy_people', 'money', 'buy_first_time', 'read_times', 'read_first_time', 'bookshelf', 'display'):
            keys = sorted(ret, key=lambda k: ret[k][sort_by], reverse=True)
        else:
            keys = ret.keys()
    total = len(ret)
    data_list = []
    end_num = page_no * num
    if ret.has_key('0'):
        tmp_data = ret['0']
        tmp_data['book_name'] = u'所有'
        tmp_data['author_name'] = 'unknow'
        tmp_data['source'] = 'unknow'
        tmp_data['cate_id'] = 'unknow'
        tmp_data['book_id'] = '0'
        data_list.append(tmp_data)
        ret.pop('0')
        keys.remove('0')
        end_num = end_num - 1
    for book_id in keys[(page_no-1)*num: end_num]:
        bk = Book.query.filter_by(book_id=book_id).first()
        data = ret[book_id]
        data['book_name'] = bk.book_name if bk else 'unknow'
        data['author_name'] = bk.author_name if bk else 'unknow'
        data['source'] = bk.source if bk else 'unknow'
        if bk:
            data['cate_id'] = bk.to_admin_dict()['cate_id']
        else:
            data['cate_id'] = 'unknow'
        data['book_id'] = book_id
        if book_id == '0':
            data['book_name'] = u'所有'
        data_list.append(data)
    return json.dumps({'code':0, 'data': data_list, 'total': total})

@bp.route('/book_chapter_data')
@login_required
def book_chapter_data():
    book_id = request.args.get('book_id', 0, int)
    url = current_app.config['STATS_URL'] + '/admin/book_chapter_data'
    ret = requests_all(url, request.args.to_dict(),'get').json()
    if ret['code'] != 0:
        return json.dumps(ret)
    else:
        ret = ret['data']
    data_list = []
    for chapter_id in ret.keys():
        bc = BookChapters.query.filter_by(book_id=book_id, chapter_id=chapter_id).first()
        data = ret[chapter_id]
        data['chapter_name'] = bc.chapter_name if bc else 'unknow'
        data['need_fee'] = bc.money if bc else 0
        data_list.append(data)
    return json.dumps({'code':0, 'data': data_list})
