# coding: utf-8
from dateutil.tz.tz import tzlocal
import ujson as json
from flask import Blueprint, request, current_app
from flask_login import login_user, logout_user, current_user, login_required
from lib import sina, redis_utils
from sqlalchemy.sql import or_

from lib.buy import get_word_money
from lib.ios_special import is_ios_special
from models.book import *
from models.other import *
from models.bookshelf import *
from models.other import *
import datetime
import random
import requests
import arrow

book = Blueprint('book', __name__)

HOT_TYPE = 'hot'
NEW_TYPE = 'new'
MYSELF_TYPE = 'myself'
REC_TYPE = 'recommend'
FINISH_TYPE = 'finish'
COMIC_TYPE = 'comic'
PAY_NUM = 20

@book.route('/book_list')
def book_list():
    ret = sina.get_book_list()
    return ret


def get_banner(m_id, sex, platform):
    banner_list = []
    banners = Banner.query.order_by(Banner.level.desc()).filter(or_(Banner.sex==sex, Banner.sex==0), or_(Banner.platform==platform, Banner.platform=='all'), Banner.showed==1).all()
    for banner in banners:
        banner_list.append(banner.to_dict())

    return banner_list

def v2_get_banner(channel_code, platform):
    channel_data = ChannelData.query.filter_by(class_name='banner', channel_code=channel_code).all()
    ids = [ i.class_id for i in channel_data ]
    banners = Banner.query.filter(or_(Banner.platform==platform, Banner.platform=='all'), Banner.showed==1)
    banners = banners.filter(Banner.id.in_(ids))
    banners = banners.order_by(Banner.level.desc()).all()
    return [ b.to_dict() for b in banners ]


def get_hot_type():
    hot_list = [
        {
            "title": "",
            "url": "",
            "icon_url": ""
        },
        {
            "title": "",
            "url": "",
            "icon_url": ""
        },
        {
            "title": "",
            "url": "",
            "icon_url": ""
        },
        {
            "title": "",
            "url": "",
            "icon_url": ""
        },
        {
            "title": "",
            "url": "",
            "icon_url": ""
        },
        {
            "title": "",
            "url": "",
            "icon_url": ""
        },
    ]
    return hot_list

def v2_get_top_list(channel_code, v):
    channel_data = ChannelData.query.filter_by(class_name='topic', channel_code=channel_code).order_by(ChannelData.ranking.desc()).all()
    data = [ i.to_admin_dict()['class_data'] for i in channel_data ]
    data = [ i for i in data if i ]
    return data

def get_top_list(v):
    top_list = [
        {
            "title": u"签到",
            "url": u"https://pages.kdyoushu.com/check_in.html",
            "icon_url": "http://ov2eyt2uw.bkt.clouddn.com/sign_book.png",
            "activity": "",
            "params": {},
            "ios_activity": ""
        },
        {
            "title": u"充值",
            "url": u"",
            "icon_url": "http://ov2eyt2uw.bkt.clouddn.com/chongzhi.png",
            "activity": "RechargeActivity",
            "params": {},
            "ios_activity": "ReachareViewController"
        },
    ]
    shujia = {
            "title": u"书架",
            "url": u"",
            "icon_url": "http://ov2eyt2uw.bkt.clouddn.com/bookshelf.png",
            "activity": "index_1",
            "params": {},
            "ios_activity": "BookShelfViewController"
        }
    ranking = {
            "title": u"排行榜",
            "url": u"",
            "icon_url": "http://ov2eyt2uw.bkt.clouddn.com/bangdan.png",
            "activity": "TopListActivity",
            "params": {},
            "ios_activity": "RankingListViewController"
        }
    free_book = {
            "title": u"免费",
            "url": u"",
            "icon_url": "http://ov2eyt2uw.bkt.clouddn.com/mian_icon1030.png",
            "activity": "FreeBooksActivity",
            "params": {},
            "ios_activity": "FreeBookAreaViewController"
        
    }
    comic_book = {
            "title": u"漫画",
            "url": u"",
            "icon_url": "http://ov2eyt2uw.bkt.clouddn.com/manhuaicon.png",
            "activity": "SearchResultForAuthorActivity",
            "params": {'type': 6, 'params': u'漫画专区', 'name': COMIC_TYPE},
            "ios_activity": "CateResultViewController"
    }
    platform = request.args.get('platform', '')
    if v == '1.0.1':
        top_list.append(ranking)
    else:
        if platform == 'ios' and v >= '1.0.5':
            top_list.append(free_book)
        else:
            pass
    if platform == 'android' and v >= '1.0.9':
        top_list.append(free_book)
    if platform == 'android' and v >= '1.1.0':
        top_list.append(comic_book)
    if platform == 'ios' and v >= '1.0.6':
        comic_book['params']['name'] = COMIC_TYPE
        top_list.append(comic_book)
    if v == '9.9.9':
        top_list.append(shujia)
        top_list.append(ranking)
        top_list.append(free_book)
        top_list.append(comic_book)
    return top_list


def get_book_first_pay_chapter_id(book_id):
    ''' 返回开始付费章节ID '''
    key = "book_first_pay_chapter_id_%s" % book_id
    redis_data = redis_utils.get_cache(key, refresh_expires=False)
    if redis_data:
        return redis_data

    # 检测是否漫画
    is_comic = False
    book = Book.query.filter_by(book_id=book_id).first()
    if book and book.is_comic:
        is_comic = True

    if is_comic:
        chapter = BookChapters.query.filter(BookChapters.book_id == book_id, BookChapters.money != 0) \
            .order_by(BookChapters.chapter_id.asc()).first()
        if not chapter:
            return 999999
        pay_num = int(chapter.chapter_id)
    else:
        chapter = BookChapters.query.order_by(BookChapters.chapter_id.asc()).filter(BookChapters.book_id==book_id)[PAY_NUM:PAY_NUM+1]
        if not chapter:
            return 0
        pay_num = int(chapter[0].chapter_id)
    redis_utils.set_cache(key, pay_num, 86400)
    return pay_num

