# coding: utf-8
import ujson as json
from flask import Blueprint, request, current_app
from flask_login import login_user, logout_user, current_user, login_required
from lib import sina, redis_utils
from models.book import *
from models.bookshelf import *

category = Blueprint('category', __name__)

@category.route('/get_type')
def get_type():
    ''' 获取类型列表 '''
    platform = request.args.get('platform', 'android')
    v = request.args.get('v')
    m_id = request.args.get('m_id', 0, int)
    key = 'get_type_%s' % platform
    redis_data = redis_utils.get_cache(key, refresh_expires=False)
    if redis_data:
        json.dumps({'code':0, 'data': json.loads(redis_data)})
    parent_list = {1: u'男生', 2: u'出版', 3: u'女生'}
    type_list = {}
    for parent in parent_list:
        category_list = []
        book_category = BookCategory.query.filter_by(parent_id=parent, showed=True).all()
        for c in book_category:
            if v == '1.0.0' and int(c.cate_id) in [3014, 2011] and not m_id:
                pass
            else:
                category_list.append(c.to_dict())
        type_list[parent] = category_list 

    data = {
        'parent_list': parent_list,
        'type_list': type_list
    }
    redis_utils.set_cache(key, json.dumps(data), 600)
    return json.dumps({'code': 0, 'data': data})


@category.route('/get_book')
def get_book():
    ''' 根据类型获取书籍 '''
    cate_id = request.args.get('cate_id')
    page_no = int(request.args.get("page_no", 1))
    num = int(request.args.get("num", 20))
    pagination = Book.query.filter(Book.cate_id==cate_id, Book.source.in_(current_app.config['ALLOW_SOURCE'])).paginate(page_no, per_page=num, error_out=False)
    books = pagination.items
    book_list = []
    for book in books:
        book_dict = book.to_dict()
        category = BookCategory.query.filter_by(cate_id=book.cate_id).first()
        book_dict['cate_name'] = category.cate_name
        book_list.append(book_dict)

    data = {
        'book_list': book_list,
        'cate_id': cate_id,
        'page_no': page_no,
        'num': num
    }
    return json.dumps({'code': 0, 'data': data})



