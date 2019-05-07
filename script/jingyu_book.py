# -*- coding: utf-8 -*-
"""
Doc: 鲸鱼中文网

Created on 2017/9/27
@author: MT
"""
import datetime
import json
from lib import utils
import requests
import xmltodict
from flask import current_app
from requests.adapters import HTTPAdapter

from models import BookCategory, Book, BookVolume, BookChapters, BookChapterContent
from models import db

# 请求失败时重试三次
session = requests.Session()
session.mount('', HTTPAdapter(max_retries=3))

CHANNEL_NAME = 'jingyu'
BOOK_LIST_URL = 'http://manager.jingyu.com/api/getBookList'
BOOK_INFO_URL = 'http://manager.jingyu.com/api/bookInfo'
CHAP_LIST_URL = 'http://manager.jingyu.com/api/chapterList'
CHAP_CONTENT_URL = 'http://manager.jingyu.com/api/chapterContent'
DELETE_BOOK_URL = 'http://manager.jingyu.com/api/deleteBookList'


def req_api(url, retry=3, **kwargs):
    """请求对方接口"""
    print 'API=== %s ===' % url, kwargs
    resp = session.get(url, params=kwargs)
    retry = retry - 1
    if not resp.text and retry > 0:
        return req_api(url, retry=retry, **kwargs)
    text = confir(resp.content)
    parse_data = xmltodict.parse(text)
    print 'API=== return', json.dumps(parse_data)[:100]
    return parse_data


def get_last_update_time():
    """获取上次更新时间"""
    cache_key = 'last_update_jingyu_book_time'
    update_time = current_app.redis.get(cache_key) or \
        (datetime.datetime.now() - datetime.timedelta(hours=1)).strftime('%Y-%m-%d %H:%M:%S')
    return update_time


def set_last_update_time(start_time):
    cache_key = 'last_update_jingyu_book_time'
    current_app.redis.set(cache_key, start_time.strftime('%Y-%m-%d %H:%M:%S'))


def get_book_list():
    """获取书籍列表"""
    data = req_api(BOOK_LIST_URL, begin_time=get_last_update_time())
    if not data:
        return []

    # 获取本地已有分类
    local_cate_dict = {cate.cate_name.encode('utf8'): cate.cate_id for cate in BookCategory.query.all()}
    book_list = []
    cur_time = datetime.datetime.now()
    for _book in data['document']['books']['book']:
        book_id = int(_book['id'])
        book = req_api(BOOK_INFO_URL, bookid=book_id)['book']
        cate_id = local_cate_dict.get(book['class'].encode('utf8')) or local_cate_dict.get('其他')
        if not cate_id:
            print '!!!!NO cate_id: ', book
            continue
        book_list.append(dict(book_id=book_id,
                              book_name=book['name'],
                              cate_id=cate_id,
                              channel_type=1,
                              author_name=book['author'],
                              chapter_num=0,
                              is_publish=2,
                              status=(1 if int(book['status']) == 2 else 2),
                              create_time=cur_time,
                              cover=book['bigimg'],
                              intro=book['bookintr'],
                              word_count=int(book['words']),
                              source=CHANNEL_NAME,
                              update_time=book['updatetime']))
    return book_list


def get_volume_chapter_list(channel_book_id, max_cid, local_book_id):
    """获取卷和章节列表"""
    data = req_api(CHAP_LIST_URL, bookid=channel_book_id, offset_chapid=max_cid)
    if not data:
        return [], []

    volume_list = []
    chapter_list = []
    if not data['chaplist']:
        return [], []
    volume_data_group = data['chaplist']['volume']
    if isinstance(volume_data_group, dict):
        volume_data_group = [volume_data_group]
    for volume_data in volume_data_group:
        volume_id = int(volume_data['volumeid'])
        volume = {
            'book_id': local_book_id,
            'volume_id': volume_id,
            'volume_name': volume_data['volumename'],
        }
        volume_list.append(volume)
        chap_data_list = volume_data['chapters']['chap']
        if isinstance(chap_data_list, dict):
            chap_data_list = [chap_data_list]
        for chap in chap_data_list:
            chap_detail = req_api(CHAP_CONTENT_URL, bookid=channel_book_id, chapid=int(chap['id']))['chapter']
            chapter_list.append({
                'book_id': local_book_id,
                'volume_id': volume_id,
                'volume_name': volume_data['volumename'],
                'chapter_id': int(chap['id']),
                'chapter_name': chap['title'],
                'word_count': int(chap_detail['words']),
                'create_time': datetime.datetime.fromtimestamp(int(chap_detail['updatetime'])),
                'update_time': datetime.datetime.fromtimestamp(int(chap_detail['updatetime'])),
                'content': chap_detail['content'].replace('<p>', '').replace('</p>', '\n')
            })
    return volume_list, chapter_list