def get_comic_images(format_string):
    """处理格式化字符串，获取漫画正文内容"""
    return ['%s-app.image' % item for item in format_string.split('|')]

def v2_get_book_shelf_data(channel_code):
    cd = ChannelData.query.filter_by(class_name='book_shelf_name', channel_code=channel_code).order_by(ChannelData.ranking.desc()).all()
    book_shelf_names = []
    for i in cd:
        bsn = BookShelfName.query.filter_by(id=i.class_id).first()
        if bsn:
            book_shelf_names.append(bsn)

    book_shelf_data = []
    style = 1
    num = 1
    for book_shelf_name in book_shelf_names:
        if book_shelf_name.name in ('myself', 'recommend'):
            continue
        t_data = book_shelf_name.to_dict()
        t_data['style'] = style

        # 1横(6本) 2竖(3本)
        num = 6 if style == 1 else 3
        # 横竖交替
        style = 2 if style == 1 else 1

        query = BookShelf.query.filter_by(name=book_shelf_name.name, showed=True)
        book_shelfs = query.order_by(BookShelf.ranking.desc(), BookShelf.updated.desc())[:num]

        books = []
        for b in book_shelfs:
            book = Book.query.filter_by(book_id=b.book_id).first()
            if book:
                books.append(book.to_dict())

        if books:
            t_data['books'] = books
            t_data['params']['channel_code'] = channel_code
            t_data['params']['title'] = get_channel_type_title(channel_code)
            book_shelf_data.append(t_data)
    return book_shelf_data


@book.route('/v2/index')
def v2_index():
    channel_code = request.args.get('channel_code', 0, int)
    if not channel_code:
        return  json.dumps({'code':1, 'msg': 'channel_code is not exist.'})
    
    platform = request.args.get('platform')
    v = request.args.get('v')
    m_id = request.args.get('m_id', 0, int)
    key = 'v2_index_%s_%s_%s_%s' % (platform, v, m_id, channel_code)

    redis_data = redis_utils.get_cache(key, refresh_expires=False)
    #redis_data = ''
    if redis_data:
        return json.dumps({'code':0, 'data': json.loads(redis_data)})

    data = dict(
        banner_list = v2_get_banner(channel_code, platform),
        top_list = v2_get_top_list(channel_code, v),
        book_shelf_data = v2_get_book_shelf_data(channel_code)
    )

    redis_utils.set_cache(key, json.dumps(data), 86400)
    return json.dumps({'code': 0, 'data': data})

def get_channel_type_title(channel_code):
    ct = ChannelType.query.filter_by(id=channel_code).first()
    return ct.name if ct else 'unknow'
    


@book.route('/index')
def index():
    ''' 首页 '''
    platform = request.args.get('platform')
    v = request.args.get('v')
    sex = request.args.get('sex', 0)
    m_id = request.args.get('m_id', 0, int)
    key = 'index_%s_%s_%s_%s' % (platform, sex, v, m_id)
    
    redis_data = redis_utils.get_cache(key, refresh_expires=False)
    #redis_data = ""
    if redis_data:
        data = json.loads(redis_data)
        if is_ios_special():
            data['top_list'] = data['top_list'][:-1]
        return json.dumps({'code':0, 'data': data})
    data = {}
    if v == '1.0.0':
        hot_list = BookShelf.query.order_by(BookShelf.ranking.desc()).filter(BookShelf.name==HOT_TYPE, BookShelf.showed == True, or_(BookShelf.sex==sex, BookShelf.sex==0))[:3]
    else:
        if not m_id:
            hot_list = BookShelf.query.order_by(BookShelf.ranking.desc()).filter(BookShelf.name==HOT_TYPE, BookShelf.showed == True, or_(BookShelf.sex==sex, BookShelf.sex==0))[:6]
        else:
            hot_list = BookShelf.query.filter(BookShelf.name==HOT_TYPE, BookShelf.showed == True, or_(BookShelf.sex==sex, BookShelf.sex==0))[:9]

    hot_data = []
    for hot in hot_list:
        book = Book.query.filter_by(book_id=hot.book_id).first()
        if book.showed:
            hot_data.append(book.to_dict())
    data['hot_data'] = hot_data
    
    if v == '1.0.0':
        new_list = BookShelf.query.order_by(BookShelf.ranking.desc()).filter(BookShelf.name==NEW_TYPE, BookShelf.showed == True,or_(BookShelf.sex==sex, BookShelf.sex==0))[:3]
    else:
        if not m_id:
            new_list = BookShelf.query.order_by(BookShelf.ranking.desc()).filter(BookShelf.name==NEW_TYPE, BookShelf.showed == True,or_(BookShelf.sex==sex, BookShelf.sex==0))[:6]
        else:
            new_list = BookShelf.query.filter(BookShelf.name==NEW_TYPE, BookShelf.showed == True,or_(BookShelf.sex==sex, BookShelf.sex==0))[:3]

    new_data = []
    for new in new_list:
        book = Book.query.filter_by(book_id=new.book_id).first()
        if book.showed:
            new_data.append(book.to_dict())
    
    if not m_id:
        finish_list = BookShelf.query.order_by(BookShelf.ranking.desc()).filter(BookShelf.name==FINISH_TYPE, BookShelf.showed == True,or_(BookShelf.sex==sex, BookShelf.sex==0))[:6]
    else:
        finish_list = BookShelf.query.filter(BookShelf.name==FINISH_TYPE, BookShelf.showed == True,or_(BookShelf.sex==sex, BookShelf.sex==0))[:3]

    finish_data = []
    for finish in finish_list:
        book = Book.query.filter_by(book_id=finish.book_id).first()
        if book.showed:
            finish_data.append(book.to_dict())
    
    free_data = []
    free_list = Book.query.filter(Book.showed == True, Book.free_collect == True, or_(Book.channel_type==sex, Book.channel_type==0))[:6]
    for free in free_list:
        free_data.append(free.to_dict())
    
    #漫画
    comic_data = []
    comic_list = Book.query.filter(Book.showed == True, Book.is_comic == True, or_(Book.channel_type==sex, Book.channel_type==0))[:6]
    for comic in comic_list:
        comic_data.append(comic.to_dict())

    data['finish_data'] = finish_data
    data['new_data'] = new_data
    data['banner_list'] = get_banner(m_id, sex, platform)
    data['hot_type'] = get_hot_type()
    data['top_list'] = get_top_list(v)
    data['free_data'] = free_data
    data['comic_data'] = comic_data
    redis_utils.set_cache(key, json.dumps(data), 180)
    if is_ios_special():
        data['top_list'] = data['top_list'][:-1]
    return json.dumps({'code': 0, 'data': data})


