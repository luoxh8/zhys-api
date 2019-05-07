# coding=utf-8

from flask import Blueprint, request
from flask_login import login_required, current_user
from models import Book, BookCategory, BookVolume, BookChapters
from models import db
import json
from lib import utils

bp = Blueprint("book", __name__)

@bp.route('/get_book_info')
@login_required
def get_book_info():
    book_id = request.args.get('book_id', 0, int)
    if not book_id:
        return json.dumps({'code':1, 'msg':'book_id >0'})
    book = Book.query.filter_by(book_id=book_id).first()
    if not book:
        return json.dumps({'code':1, 'msg':'book is not exist.'})
    return json.dumps({'code':0, 'data': book.to_admin_dict()})

@bp.route('/update_book', methods=['POST'])
@login_required
def update_book():
    book_id = request.form.get('book_id', 0, int)
    if not book_id:
        return json.dumps({'code': 1, 'msg': 'book_id is not exist.'})
    book = Book.query.filter_by(book_id=book_id).with_lockmode('update').first()
    if not book:
        return json.dumps({'code': 1, 'msg': 'book is not exist.'})

    book_name = request.form.get('book_name', '')
    cate_id = request.form.get('cate_id', 0, int)
    channel_type = request.form.get('channel_type', -1, int)
    author_name = request.form.get('author_name', '')
    is_publish = request.form.get('is_publish', 0, int)
    status = request.form.get('status', 0, int)
    showed = request.form.get('showed', -1, int)
    ranking = request.form.get('ranking', -1, int)
    short_des = request.form.get('short_des', '')
    cover = request.form.get('cover', '')
    intro = request.form.get('intro', '')

    book.book_name = book_name if book_name else book.book_name
    book.cate_id = cate_id if cate_id else book.cate_id
    book.channel_type = channel_type if channel_type >= 0 and channel_type <= 2 else book.channel_type
    book.author_name = author_name if author_name else book.author_name
    book.is_publish = is_publish if is_publish in (1 ,2) else book.is_publish
    book.status = status if status in (1 ,2) else book.status
    book.showed = showed if showed in (0 ,1) else book.showed
    book.ranking = ranking if ranking >=0 else book.ranking
    book.short_des = short_des if short_des else book.short_des
    book.intro = intro if intro else book.intro

    if cover and 'http' in cover:
        book.cover = cover

    db.session.add(book)
    db.session.commit()
    return json.dumps({'code': 0, 'data': book.to_admin_dict()})




@bp.route('/list')
@login_required
def list():
    page_no = int(request.args.get("page_no", 1))
    num = int(request.args.get("num", 20))
    sql = 'select count(*) from book where 1=1 '
    if current_user.email in ['sina', 'kaixing', 'jingyu', 'zhangyue', 'anzhi', 'yangguang', 'riyue', 'yunyue', 'junengwan', 'lizhi', 'feilang', 'shenju', 'shidai', 'wanhuatong', 'iciyuan']:
        source = 'yangyue' if current_user.email == 'yangguang' else current_user.email
        sql += ' and source="%s" ' %(source)

        books = Book.query.filter_by(source=source).paginate(page_no, per_page=num, error_out=False).items
    else:
        books = Book.query.filter().paginate(page_no, per_page=num, error_out=False).items
    total = db.session.execute(sql).scalar() or 0
    book_list = [book.to_admin_dict() for book in books]
    return json.dumps({'code':0, 'data': book_list, 'total': total})


@bp.route('/search')
@login_required
def search():
    book_name = request.args.get('book_name', '')
    author_name = request.args.get('author_name', '')
    book_id = request.args.get('book_id', 0, int)
    channel_type = request.args.get('channel_type', 0, int)
    is_publish = request.args.get('is_publish', 0, int)
    status = request.args.get('status', 0, int)
    cate_id = request.args.get('cate_id', 0, int)
    source = request.args.get('source', '')

    page_no = request.args.get("page_no", 1, int)
    num = request.args.get("num", 20, int)
    query = Book.query
    total_sql = 'select count(*) from book where 1=1 '
    if book_name:
        query = query.filter(Book.book_name.like('%%%s%%' %(book_name)))
        total_sql += ' and book_name like "%%%s%%" ' %(book_name)
    if author_name:
        query = query.filter(Book.author_name.like('%%%s%%' %(author_name)))
        total_sql += ' and author_name like "%%%s%%" ' %(author_name)
    if book_id:
        query = query.filter_by(book_id=book_id)
        total_sql += ' and book_id=%s ' %(book_id)
    if channel_type:
        query = query.filter_by(channel_type=channel_type)
        total_sql += ' and channel_type=%s ' %(channel_type)
    if is_publish:
        query = query.filter_by(is_publish=is_publish)
        total_sql += ' and is_publish=%s ' %(is_publish)
    if status:
        query = query.filter_by(status=status)
        total_sql += ' and status=%s ' %(status)
    if cate_id:
        query = query.filter_by(cate_id=cate_id)
        total_sql += ' and cate_id=%s ' %(cate_id)
    if source:
        query = query.filter_by(source=source)
        total_sql += ' and source="%s" ' %(source)


    query = query.paginate(page_no, per_page=num, error_out=False)
    total = db.session.execute(total_sql).scalar() or 0
    data = [ book.to_admin_dict() for book in query.items ]
    return json.dumps({'code': 0, 'data': data, 'total': total})

