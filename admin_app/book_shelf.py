# coding=utf-8

from datetime import datetime
from flask import Blueprint, request
from flask_login import login_required, current_app
from models import BookShelfName, BookShelf, Book, AdminUrl
from models import db
import json
from lib import utils

bp = Blueprint("book_shelf", __name__)

@bp.route('/index')
def index():
    return 'book_shelf is ok.'

@bp.route('/book_shelf_name_list')
@login_required
def book_shelf_name_list():
    bsns = BookShelfName.query.all()
    data = [ bsn.to_admin_dict() for bsn in bsns]
    return json.dumps({'code': 0, 'data': data})

@bp.route('/add_book_shelf_name', methods=['POST', 'GET'])
@login_required
def add_book_shelf_name():
    name = request.form.get('name', '') or request.args.get('name', '')
    nickname = request.form.get('nickname', '') or request.args.get('nickname', '')
    bsn = BookShelfName.query.filter_by(name=name).first()
    if bsn:
        return json.dumps({'code': 1, 'msg': 'name:%s bookshelf is exist.' %(name)})

    data = request.args.to_dict() if request.method == 'GET' else request.form.to_dict()

    bsn = BookShelfName(data)
    db.session.add(bsn)
    db.session.commit()
    return json.dumps({'code': 0, 'data': bsn.to_admin_dict()})

@bp.route('/update_book_shelf_name', methods=['POST', 'GET'])
@login_required
def update_book_shelf_name():
    _id = request.form.get('id') or request.args.get('id', '')
    bsn = BookShelfName.query.filter_by(id=_id).first()
    if bsn:
        bsn.update(request.form.to_dict())
        db.session.add(bsn)
        db.session.commit()
        return json.dumps({'code': 0, 'data': bsn.to_admin_dict()})
    else:
        return json.dumps({'code': 1, 'msg': 'bookshelf is not exist.'}) 

@bp.route('/book_shelf_books')
@login_required
def book_shelf_books():
    page_no = int(request.args.get("page_no", 1))
    num = int(request.args.get("num", 20))
    name = request.form.get('name', '') or request.args.get('name', '')
    sql = 'select count(*) from book_shelf where name="%s" ' %(name)
    total = db.session.execute(sql).scalar() or 0
    books = BookShelf.query.filter_by(name=name, showed=True)
    books = books.order_by(BookShelf.ranking.desc(), BookShelf.updated.asc())[(page_no-1)*num: page_no * num]
    data = [ bs.to_admin_dict() for bs in books ]
    return json.dumps({'code': 0, 'data': data, 'total': total})

@bp.route('/add_book', methods=['POST', 'GET'])
@login_required
def add_book_shelf():
    book_id = request.form.get('book_id', 0, int) or request.args.get('book_id', 0, int)
    name = request.form.get('name', '') or request.args.get('name', '')
    sex = request.form.get('sex', 0, int) or request.args.get('sex', 0, int)
    ranking = request.form.get('ranking', 0, int) or request.args.get('ranking', 0, int)
    rate = request.form.get('rate', 0, int) or request.args.get('rate', 0, int)
    showed = request.form.get('showed', 1, int) or request.args.get('showed', 1, int)
    bs = BookShelf.query.filter_by(book_id=book_id, name=name).first()
    if bs:
        return json.dumps({'code': 1, 'msg': '%s: bookshelf, %s: book_id is exist.' %(name, book_id)})
    else:
        bk = Book.query.filter_by(book_id=book_id).first()
        if not bk:
            return json.dumps({'code': 1, 'msg': '%s, book is not exist.' %(book_id)})
        bs = BookShelf(book_id, name, 0, ranking, rate, showed, sex)
        db.session.add(bs)
        db.session.commit()
        return json.dumps({'code': 0, 'data': bs.to_admin_dict()})


@bp.route('/update_book_ranking', methods=['POST', 'GET'])
@login_required
def update_book_ranking():
    _id = request.form.get('id', 0, int) or request.args.get('id', 0, int)
    ranking = request.form.get('ranking', 0, int) or request.args.get('ranking', 0, int)
    sql = 'update book_shelf set ranking=%s where id=%s' %(ranking, _id)
    db.session.execute(sql)
    db.session.commit()
    return json.dumps({'code': 0, 'msg': 'ok.'})

@bp.route('/del_book', methods=['POST', 'GET'])
@login_required
def del_book():
    _id = request.form.get('id', 0, int) or request.args.get('id', 0, int)
    sql = 'delete from book_shelf where id=%s' %(_id)
    db.session.execute(sql)
    db.session.commit()
    return json.dumps({'code': 0, 'msg': 'ok.'})
