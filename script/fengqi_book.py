# -*- coding: utf-8 -*-
"""
Doc: 风起中文网

Created on 2017/9/27
@author: MT
"""
import datetime
import requests
from requests.adapters import HTTPAdapter
from models import db
from models import BookCategory, Book, BookVolume, BookChapters, BookChapterContent
from models.book import ChannelBookCategory

# 请求失败时重试三次
session = requests.Session()
session.mount('https://partner.chuangbie.com', HTTPAdapter(max_retries=3))


def req_api(url, **kwargs):
    """请求对方接口"""
    url = ''
    kwargs['apikey'] = ''
    resp = session.get(url, params=kwargs)
    if resp.status_code != 200:
        return None
    return resp.json()


def get_book_list():
    """获取书籍列表"""
    data = req_api('')
    if not data:
        return []

    # 获取本地已有分类
    local_cate_dict = {cate.cate_name: cate.cate_id for cate in BookCategory.query.all()}
    book_list = []
    for _book in data:
        book = req_api('', book_id=_book['bookid'])
        book_type, cate_name = book['class'].split('-')
        book_type = 1 if book_type == '原创男频' else 2
        cate_id = local_cate_dict.get(cate_name)
        if not cate_id:
            print '!!!!NO cate_id: ', book
            continue
        book_list.append(dict(book_id=book['bookid'],
                              book_name=book['title'],
                              cate_id=cate_id,
                              channel_type=book_type,
                              author_name=book['author'],
                              chapter_num=book['chaptercount'],
                              is_publish=2,
                              status=(1 if book['bookstatus'] == 1 else 2),
                              create_time=datetime.datetime.fromtimestamp(book['createtime']),
                              cover=book['cover_url'],
                              intro=book['description'],
                              word_count=book['total_words'],
                              source='fengqi',
                              update_time=datetime.datetime.fromtimestamp(book['lastupdatetime'])))
    return book_list


def get_chapter_list(book_id):
    """获取章节列表"""
    data = req_api('', book_id=book_id)
    if not data:
        return []
    return data


def update_volume_chapter(real_book_id, local_book):
    """更新卷章节"""
    book_id = local_book['book_id']
    max_cid = local_book.get('max_cid', 0)
    chapter_list = get_chapter_list(real_book_id)
    if not chapter_list:
        return

    for chapter in chapter_list:
        if chapter['chapterid'] <= max_cid:
            continue

        chapter = get_chapter_content(real_book_id, chapter['chapterid'])
        chapter['book_id'] = book_id

        # 增加卷
        if chapter['volume_id'] > local_book.get('max_vid', 0):
            db.session.add(BookVolume(dict(book_id=book_id,
                                           volume_id=chapter['volume_id'],
                                           volume_name=chapter['volume_name'])))
            local_book['max_vid'] = chapter['volume_id']

        # 增加章节
        db.session.add(BookChapters(chapter))
        db.session.add(BookChapterContent(chapter))


def get_chapter_content(book_id, chapter_id):
    """获取章节正文"""
    api_url = ''
    data = req_api(api_url, book_id=book_id, chapter_id=chapter_id)
    return {
        'volume_id': data['volumeid'],
        'volume_name': data['volumename'],
        'chapter_id': data['chapterid'],
        'chapter_name': data['chaptername'],
        'word_count': data['chaptersize'],
        'create_time': datetime.datetime.fromtimestamp(data['createtime']),
        'update_time': datetime.datetime.fromtimestamp(data['lastupdatetime']),
        'content': data['chaptercontent']
    }


def pull_book():
    """拉取最新书籍信息"""
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
            db.session.add(book_m)
            db.session.commit()

            # 增加章节
            local_book = {'book_id': book_m.book_id}
            update_volume_chapter(book['book_id'], local_book)
        else:
            if book['chapter_num'] > local_book['chapter_num'] or \
                    book['word_count'] > local_book['word_count'] or \
                    book['update_time'] > local_book['update_time']:
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
            cate_id=:cate_id,
            channel_type=:channel_type,
            author_name=:author_name,
            chapter_num=:chapter_num,
            is_publish=:is_publish,
            status=:status,
            cover=:cover,
            intro=:intro,
            word_count=:word_count,
            update_time=:update_time
        where book_id=:book_id''', {
        "book_name": data['book_name'],
        "cate_id": int(data['cate_id']),
        "channel_type": int(data['channel_type']),
        "author_name": data['author_name'],
        "chapter_num": data['chapter_num'],
        "is_publish": data['is_publish'],
        "status": data['status'],
        "cover": data['cover'],
        "intro": data['intro'],
        "word_count": int(data['word_count']),
        "update_time": data['update_time'],
        "book_id": data['book_id'],
    })


def gen_channel_bind_id(bind_id):
    """生成渠道相关id"""
    return 'fengqi:%s' % bind_id


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