@book.route('/detail')
def detail():
    ''' 获取书籍详情 '''
    book_id = request.args.get('book_id', 0, int)
    if not book_id:
        return json.dumps({'code': -2, 'msg': u'参数错误'})
    is_sup_free = is_sup_free_book()
    is_sup_comic = is_sup_comic_book()

    key = 'detail_%s' % book_id
    if is_sup_free and not is_sup_comic:
        key = 'nofreedetail_%s' % book_id
    elif not is_sup_comic and not is_sup_free:
        key = 'nocomicdetail_%s' % book_id
    else:
        pass
    redis_data = redis_utils.get_cache(key, refresh_expires=False)
    #redis_data = ""
    if redis_data:
        data = json.loads(redis_data)
        if current_user.is_authenticated:
            collect = BookShelf.query.filter_by(name=MYSELF_TYPE, user_id=current_user.id, book_id=book_id).count()
            if collect == 1:
                data['is_myself'] = 1
            else:
                data['is_myself'] = 0
        return json.dumps({'code': 0, 'data': data})

    book = Book.query.filter_by(book_id=book_id).first()
    if not book:
        return json.dumps({'code': -1, 'msg': u'无此书籍信息'})
    book_volume = BookVolume.query.filter_by(book_id=book_id).first()
    if book_volume:
        book_chapters = BookChapters.query.filter_by(book_id=book_id, volume_id=book_volume.volume_id)[:20]
    else:
        book_chapters = BookChapters.query.filter_by(book_id=book_id)[:20]
    #获取分类
    category = BookCategory.query.filter_by(cate_id=book.cate_id).first()
    like_key = 'like_book_%s' % book.cate_id
    if is_sup_free and not is_sup_comic:
        like_key = 'nofreelike_book_%s' % book.cate_id
    elif not is_sup_comic and not is_sup_free:
        like_key = 'nocomiclike_book_%s' % book.cate_id
    else:
        pass
    like_book = redis_utils.get_cache(like_key, refresh_expires=False)
    #like_book_list = []
    if like_book:
        like_book_list = json.loads(like_book)
    else:
        like_book_list = []
        query = Book.query.filter_by(cate_id=book.cate_id, showed=1)
        
        if is_sup_free and not is_sup_comic:
            query = query.filter_by(is_comic=0)
        elif not is_sup_free and not is_sup_free:
            query = query.filter_by(free_collect=0, is_comic=0)
        else:
            pass
        if query.count()<6:
            like_book_query = query.all()
        else:
            count = random.randint(1, query.count())
            count =  count if count >= 6 else 7
            like_book_query = query[count-6:count]
        for l in like_book_query:
            like_book_list.append(l.to_dict())
        redis_utils.set_cache(like_key, json.dumps(like_book_list), 180)    
    chapter_list = []
    for chapter in book_chapters:
        chapter_list.append(chapter.to_dict())
    book_dict = book.to_dict()

    # 外链小说
    free_source = request.args.get('free_source', '')
    if book.free_collect:
        source_item = get_free_source(book_id, free_source)
        if not source_item:
            return json.dumps({'code': -1, 'msg': u'无此书籍信息'})

        book_dict.update(source_item.to_dict())

    book_dict['cate_name'] = category.cate_name
    if not book_dict.get('chapter_num'):
        book_dict['chapter_num'] = BookChapters.query.filter_by(book_id=book_id).count()
    data = {
        'book_detail':book_dict,
        'book_chapters': chapter_list,
        'like_book_list': like_book_list
    }
    redis_utils.set_cache(key, json.dumps(data), 1800)
    if current_user.is_authenticated:
        collect = BookShelf.query.filter_by(name=MYSELF_TYPE, user_id=current_user.id, book_id=book_id).count()
        if collect == 1:
            data['is_myself'] = 1
        else:
            data['is_myself'] = 0
    return json.dumps({'code': 0, 'data': data})


def get_free_source(book_id, free_source):
    if not free_source:  # 默认取最新的源
        source_item = FreeBook.query.filter_by(book_id=book_id).order_by(FreeBook.update_time.desc()).first()
    else:
        source_item = FreeBook.query.filter_by(book_id=book_id, free_source=free_source).first()
    return source_item


@book.route('/add_bookcase')
@login_required
def add_bookcase():
    ''' 添加书架 '''
    book_id = request.args.get('book_id')
    book_id_list = book_id.split("|")
    s = request.args.get('s')
    platform = request.args.get('platform')
    book_status_list = []
    for book_id in book_id_list:
        collect = BookShelf.query.filter_by(name=MYSELF_TYPE, user_id=current_user.id, book_id=book_id).count()
        if collect == 1:
            pass
        else:
            #book_shelf = BookShelf(book_id=book_id, name=MYSELF_TYPE, user_id=current_user.id)
            book_shelf = BookShelf(book_id, MYSELF_TYPE, current_user.id, 0, 0, True, 0)
            db.session.add(book_shelf)
    try:
        db.session.commit()
    except:
        return json.dumps({'code': -1, 'msg': u'网络错误'})
    for book_id in book_id_list:
        try:
            requests.get('%s/book/book_collect?book_id=%s&user_id=%s&type=%s&platform=%s&s=%s'%
                (current_app.config['STATS_URL'], book_id, current_user.id, 'bookshelf', platform, s))
        except:
            pass
    return json.dumps({'code': 0, 'data': {}})


