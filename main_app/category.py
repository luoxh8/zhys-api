# coding: utf-8
import codecs
import ujson as json
from flask import Blueprint, request
from flask_login import login_user, logout_user, current_user, login_required
from lib import sina, redis_utils
from models.book import *
from models.bookshelf import *

category = Blueprint('category', __name__)

def get_categorys(parent_id, num):
    categorys = BookCategory.query.filter_by(parent_id=parent_id, showed=True)[: num]
    cate_list = [ c.to_dict() for c in categorys ]
    return cate_list


def get_other_categorys(parent_id, num):
    data = [
        # style 1没有榜单头样式 2有榜单头样式
        { 'cate_id': -401, 'cate_name': u'17k男生订阅榜', 'parent_id': 4, 'icon': 'http://ov2eyt2uw.bkt.clouddn.com/other_categorys_17k_man.png', 'style': 1},
        { 'cate_id': -402, 'cate_name': u'17k女生订阅榜', 'parent_id': 4, 'icon': 'http://ov2eyt2uw.bkt.clouddn.com/other_categorys_17k_woman.png', 'style': 1},
        { 'cate_id': -403, 'cate_name': u'百度热搜榜', 'parent_id': 4, 'icon': 'http://ov2eyt2uw.bkt.clouddn.com/other_categorys_baidu_hot.png', 'style': 1},
        { 'cate_id': -404, 'cate_name': u'起点男生风云榜', 'parent_id': 4, 'icon': 'http://ov2eyt2uw.bkt.clouddn.com/other_categorys_qd_man.png', 'style': 1},
        { 'cate_id': -405, 'cate_name': u'起点女生风云榜', 'parent_id': 4, 'icon': 'http://ov2eyt2uw.bkt.clouddn.com/other_categorys_qd_woman.png', 'style': 1},
        { 'cate_id': -406, 'cate_name': u'阅读王男生畅销榜', 'parent_id': 4, 'icon': 'http://ov2eyt2uw.bkt.clouddn.com/other_categorys_ydw_man.png', 'style': 1},
        { 'cate_id': -407, 'cate_name': u'阅读王女生畅销榜', 'parent_id': 4, 'icon': 'http://ov2eyt2uw.bkt.clouddn.com/other_categorys_ydw_woman.png', 'style': 1},
    ]
    ret = []
    for i in data:
        if parent_id == i['parent_id']:
            ret.append(i)
    return ret

@category.route('/category_list')
def category_list():
    parent_id = request.args.get('parent_id', 0, int)
    if not parent_id:
        return json.dumps({'code': 1, 'msg': 'parent_id error. %s' %(parent_id)})
    if parent_id in (1,3):
        data = get_categorys(parent_id, 1000)
    else:
        data = get_other_categorys(parent_id, 1000)
    return json.dumps({'code': 0, 'data': data})

@category.route('/cate_index')
def cate_index():
    key = 'cate_index'
    redis_data = redis_utils.get_cache(key, refresh_expires=False)
    #redis_data = ''
    if redis_data:
        return json.dumps({'code':0, 'data': json.loads(redis_data)})
    data = [
        {'title': u'热门榜单', 'short_title': u'热门', 'parent_id': 4, 'icon': 'http://ov2eyt2uw.bkt.clouddn.com/cate_index_hot.png'},
        {'title': u'女生更爱', 'short_title': u'女生', 'parent_id': 3, 'icon': 'http://ov2eyt2uw.bkt.clouddn.com/cate_index_woman.png'},
        {'title': u'男生更爱', 'short_title': u'男生', 'parent_id': 1, 'icon': 'http://ov2eyt2uw.bkt.clouddn.com/cate_index_man.png'},
        #{'title': u'免费网络文学', 'short_title': u'免费', 'parent_id': 5, 'icon': 'http://ov2eyt2uw.bkt.clouddn.com/cate_index_free.png'},
        #{'title': u'漫画频道', 'short_title': u'漫画', 'parent_id': 6, 'icon': 'http://ov2eyt2uw.bkt.clouddn.com/cate_index_comic.png'},
    ]
    for i in data:
        if i['parent_id'] in [1, 3]: # 1 男生 3 女生
            i['cate_list'] = get_categorys(i['parent_id'], 1000)
        else:
            i['cate_list'] = get_other_categorys(i['parent_id'], 1000)

        for cate in i['cate_list']:
            cate['book_list'] = get_books_by_cate_id(cate['cate_id'], 1, 3)
    redis_utils.set_cache(key, json.dumps(data), 600)
    return json.dumps({'code': 0, 'data': data})

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

def get_books_by_cate_id(cate_id, page_no, num):
    if cate_id > 0:
        books = Book.query.filter_by(cate_id=cate_id, showed=True)

        if is_sup_free_book() and not is_sup_comic_book():
            books = books.filter_by(is_comic=0)
        elif not is_sup_free_book() and not is_sup_comic_book():
            books = books.filter_by(is_comic=0, free_collect=0)

        books = books.paginate(page_no, per_page=num, error_out=False)
        books = books.items
        return [ b.to_dict() for b in books ]
    else:
        #board = request.args.get('board', 0, int) # 1周榜 2月榜 3总榜 备用
        abs_cate_id = abs(cate_id)
        if abs_cate_id >= 400 and abs_cate_id <= 500:
            if page_no > 3:
                return []
            begin_count = (page_no - 1) * num
            ret = []
            with codecs.open('log/%s' %(abs_cate_id), 'r') as f:
                for book_name in f:
                    if len(ret) < num:
                        b = Book.query.filter(Book.book_name.like('%%%s%%' %(book_name.strip()))).first()
                        if b:
                            if begin_count:
                                begin_count -= 1
                            else:
                                ret.append(b.to_dict())
            return ret
        else:
            return []

@category.route('/get_book')
def get_book():
    ''' 根据类型获取书籍 '''
    cate_id = request.args.get('cate_id', 0, int)
    page_no = int(request.args.get("page_no", 1))
    num = int(request.args.get("num", 20))
    if not cate_id:
        return json.dumps({'code': 1, 'msg': 'cate_id error. %s' %(cate_id)})

    data = {
        'book_list': get_books_by_cate_id(cate_id, page_no, num),
        'cate_id': cate_id,
        'page_no': page_no,
        'num': num,
    }
    return json.dumps({'code': 0, 'data': data})



def is_sup_free_book():
    """是否是支持外链书籍的版本"""
    platform = request.args.get('platform')
    version = request.args.get('v', '')
    return True if (platform == 'android' and version >= '1.0.9' or platform == 'ios' and version >= '1.0.4') else False


def is_sup_comic_book():
    """是否是支持漫画的版本"""
    platform = request.args.get('platform')
    version = request.args.get('v', '')
    return True if (platform == 'android' and version >= '1.1.0' or platform == 'ios' and version >= '1.0.5') else False