@bp.route('/get_source_type')
@login_required
def get_source_type():
    data = [
        {'source_type': 'sina', 'source_type_name': u'新浪阅读'},
        {'source_type': 'kaixing', 'source_type_name': u'恺兴'},
        {'source_type': 'jingyu', 'source_type_name': u'鲸鱼'},
        {'source_type': 'zhangyue', 'source_type_name': u'掌阅'},
        {'source_type': 'anzhi', 'source_type_name': u'安之'},
        {'source_type': 'yangyue', 'source_type_name': u'阳光'},
        {'source_type': 'riyue', 'source_type_name': u'日月'},
        {'source_type': 'yunyue', 'source_type_name': u'云阅'},
        {'source_type': 'junengwan', 'source_type_name': u'剧能玩'},
        {'source_type': 'feilang', 'source_type_name': u'飞浪'},
        {'source_type': 'maimeng', 'source_type_name': u'麦萌'},
        {'source_type': 'lizhi', 'source_type_name': u'礼智'},
        {'source_type': 'shenju', 'source_type_name': u'神居动漫'},
        {'source_type': 'shidai', 'source_type_name': u'时代漫王'},
        {'source_type': 'huashen', 'source_type_name': u'画神'},
        {'source_type': 'kuman', 'source_type_name': u'酷漫网'},
        {'source_type': 'shenbeike', 'source_type_name': u'神北克'},
        {'source_type': 'wanhuatong', 'source_type_name': u'万画筒'},
        {'source_type': 'zhoumiao', 'source_type_name': u'周淼漫画'},
        {'source_type': 'iciyuan', 'source_type_name': u'iCiyuan 动漫'},
    ]
    return json.dumps({'code':0, 'data': data})

@bp.route('/chapter_list')
@login_required
def chapter_list():
    book_id = request.args.get('book_id', 0, int)
    page_no = int(request.args.get("page_no", 1))
    num = int(request.args.get("num", 20))

    if not book_id:
        return json.dumps({'code': -2, 'msg': u'参数错误'})
    book = Book.query.filter_by(book_id=book_id).first()
    if not book:
        return json.dumps({'code': -1, 'msg': u'无此书籍信息'})
    book_volume = BookVolume.query.filter_by(book_id=book_id).first()
    if book_volume:
        sql = 'select count(*) from book_chapters where book_id=%s and volume_id=%s' %(book_id, book_volume.volume_id)
        book_chapters = BookChapters.query.filter_by(book_id=book_id, volume_id=book_volume.volume_id).paginate(page_no, per_page=num, error_out=False).items
    else:
        sql = 'select count(*) from book_chapters where book_id=%s' %(book_id)
        book_chapters = BookChapters.query.filter_by(book_id=book_id).paginate(page_no, per_page=num, error_out=False).items
    chapters = [ chapter.to_admin_dict() for chapter in book_chapters ]
    total = db.session.execute(sql).scalar() or 0
    return json.dumps({'code':0, 'data': chapters, 'total': total})

@bp.route('/update_chapter_money', methods=['POST', 'GET'])
@login_required
def update_chapter_money():
    _id = request.form.get('id', 0, int) or request.args.get('id', 0, int)
    money = request.form.get('money', 0, int) or request.args.get('money', 0, int) 
    if _id:
        chapter = BookChapters.query.filter_by(id=_id).first()
        if chapter:
            chapter.money = money
            db.session.add(chapter)
            db.session.commit()
            return json.dumps({'code': 0, 'data': chapter.to_admin_dict()})
        else:
            return json.dumps({'code': 1, 'msg': 'chapter is not exist.'})
    else:
        return json.dumps({'code': 1, 'msg': 'id is null.'})

@bp.route('/update_book_chapter_money', methods=['POST', 'GET'])
@login_required
def update_book_chapter_money():
    money = request.form.get('money', 0, int) or request.args.get('money', 0, int) 
    book_id = request.form.get('book_id', 0, int) or request.args.get('book_id', 0, int)
    if not book_id:
        return json.dumps({'code': -2, 'msg': u'参数错误'})
    book = Book.query.filter_by(book_id=book_id).first()
    if not book:
        return json.dumps({'code': -1, 'msg': u'无此书籍信息'})
    book_volume = BookVolume.query.filter_by(book_id=book_id).first()
    if book_volume:
        sql = 'update book_chapters set money=%s where book_id=%s and volume_id=%s' %(money, book_id, book_volume.volume_id)
    else:
        sql = 'update book_chapters set money=%s where book_id=%s' %(money, book_id)
    db.session.execute(sql)
    db.session.commit()
    return json.dumps({'code':0, 'msg': 'ok.'})

@bp.route('/category_list')
@login_required
def category_list():
    page_no = request.args.get("page_no", 1, int)
    num = request.args.get("num", 20, int)
    showed = request.args.get('showed', 0, int)

    sql = 'select count(*) from book_category where 1=1 '
    query = BookCategory.query
    if showed:
        sql += ' and showed=1 '
        query = query.filter_by(showed=1)

    total = db.session.execute(sql).scalar() or 0

    book_categorys = query.paginate(page_no, per_page=num, error_out=False).items
    book_categorys_list = [book_category.to_admin_dict() for book_category in book_categorys]
    return json.dumps({'code':0, 'data': book_categorys_list, 'total': total})

@bp.route('/update_category', methods=['POST', 'GET'])
@login_required
def update_category():
    cate_id = request.form.get('cate_id', 0, int) or request.args.get('cate_id', 0, int)
    icon = request.form.get('icon', '') or request.args.get('icon', '')
    book_cate = BookCategory.query.filter_by(cate_id=cate_id).first()
    if book_cate:
        book_cate.icon = icon
        db.session.add(book_cate)
        db.session.commit()
        return json.dumps({'code': 0, 'data': book_cate.to_admin_dict()})
    else:
        return json.dumps({'code': 1, 'msg': '%s category is not exist.' %(cate_id)})