def update_volume_chapter(real_book_id, local_book):
    """更新卷章节"""
    local_book_id = local_book['book_id']
    max_cid = local_book.get('max_cid', 0)
    volume_list, chapter_list = get_volume_chapter_list(real_book_id, max_cid, local_book_id)
    max_vid = local_book.get('max_vid', 0)
    for volume in volume_list:
        if volume['volume_id'] > max_vid:
            # 增加卷
            db.session.add(BookVolume(volume))

    for chapter in chapter_list:
        if chapter['chapter_id'] <= max_cid:
            continue

        # 增加章节
        db.session.add(BookChapters(chapter))
        db.session.add(BookChapterContent(chapter))


def pull_book():
    """拉取最新书籍信息"""
    start_time = datetime.datetime.now()
    book_list = get_book_list()
    print "book num:", len(book_list)
    if not book_list:
        return

    # 取本地书籍对应最新章节id 卷id 更新时间
    local_latest_books = get_local_book_latest()
    for book in book_list:
        channel_book_id = gen_channel_bind_id(book['book_id'])
        book['channel_book_id'] = channel_book_id
        local_book = local_latest_books.get(channel_book_id, {})
        if not local_book:
            book_m = Book(book)
            book_m.word_count = 0
            db.session.add(book_m)
            db.session.commit()

            # 增加章节
            local_book = {'book_id': book_m.book_id}
            update_volume_chapter(book['book_id'], local_book)

            book_m.cover = utils.upload_img_by_url('book_cover_%s' % book_m.book_id, book_m.cover)
            book_m.word_count = book['word_count']
        else:
            if book['word_count'] > local_book['word_count'] or \
                            book['update_time'] > local_book['update_time']:
                # 更新章节
                update_volume_chapter(book['book_id'], local_book)

            # 更新书籍
            book['book_id'] = local_book['book_id']
            update_book(book)
        try:
            db.session.commit()
            set_last_update_time(start_time)
        except Exception:
            db.session.rollback()


def get_local_book_latest():
    """获取本地已缓存书籍最新信息"""
    # cache_key = 'local_latest_book_info'
    # data = current_app.redis.get(cache_key)
    # if data:
    #     data = json.loads(data)
    #     data = {int(k): v for k, v in data.iteritems()}
    #     return data
    # else:
    import time
    t1 = time.time()
    local_latest_books = db.session.execute('''
        select b.channel_book_id, b.book_id, max(bc.volume_id) as volume_id,
            max(bc.chapter_id) as chapter_id, b.update_time, b.chapter_num, b.word_count
        from book_chapters bc right join book b
        on bc.book_id=b.book_id where b.source="%s" group by b.book_id
    ''' % CHANNEL_NAME).fetchall()
    print '查询时间', time.time() - t1
    local_latest_books = {b.channel_book_id: {"max_vid": int(b.volume_id or 0),
                                              "max_cid": int(b.chapter_id or 0),
                                              "book_id": int(b.book_id),
                                              "update_time": b.update_time.__str__(),
                                              "word_count": int(b.word_count),
                                              "chapter_num": int(b.chapter_num)} for b in local_latest_books}
    print "local_latest_books: ", local_latest_books
    return local_latest_books


def update_book(data):
    """更新书籍信息"""
    db.session.execute('''
UPDATE book
SET
  book_name    = :book_name,
  author_name  = :author_name,
  chapter_num  = :chapter_num,
  status       = :status,
  intro        = :intro,
  word_count   = :word_count,
  update_time  = :update_time
WHERE book_id = :book_id''', {
        "book_name": data['book_name'],
        "cate_id": int(data['cate_id']),
        "channel_type": int(data['channel_type']),
        "author_name": data['author_name'],
        "chapter_num": data['chapter_num'],
        "is_publish": data['is_publish'],
        "status": data['status'],
        "intro": data['intro'],
        "word_count": int(data['word_count']),
        "update_time": data['update_time'],
        "book_id": data['book_id'],
    })


def gen_channel_bind_id(bind_id):
    """生成渠道相关id"""
    return '%s:%s' % (CHANNEL_NAME, bind_id)


def confir(str):
    """过滤不可见字符"""
    for i in range(0,32):
        str = str.replace(chr(i),'')
    return  str