@book.route('/myself_bookcase')
def myself_bookcase():
    ''' 获取当前用户书架信息 '''
    sex = request.args.get('sex', 0, int)
    v = request.args.get('v')
    collect_list = []
    if current_user.is_authenticated:
        book_shels = BookShelf.query.order_by(BookShelf.updated.desc()).filter(BookShelf.name==MYSELF_TYPE, BookShelf.user_id==current_user.id).all()
        for collect in book_shels:
            book = Book.query.filter_by(book_id=collect.book_id).first()
            if  book:
                book_dict = book.to_dict()
                book_dict["rate"] = collect.rate
                collect_list.append(book.to_dict())
    else:
        book_shels = BookShelf.query.filter(BookShelf.name==REC_TYPE, BookShelf.showed == True,or_(BookShelf.sex==sex, BookShelf.sex==0))[:5]
        for collect in book_shels:
            book = Book.query.filter_by(book_id=collect.book_id).first()
            book_dict = book.to_dict()
            book_dict["rate"] = collect.rate
            collect_list.append(book.to_dict())
        if v == '1.0.0':
            collect_list = []
    return json.dumps({'code': 0, 'data': collect_list})


def is_sup_free_book():
    """是否是支持外链书籍的版本"""
    platform = request.args.get('platform')
    version = request.args.get('v', '')
    return True if (platform == 'android' and version >= '1.0.9' or platform == 'ios' and version >= '1.0.4') else False


def is_sup_comic_book():
    """是否是支持漫画的版本"""
    platform = request.args.get('platform')
    version = request.args.get('v', '')
    return True if (platform == 'android' and version >= '1.1.0' or platform == 'ios' and version >= '1.0.6') else False

@book.route('/find_book')
def find_book():
    ''' 查找书籍 '''
    params = request.args.get('params', '')
    page_no = int(request.args.get("page_no", 1))
    num = int(request.args.get("num", 20))

    if not params:
        return json.dumps({'code': -1, 'msg': u'请输入查找关键字'})

    pagination = Book.query.filter(or_(Book.book_name.like('%'+params+'%'),
        Book.author_name.like('%'+params+'%')), Book.showed == True)
    if not is_sup_free_book() and not is_sup_comic_book():
        print 11111111
        pagination = pagination.filter(Book.free_collect==0, Book.is_comic==0)
    elif is_sup_free_book and not is_sup_comic_book():
        print 22222
        pagination = pagination.filter( Book.is_comic==0)
    else:
        pass
    pagination = pagination.paginate(page_no, per_page=num, error_out=False)
    books = pagination.items
    book_list = []
    for book in books:
        book_dict = book.to_dict()
        category = BookCategory.query.filter_by(cate_id=book.cate_id).first()
        book_dict['cate_name'] = category.cate_name
        book_list.append(book_dict)
    data = {
        'book_list': book_list,
        'params': params,
        'page_no': page_no,
        'num': num
    }
    # 热搜统计
    current_app.redis.zincrby('hot_search', params)
    return json.dumps({'code': 0, 'data': data})


@book.route('/hot_search')
def hot_search():
    """热搜关键词"""
    #data = current_app.redis.zrevrange('hot_search', 0, 9) or []
    data = ['圣墟', '护花天王', '龙王传说', '大帝姬', '斗破苍穹', '永夜君王', '极品小医师', '暖妻成瘾', '恋恋娇妻太腹黑', '慕南枝']
    return json.dumps({'code': 0, 'data': data})


@book.route('/book_associate')
def book_associate():
    ''' 书籍查询联想 '''
    params = request.args.get('params', '')
    if not params:
        return json.dumps({'code': -1, 'msg': u'请输入搜索条件'})
    book_name_list = []
    author_name_list = []

    key = 'book_associate_%s' % params
    if not is_sup_free_book() and not is_sup_comic_book():
        key = 'nocomicbook_associate_%s' % params
    elif is_sup_free_book() and not is_sup_comic_book():
        key = 'nofreebook_associate_%s' % params
    else:
        pass
    redis_data = redis_utils.get_cache(key, refresh_expires=False)
    if redis_data:
        return json.dumps({'code': 0, 'data': json.loads(redis_data)})

    if is_sup_free_book() and not is_sup_comic_book():
        book_names = Book.query.filter(Book.book_name.like('%'+params+'%'), Book.showed == True, Book.is_comic == 0).limit(5)
        author_names = Book.query.filter(Book.author_name.like('%'+params+'%'), Book.showed == True, Book.is_comic == 0).limit(5)
    elif is_sup_free_book() and is_sup_comic_book():
        book_names = Book.query.filter(Book.book_name.like('%'+params+'%'), Book.showed == True).limit(5)
        author_names = Book.query.filter(Book.author_name.like('%'+params+'%'), Book.showed == True).limit(5)
        
    else:
        book_names = Book.query.filter(Book.book_name.like('%'+params+'%'), Book.showed == True, Book.free_collect==0, Book.is_comic == 0).limit(5)
        author_names = Book.query.filter(Book.author_name.like('%'+params+'%'), Book.showed == True, Book.free_collect==0, Book.is_comic == 0).limit(5)
    for book_name in book_names:
        names = {
            'book_name': book_name.book_name,
            'book_id': book_name.book_id,
        }
        book_name_list.append(names)
    for author_name in author_names:
        names = {
            'author_name': author_name.author_name,
            'book_id': author_name.book_id,
        }
        author_name_list.append(names)
    data = {
        'book_name_list': book_name_list,
        'author_name_list': author_name_list
    }
    redis_utils.set_cache(key, json.dumps(data), 86400)
    return json.dumps({'code': 0, 'data': data})


