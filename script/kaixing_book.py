# -*- coding: utf-8 -*-
"""
Doc: 恺兴

Created on 2017/9/20
@author: MT
"""

import ujson as json
import datetime
import requests
from requests.adapters import HTTPAdapter
from models import db
from models import BookCategory, Book, BookVolume, BookChapters, BookChapterContent
from models.book import ChannelBookCategory
from lib import utils

PARTNER_ID = 2152
PARTNER_SIGN = '01098b30b5b04f3f532eb5635791713f'

# 请求失败时重试三次
session = requests.Session()
session.mount('https://partner.chuangbie.com', HTTPAdapter(max_retries=3))


def req_api(url, **kwargs):
    """请求对方接口"""
    kwargs['partner_id'] = PARTNER_ID
    kwargs['partner_sign'] = PARTNER_SIGN
    resp = session.post(url, data=kwargs)
    data = resp.json()
    print data.get('msg', '')
    if data['flag'] is False:
        return None
    return data


def get_book_list():
    """获取书籍列表"""
    api_url = 'https://partner.chuangbie.com/partner/booklist'
    data = req_api(api_url, page_now=1, page_size=10000)
    if not data:
        return []

    book_data = data['content']['data']
    # 获取本地已有分类
    local_cate_dict = {cate.channel_cate_id: cate.cate_id for cate in ChannelBookCategory.query.all()}
    book_list = []
    now = datetime.datetime.now()
    for book in book_data:
        cate_id = local_cate_dict.get(gen_channel_bind_id(int(book['ftype_id'])))
        if not cate_id:
            print '!!!!NO cate_id: ', book
            continue
        book_list.append(dict(book_id=int(book['book_id']),
                              book_name=book['book_name'],
                              cate_id=cate_id,
                              channel_type=int(book['attribution']),
                              author_name=book['author_name'],
                              chapter_num=0,
                              is_publish=(1 if int(book['attribution']) == 3 else 2),
                              status=(1 if int(book['status']) == 2 else 2),
                              create_time=now,
                              cover=book['cover_url'],
                              intro=book['description'],
                              word_count=int(book['word_count']),
                              last_update_chapter_id=int(book['last_update_chapter_id']),
                              source='kaixing',
                              update_time=now))
    return book_list


def get_chapter_list(book_id, max_cid=0):
    """获取章节列表"""
    api_url = 'https://partner.chuangbie.com/partner/chapterlist'
    data = req_api(api_url, book_id=book_id, min_chapter_id=max_cid)
    if not data:
        return []
    return data['content']['data']


def update_volume_chapter(real_book_id, local_book):
    """更新卷章节"""
    book_id = local_book['book_id']
    max_cid = local_book.get('max_cid', 0)
    chapter_list = get_chapter_list(real_book_id, max_cid)
    if not chapter_list:
        return

    for chapter in chapter_list:
        # 增加卷
        volume_id = int(chapter['volume_id'])
        if volume_id > local_book.get('max_vid', 0):
            volume_name = get_volume_name(real_book_id, volume_id)
            db.session.add(BookVolume(dict(book_id=book_id,
                                           volume_id=volume_id,
                                           volume_name=volume_name)))
            local_book['max_vid'] = volume_id

        chapter_id = int(chapter['chapter_id'])
        if chapter_id <= max_cid:
            continue

        # 增加章节
        db.session.add(BookChapters(dict(book_id=book_id,
                                         volume_id=volume_id,
                                         chapter_id=chapter_id,
                                         chapter_name=chapter['chapter_name'],
                                         word_count=int(chapter['word_count']),
                                         create_time=chapter['update_time'],
                                         update_time=chapter['update_time'])))
        content = get_chapter_content(real_book_id, chapter_id)
        db.session.add(BookChapterContent(dict(book_id=book_id,
                                               volume_id=volume_id,
                                               chapter_id=chapter_id,
                                               content=content)))


def get_volume_name(book_id, volume_id):
    """获取卷名称"""
    api_url = 'https://partner.chuangbie.com/partner/bookvolume'
    data = req_api(api_url, book_id=book_id, volume_id=volume_id)
    return data['content']['data']['volume_name']


def get_chapter_content(book_id, chapter_id):
    """获取章节正文"""
    api_url = 'https://partner.chuangbie.com/partner/chaptercontent'
    data = req_api(api_url, book_id=book_id, chapter_id=chapter_id)
    return data['content']['data']['chapter_content']


def pull_book():
    """拉取最新书籍信息"""
    book_list = get_book_list()
    print "Books: ", book_list
    print len(book_list)
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
            db.session.add(book_m)
            db.session.commit()

            # 增加章节
            local_book = {'book_id': book_m.book_id}
            update_volume_chapter(book['book_id'], local_book)
            book_m.cover = utils.upload_img_by_url('book_cover_%s' % book_m.book_id, book_m.cover)
        else:
            if book['word_count'] > local_book['word_count'] or \
                            book['last_update_chapter_id'] > local_book['max_cid']:
                # 更新章节
                update_volume_chapter(book['book_id'], local_book)

            # 更新书籍
            book['book_id'] = local_book['book_id']
            update_book(book)
        db.session.commit()


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
        on bc.book_id=b.book_id where b.source='kaixing' group by b.book_id
    ''').fetchall()
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
        update book set
            book_name=:book_name,
            author_name=:author_name,
            chapter_num=:chapter_num,
            status=:status,
            intro=:intro,
            word_count=:word_count,
            update_time=:update_time
        where book_id=:book_id''', {
        "book_name": data['book_name'],
        "author_name": data['author_name'],
        "chapter_num": data['chapter_num'],
        "status": data['status'],
        "intro": data['intro'],
        "word_count": int(data['word_count']),
        "update_time": data['update_time'],
        "book_id": data['book_id'],
    })


def gen_channel_bind_id(bind_id):
    """生成渠道相关id"""
    return 'kaixing:%s' % bind_id


def update_book_category():
    """更新书籍分类列表"""
    api_url = 'https://partner.chuangbie.com/partner/booktypelist'
    data = req_api(api_url)
    if not data:
        return

    # 获取本地已有分类
    local_cate_list = db.session.query(ChannelBookCategory, BookCategory).filter(
        ChannelBookCategory.cate_id == BookCategory.cate_id).all()
    local_cate_dict = {cate.ChannelBookCategory.channel_cate_id: cate.BookCategory for cate in local_cate_list}
    local_cate_name_dict = {cate.BookCategory.cate_name: cate.BookCategory.cate_id for cate in local_cate_list}

    cate_list = data['content']['data']
    for cate in cate_list:
        channel_cate_id = gen_channel_bind_id(cate['type_id'])
        local_cate = local_cate_dict.get(channel_cate_id)
        if local_cate:
            continue

        cate_name = cate['type_name']
        cate_id = local_cate_name_dict.get(cate_name)
        if not cate_id:
            cate_m = BookCategory(cate_name, _get_parent_id(int(cate['attribution'])))
            db.session.add(cate_m)
            db.session.commit()
            cate_id = cate_m.cate_id
        db.session.add(ChannelBookCategory(channel_cate_id, cate_id))
        db.session.commit()


def _get_parent_id(attribution):
    """获取上级分类"""
    if attribution == 1:  # 男生
        return 1
    elif attribution == 2:  # 女生
        return 3
    elif attribution == 3:  # 出版
        return 2


if __name__ == '__main__':
    # print update_book_category()
    print get_book_list()