@book.route('/get_content')
def get_content():
    ''' 获取书籍内容 '''
    book_id = request.args.get('book_id')
    volume_id = request.args.get('volume_id')
    chapter_id = request.args.get('chapter_id')

    chapter = BookChapters.query.filter_by(book_id=book_id).first()
    if not chapter:
        return json.dumps({'code': -1, 'msg': u'没有此章节信息'})
    if int(chapter_id) >= int(get_book_first_pay_chapter_id(book_id)):
        if current_user.is_authenticated:
            purchase_book =  PurchasedBook.query.filter_by(book_id=book_id, user_id=current_user.id).first()
            
            if not purchase_book:
                return json.dumps({'code': -2, 'msg': u'请购买后阅读'})
            elif not json.loads(purchase_book.buy_info):
                return json.dumps({'code': -2, 'msg': u'请购买后阅读'})
            elif not json.loads(purchase_book.buy_info).get(str(int(volume_id))):
                return json.dumps({'code': -2, 'msg': u'请购买后阅读'})
            elif int(chapter_id) not in json.loads(purchase_book.buy_info).get(str(int(volume_id))):
                return json.dumps({'code': -2, 'msg': u'请购买后阅读'})
            else:
                pass



#if not purchase_book or not json.loads(purchase_book.buy_info) or int(chapter_id) not in json.loads(purchase_book.buy_info)[volume_id]:
#                return json.dumps({'code': -2, 'msg': u'请购买后阅读'})
        else:
            return json.dumps({'code': -2, 'msg': u'请登录后阅读'})

    data = {
        'book_id': -1,
        'volume_id': -1,
        'chapter_id': -1,
        'content': '', #content.content.replace(u'　', '').replace(' ', '')
    }
    # 判断是否漫画类型
    book = Book.query.filter_by(book_id=book_id).first()
    if book and book.is_comic:
        item = BookChapters.query.filter_by(book_id=book_id, volume_id=volume_id, chapter_id=chapter_id).first()
        if not item:
            return json.dumps({'code': -1, 'msg': u'没有此章节信息'})

        data['book_id'] = item.book_id
        data['volume_id'] = item.volume_id
        data['chapter_id'] = item.chapter_id
        data['content'] = get_comic_images(item.content_url)
    else:
        content = BookChapterContent.query.filter_by(book_id=book_id, volume_id=volume_id, chapter_id=chapter_id).first()
        if not content:
            return json.dumps({'code': -1, 'msg': u'没有此章节信息'})

        data['book_id'] = content.book_id
        data['volume_id'] = content.volume_id
        data['chapter_id'] = content.chapter_id
        data['content'] = content.content.replace(u'　', '').replace(' ', '')

    return json.dumps({'code': 0, 'data': data})


@book.route('/get_content/multi', methods=['POST'])
@login_required
def get_content_multi():
    """批量下载章节"""
    accept_encoding = request.headers.get('Accept-Encoding', '')
    if 'gzip' not in accept_encoding.lower():
        return json.dumps({"code": -1, "msg": "只允许压缩传输"})

    book_id = request.form.get('book_id', 0, int)
    if not book_id:
        return json.dumps({"code": -1, "msg": "参数错误"})
    volume_chapter = request.form.get('volume_chapter')
    volume_chapter_dict = {}
    
    for x in [v.split(',') for v in volume_chapter.split('|')]:
        volume_chapter_dict.setdefault(int(x[0]), []).append(int(x[1]))

    purchased = PurchasedBook.query.filter_by(user_id=current_user.id, book_id=book_id).first()
    buy_info = {}
    if purchased:
        buy_info = json.loads(purchased.buy_info)

    first_pay_chapter_id = get_book_first_pay_chapter_id(book_id)
    for volume_id, chapter_ids in volume_chapter_dict.iteritems():
        buy_chapters = buy_info.get(str(volume_id), [])
        for chapter_id in chapter_ids:
            if chapter_id >= first_pay_chapter_id:
                if chapter_id not in buy_chapters:
                    return json.dumps({'code': -2, 'msg': u'请购买后阅读'})

    is_comic = False
    book = Book.query.filter_by(book_id=book_id).first()
    if book and book.is_comic:
        is_comic = True

    data = []
    for volume_id, chapter_ids in volume_chapter_dict.iteritems():
        if is_comic:
            chapters = BookChapters.query.filter(
                BookChapters.book_id == book_id,
                BookChapters.volume_id == volume_id,
                BookChapters.chapter_id.in_(chapter_ids)
            ).all()
            for chapter in chapters:
                data.append({
                    'volume_id': chapter.volume_id,
                    'chapter_id': chapter.chapter_id,
                    'content': get_comic_images(chapter.content_url),
                    'chapter_name': chapter.chapter_name,
                })
        else:
            contents = BookChapterContent.query.filter(
                BookChapterContent.book_id==book_id,
                BookChapterContent.volume_id==volume_id,
                BookChapterContent.chapter_id.in_(chapter_ids)).all()
            for content in contents:
                ch = BookChapters.query.filter_by(chapter_id=content.chapter_id).first()
                data.append({
                    'volume_id': content.volume_id,
                    'chapter_id': content.chapter_id,
                    'content': content.content.replace(u'　', '').replace(' ', ''),
                    'chapter_name': ch.chapter_name
                })
    if len(data) < len(volume_chapter.split('|')):
        return json.dumps({'code': -1, 'msg': u'章节不存在'})
    return json.dumps({'code': 0, 'data': data})


@book.route('/find_chapters')
def find_chapters():
    ''' 查询图书章节 '''
    book_id = request.args.get('book_id')
    page_no = request.args.get("page_no", 1, int)
    num = request.args.get("num", 20, int)
    free_source = request.args.get('free_source', '')
    chapter_list = []
    if not num:
        num = 20

    # 检测是否漫画
    is_comic = False
    book = Book.query.filter_by(book_id=book_id).first()
    if book and book.is_comic:
        is_comic = True

    source_item = get_free_source(book_id, free_source)
    if source_item:
        free_source = source_item.free_source
    book_chapter = BookChapters.query.order_by(BookChapters.chapter_id.asc()).filter(
        BookChapters.book_id==book_id, BookChapters.free_source==free_source)[(page_no-1)*num:page_no*num]
    #pagination = BookChapters.query.filter_by(book_id=book_id).paginate(page_no, per_page=num, error_out=False)
    #book_chapter = pagination.items
    #如果购买直接查询购买记录
    if current_user.is_authenticated:
        purchase_book =  PurchasedBook.query.filter_by(book_id=book_id, user_id=current_user.id).first()

    # 取卷名
    v_ids = [c.volume_id for c in book_chapter if c.volume_id > 0]
    volume_list = BookVolume.query.filter(BookVolume.book_id==book_id,
                                          BookVolume.volume_id.in_(v_ids)).all()
    volume_list = {v.volume_id: v.volume_name for v in volume_list}
    book_num = int(get_book_first_pay_chapter_id(book_id))
    for chapter in book_chapter:
        chapter_dict = chapter.to_dict()
        if source_item:
            chapter_dict['pay_type'] = 1    
        elif chapter.chapter_id >= book_num:
            if current_user.is_authenticated:
                if not purchase_book:
                    chapter_dict['pay_type'] = 0
                elif not json.loads(purchase_book.buy_info):
                    chapter_dict['pay_type'] = 0
                elif not json.loads(purchase_book.buy_info).get(str(int(chapter.volume_id))):
                    chapter_dict['pay_type'] = 0
                elif int(chapter.chapter_id) not in json.loads(purchase_book.buy_info).get(str(int(chapter.volume_id))):
                    chapter_dict['pay_type'] = 0
                else:
                    chapter_dict['pay_type'] = 1#1已购买

                #if not purchase_book or not json.loads(purchase_book.buy_info) or int(chapter.chapter_id) not in json.loads(purchase_book.buy_info)[str(int(chapter.volume_id))]:
                #    chapter_dict['pay_type'] = 0
                #else:
                #    chapter_dict['pay_type'] = 1#1已购买
            else:
                chapter_dict['pay_type'] = 0#0未购买
        else:
            chapter_dict['pay_type'] = 1#1已购买
        chapter_dict['volume_name'] = volume_list.get(chapter.volume_id, '')
        chapter_dict['cost_money'] = 0
        if not chapter_dict['pay_type']:
            if is_comic:
                chapter_dict['content_url'] = ''
                chapter_dict['cost_money'] = chapter.money
            else:
                chapter_dict['cost_money'] = get_word_money(chapter.word_count)
        chapter_list.append(chapter_dict)
    data = {
        'chapter_list': chapter_list,
        'free_collect': 0,
        'is_comic': 1 if is_comic else 0,
    }
    if source_item:
        data['free_source'] = source_item.free_source
        data['parse_rule'] = source_item.get_parse_rule()[1]
        data['free_collect'] = 1

    return json.dumps({'code': 0, 'data': data})


@book.route('/manage_book_mark')
@login_required
def manage_book_mark():
    ''' 管理书签（增加和删除） '''
    book_id = request.args.get('book_id', 0)
    volume_id = request.args.get('volume_id', 0)
    chapter_id = request.args.get('chapter_id', 0)
    params = request.args.get('params', '')
    is_de = request.args.get('is_de', 0, int)
    book_mark = BookMark.query.filter_by(user_id=current_user.id, book_id=book_id, volume_id=volume_id, chapter_id=chapter_id).first()
    if is_de:
        if not book_mark:
            return json.dumps({'code': -1, 'msg': u''})
        db.session.delete(book_mark)
        db.session.commit()
    else:
        if book_mark:
            return json.dumps({'code': -1, 'msg': u''})
        mark = BookMark(user_id=current_user.id, book_id=book_id, volume_id=volume_id, chapter_id=chapter_id, params=params)
        db.session.add(mark)
        db.session.commit()
    return json.dumps({'code': 0, 'data': {}})


@book.route('/find_book_mark')
@login_required
def find_book_mark():
    ''' 查找书签 '''
    book_id = request.args.get('book_id', 0)
    book_marks = BookMark.query.filter_by(user_id=current_user.id, book_id=book_id).all()
    book_mark_list = []
    for mark in book_marks:
        book_mark_list.append(mark.to_dict())
    data = {
        'book_mark_list': book_mark_list
    }
    return json.dumps({'code': 0, 'data': data})


@book.route('/del_bookcase')
@login_required
def del_bookcase():
    book_ids = request.args.get('book_ids', '')
    book_id_list = book_ids.split("|")
    print book_id_list
    for book_id in book_id_list:
        shelf = BookShelf.query.filter_by(name=MYSELF_TYPE, user_id=current_user.id, book_id=book_id).first()
        if not shelf:
            return json.dumps({'code': -2, 'msg': u'书籍还没有加入书架'})
        try:
            db.session.delete(shelf)
            db.session.commit()
        except:
            return json.dumps({'code': -1, 'msg': u'网络错误'})
    return json.dumps({'code': 0, 'data': {}})



@book.route('/book_ranking')
def book_ranking():
    """ 书籍排行榜 """
    #2女生排行榜 1男生排行榜 3出版排行榜
    big_place = request.args.get('big_place', 0, int)
    #1人气榜 2新书榜 3完结榜 4畅销榜
    place = request.args.get('place', 1, int)
    page_no = int(request.args.get("page_no", 1))
    num = int(request.args.get("num", 20))

    if not big_place:
        data = {
            1: {1: u'男生人气榜', 2: u'男生新书榜', 3: u'男生完结榜', 4: u'出版畅销榜'},
            2: {1: u'女生人气榜', 2: u'女生新书榜', 3: u'女生完结榜', 4: u'出版畅销榜'},
            3: {1: u'出版人气榜', 2: u'出版新书榜'}
        }
        return json.dumps({'code': 0, 'data': data})
    buy_ranking_list = get_ranking_list(big_place, place, page_no, num)
    data = {
        "buy_ranking_list": buy_ranking_list,
        "page_no": page_no,
        "num": num
    }

    return json.dumps({'code': 0, 'data':data})


@book.route('/get_ranking')
def get_ranking():
    """ 获取对应大分类排行榜 """
    big_place = request.args.get('big_place', 1, int)

    key = 'get_ranking_%s' % big_place
    
    redis_data = redis_utils.get_cache(key, refresh_expires=False)
    if redis_data:
        return json.dumps({'code':0, 'data': json.loads(redis_data)})

    ranking_list = {
        1: {1: {'name':u'男生人气榜', 'url':'http://ov2eyt2uw.bkt.clouddn.com/nanren.png'},
            2: {'name':u'男生新书榜', 'url':'http://ov2eyt2uw.bkt.clouddn.com/nanxin.png'}, 
            3: {'name':u'男生完结榜', 'url':'http://ov2eyt2uw.bkt.clouddn.com/nanwan.png'}, 
            4: {'name':u'出版畅销榜', 'url':'http://ov2eyt2uw.bkt.clouddn.com/chuchang.png'}},
        2: {1: {'name':u'女生人气榜', 'url':'http://ov2eyt2uw.bkt.clouddn.com/nvren.png'}, 
            2: {'name':u'女生新书榜', 'url':'http://ov2eyt2uw.bkt.clouddn.com/nvxin.png'}, 
            3: {'name':u'女生完结榜', 'url': 'http://ov2eyt2uw.bkt.clouddn.com/nvwan.png'}, 
            4: {'name':u'出版畅销榜', 'url':'http://ov2eyt2uw.bkt.clouddn.com/chuchang.png'}},
        3: {1: {'name':u'出版人气榜', 'url': 'http://ov2eyt2uw.bkt.clouddn.com/churen.png'}, 
            2: {'name':u'出版新书榜', 'url': 'http://ov2eyt2uw.bkt.clouddn.com/chuxin.png'}}
    }
    ranking = ranking_list.get(big_place)
    if not ranking:
        return json.dumps({'code': -1, 'msg': u'请选择条件查询'})
    big_list = {}
    for r in ranking:
        buy_ranking_list = get_ranking_list(big_place, r, 1, 3)
        big_list[r] = buy_ranking_list

    data = {
        'ranking': ranking,
        'big_list': big_list,
        'big_place': big_place
    }
    redis_utils.set_cache(key, json.dumps(data), 3600)
    return json.dumps({'code': 0, 'data': data})


def get_ranking_list(big_place, place, page_no, num):

    today = datetime.date.today()
    start_day = today - datetime.timedelta(days=30)
    now_book_time = today - datetime.timedelta(days=30)
    #query = BuyRankings.query.order_by(BuyRankings.buy_num.desc()).filter(BuyRankings.created.between(start_day, today))
    query = db.session.query(BuyRankings.book_id, BuyRankings.book_name, func.sum(BuyRankings.buy_num)).group_by(BuyRankings.book_id).filter(BuyRankings.created.between(start_day, today)).order_by(func.sum(BuyRankings.buy_num).desc())
    if big_place == 1 or big_place == 2:
        big_query = query.filter(BuyRankings.channel_type == big_place)
    else:
        big_query = query.filter(BuyRankings.is_publish == 1)

    
    if place == 1:
        pagination = big_query[(page_no-1)*num:page_no*num]
    elif place == 2:
        pagination = big_query.filter(BuyRankings.book_time.between(now_book_time, today))[(page_no-1)*num:page_no*num]
    elif place == 3:
        pagination = big_query.filter(BuyRankings.status == 1)[(page_no-1)*num:page_no*num]
    else:
        pagination = big_query.filter(BuyRankings.is_publish == 1)[(page_no-1)*num:page_no*num]
    
    #buy_rankings = pagination.items
    buy_ranking_list = []
    for buy_ranking in pagination:
        print buy_ranking
        b = Book.query.filter_by(book_id=buy_ranking.book_id).first()
        book_dict = b.to_dict()
        category = BookCategory.query.filter_by(cate_id=b.cate_id).first()
        book_dict['cate_name'] = category.cate_name
        buy_ranking_list.append(book_dict)
    return buy_ranking_list

@book.route('/find_more')
def find_more():
    """ 首页分类发现更多 """
    params = request.args.get('params', HOT_TYPE)
    page_no = int(request.args.get("page_no", 1)) 
    num = int(request.args.get("num", 20))
    sex = request.args.get('sex', 1, int)
    
    key = 'find_more_%s_%s_%s_%s' % (params, page_no, num, sex)
    redis_data = redis_utils.get_cache(key, refresh_expires=False)
    redis_data = ''
    if redis_data:
        return json.dumps({'code':0, 'data': json.loads(redis_data)})
    if params == COMIC_TYPE:
        books = Book.query.filter(Book.showed == True, Book.is_comic == True, or_(Book.channel_type==sex, Book.channel_type==0))[(page_no-1)*num:page_no*num]
        book_list = []
        for book in books:
            book_dict = book.to_dict()
            category = BookCategory.query.filter_by(cate_id=book.cate_id).first()
            book_dict['cate_name'] = category.cate_name
            book_list.append(book_dict)
    else:
        book_shelfs = BookShelf.query.filter_by(name=params, showed=True)
        book_shelfs = book_shelfs.order_by(BookShelf.ranking.desc())[(page_no-1)*num: page_no*num]
        book_list = []
        for book in book_shelfs:
            b = Book.query.filter_by(book_id=book.book_id).first()
            if b:
                book_dict = b.to_dict()
                category = BookCategory.query.filter_by(cate_id=b.cate_id).first()
                book_dict['cate_name'] = category.cate_name if category else u'其他'
                book_list.append(book_dict)

    data = { 
        "book_list": book_list,
        "page_no": page_no,
        "num": num,
        "sex": sex 
    }   
    redis_utils.set_cache(key, json.dumps(data), 3600)
    return json.dumps({'code': 0, 'data': data})


@book.route('/update_bookcase_date')
@login_required
def update_bookcase_date():
    ''' 更新书籍在书架阅读时间 '''
    book_id = request.args.get('book_id')
    shelf = BookShelf.query.filter_by(name=MYSELF_TYPE, user_id=current_user.id, book_id=book_id).first()
    if shelf:
        now = datetime.datetime.now()
        shelf.updated = now
        try:
            db.session.add(shelf)
            db.session.commit()
        except:
            return json.dumps({'code': -1, 'msg': u'网络错误'})
    else:
        pass
    return json.dumps({'code': 0, 'data': {}})


@book.route('/find_bookcase_status')
@login_required
def find_bookcase_status():
    """ 查询图书是否在书架 """
    book_ids = request.args.get('book_ids', '')
    book_id_list = book_ids.split("|")
    book_status_list = []
    for book_id in book_id_list:
        shelf = BookShelf.query.filter_by(name=MYSELF_TYPE, user_id=current_user.id, book_id=book_id).first()
        if shelf:
            book_status_list.append(1)
        else:
            book_status_list.append(0)
    data = {
        'book_status_list': book_status_list    
    }
    return json.dumps({'code': 0, 'data': data})


@book.route('/free_source/list')
@login_required
def free_source_list():
    """切换外链源"""
    book_id = request.args.get('book_id', 0, int)
    free_books = FreeBook.query.filter_by(book_id=book_id).all()
    data = [{'free_source': book.free_source,
             'last_chapter_name': book.last_chapter_name,
             'update_time': arrow.Arrow.fromdatetime(book.update_time, tzlocal()).humanize(locale='zh_cn') + u'更新'} for book in free_books]
    return json.dumps({'code': 0, 'data': data})


@book.route('/get_free_book')
def get_free_book():
    """ 获取免费书籍 """
    sex = request.args.get("sex", 1, int)
    page_no = request.args.get("page_no", 1, int)
    num = request.args.get("num", 20, int)
    platform = request.args.get("platform", "android")
    mian_banner = 'http://ov2eyt2uw.bkt.clouddn.com/mianfei.jpg'
    if platform == 'android':
        mian_banner = 'http://ov2eyt2uw.bkt.clouddn.com/free_banner_1023.jpg'
    key = 'get_free_book_%s_%s_%s' % (page_no, num, sex)
    redis_data = redis_utils.get_cache(key, refresh_expires=False)
    if redis_data:
        return json.dumps({'code':0, 'data': json.loads(redis_data)})

    pagination = Book.query.order_by(Book.ranking.desc()).filter(Book.showed == True, Book.free_collect == True, Book.channel_type==sex).paginate(page_no, per_page=num, error_out=False)
    books = pagination.items
    book_list = []
    for book in books:
        book_dict = book.to_dict()
        category = BookCategory.query.filter_by(cate_id=book.cate_id).first()
        book_dict['cate_name'] = category.cate_name
        book_list.append(book_dict)
    data = {
        'mian_banner': mian_banner,
        'book_list': book_list
    }
    redis_utils.set_cache(key, json.dumps(data), 300)
    return json.dumps({'code': 0, 'data':data})

@book.route('/init_topic')
def init_topic():
    top_list = get_top_list('9.9.9')
    for i in top_list:
        db.session.add(Topic(i))
    db.session.commit()
    return json.dumps({'code': 0, 'data': top_list})

@book.route('/init_comic')
def init_comic():
    books = Book.query.filter(Book.showed == True, Book.is_comic == True).all()
    for i in books:
        if not BookShelf.query.filter_by(book_id=i.book_id, name=COMIC_TYPE).first():
            db.session.add(BookShelf(i.book_id, COMIC_TYPE, 0, 0, 0, 1, 0))
    db.session.commit()
    return 'ok.'

@book.route('/init_channel')
def init_channel():
    channel_list = [{'name': u'男生', 'ranking': 0},
    {'name': u'女生', 'ranking': 1}]
    for data in channel_list:
        ct = ChannelType.query.filter_by(name=data['name']).first()
        if not ct:
            ct = ChannelType(data)
            db.session.add(ct)
            db.session.commit()
        # 添加banner
        if ct.name == u'男生':
            banners = Banner.query.filter(Banner.sex.in_([0,1])).all()
        else:
            banners = Banner.query.filter(Banner.sex.in_([0,2])).all()
        for b in banners:
            cd = ChannelData.query.filter_by(class_id=b.id, class_name='banner', channel_code=ct.id).first()
            if not cd:
                cd = ChannelData(class_id=b.id, class_name='banner', channel_code=ct.id)
                db.session.add(cd)

        # 添加Topic
        topics = Topic.query.all()
        for top in topics:
            cd = ChannelData.query.filter_by(class_id=top.id, class_name='topic', channel_code=ct.id).first()
            if not cd:
                cd = ChannelData(class_id=top.id, class_name='topic', channel_code=ct.id)
                db.session.add(cd)

        # 添加BookShelfName
        bookshelfnames = BookShelfName.query.all()
        for bsn in bookshelfnames:
            if bsn.name in ('myself', 'recommend'):
                continue
            cd = ChannelData.query.filter_by(class_id=bsn.id, class_name='book_shelf_name', channel_code=ct.id).first()
            if not cd:
                cd = ChannelData(class_id=bsn.id, class_name='book_shelf_name', channel_code=ct.id)
                db.session.add(cd)
    db.session.commit()
    return 'ok.'
