# -*- coding: utf-8 -*-
"""
Doc: 安之

Created on 
@author: 
"""

import ujson as json
import datetime
import requests
from requests.adapters import HTTPAdapter
from models import db
from models import BookCategory, Book, BookVolume, BookChapters, BookChapterContent
from models.book import ChannelBookCategory
from lib import redis_utils
import time

P_ID = 1018
API_KEY = 'ce312a4106eae3a0e121e367a312ea63'

# 请求失败时重试三次
session = requests.Session()
session.mount('http://www.azycjd.com', HTTPAdapter(max_retries=3))
a_num = 0
def req_api(url, **kwargs):
    """请求对方接口"""
    #kwargs['pid'] = P_ID
    #kwargs['apikey'] = API_KEY
    #if not a_num%5:
    #    time.sleep(3)
    url = url + '&pid=%s&apikey=%s'%(P_ID, API_KEY)
    try:
        resp = session.get(url, timeout=10)
    except:
        time.sleep(300)
        pull_book()
    data = resp.json()
    time.sleep(0.5)
    #a_num += 1
    if data['result']:
        return None
    return data


def get_book_list():
    """获取书籍列表"""
    api_url = 'http://www.azycjd.com/webnovelmis/azinterface/koudai/novelList?1=1'
    data = req_api(api_url)
    if not data:
        return []

    book_data = data['data']
    #print data
    # 获取本地已有分类
    #local_cate_dict = {cate.channel_cate_id: cate.cate_id for cate in ChannelBookCategory.query.all()}
    book_list = []
    now = datetime.datetime.now()
    for book in book_data:
        #cate_id = local_cate_dict.get(gen_channel_bind_id(int(book['type_id'])))
        if int(book['type_id']) in range(9, 17):
            cate_id = 1002
        elif int(book['type_id']) in range(17, 24):
            cate_id = 3015
        elif int(book['type_id']) in range(24, 38):
            cate_id = 3027
        elif int(book['type_id']) in range(38, 50) or int(book['type_id']) in range(58, 71):
            cate_id = 3024
        elif int(book['type_id']) in range(50, 58):
            cate_id = 3016
        elif int(book['type_id']) in range(71, 79):
            cate_id = 3013
        elif int(book['type_id']) in range(79, 89):
            cate_id = 3018

        if not cate_id:
            print '!!!!NO cate_id: ', book['book_name']
            continue
        book_list.append(dict(book_id=int(book['book_id']),
                              book_name=book['book_name'],
                              cate_id=cate_id,
                              channel_type=1,#源无此属性默认0
                              author_name=book['author'],
                              chapter_num=0,
                              is_publish=(1 if book['is_out'] == '1' else 2),
                              status=(1 if int(book['book_status']) == 1 else 2),
                              create_time=now,
                              cover=book['cover_link'],
                              intro=book['description'],
                              word_count=int(book['book_size']),
                              source='anzhi',
                              update_time=now))
    return book_list


def get_chapter_list(book_id):
    """获取章节列表"""
    api_url = 'http://www.azycjd.com/webnovelmis/azinterface/koudai/fenjuan?bookid=%s'%book_id
    data = req_api(api_url)
    if not data:
        return []
    return data['data']

def get_chapter_content(book_id, chapter_id):
    api_url = 'http://www.azycjd.com/webnovelmis/azinterface/koudai/chapterById?bookid=%s&chapterid=%s'%(book_id, chapter_id)
    print api_url
    data = req_api(api_url)
    if not data:
        return {}
    return data['data']


def update_volume_chapter(loca_book_id, book_id, max_cid):
    """更新卷章节"""
    chapter_list = get_chapter_list(book_id)
    if not chapter_list:
        return 0
    now = datetime.datetime.now()
    #    data = json.loads(redis_data)
    #    if max_cid < int(chapter_list[len(chapter_list)-1]['chapter_id']) and data:
    #        data[index]['max_cid'] = int(chapter_list[len(chapter_list)-1]['chapter_id'])
    #        redis_utils.set_cache(key, json.dumps(data), 86400)
    if max_cid >= int(chapter_list[len(chapter_list)-1]['chapter_id']):
        return 0
    for chapter in chapter_list:
        # 增加章节
        print chapter['chapter_name']
        chapter_id = int(chapter['chapter_id'])
        if chapter_id <= max_cid:
            continue
        try:
            chapter_content = get_chapter_content(book_id, chapter_id)
        except:
            key = 'error_pull_book_anzhi'
            redis_data = redis_utils.get_cache(key, refresh_expires=False)
            if redis_data:
                data = json.loads(redis_data)
                data.append({'book_id': book_id, 'chapter_id': chapter_id})
                redis_utils.set_cache(key, json.dumps(data), 86400)
            else:
                redis_utils.set_cache(key, json.dumps([{'book_id':book_id, 'chapter_id':apter_id}]), 86400)
            return book_id, chapter_id
        db.session.add(BookChapterContent(dict(book_id=loca_book_id,
                                            volume_id=0,
                                            chapter_id=chapter_id,
                                            content=chapter_content['content'].replace('<p>', '').replace('</p>', '').replace('\\n', '\n'))))

        db.session.add(BookChapters(dict(
            book_id=loca_book_id,
            volume_id=0,
            chapter_id=chapter_id,
            chapter_name=chapter['chapter_name'],
            create_time=now,
            update_time=now,
            word_count=cal_word_count(chapter_content['content']),
        )))
    return 1


def cal_word_count(content):
    """计算章节字数 只计算中英文"""
    num = 0 
    for i in content:
        if is_chinese(i) or is_letter(i):
            num += 1
    return num 


def is_chinese(u_char):
    """判断一个unicode是否是汉字"""
    return u'\u4e00' <= u_char <= u'\u9fa5'


def is_num(u_char):
    """判断一个unicode是否是数字"""
    return u'\u0030' <= u_char <= u'\u0039'


def is_letter(u_char):
    """判断一个unicode是否是英文字母"""
    return (u'\u0041' <= u_char <= u'\u005a') or (u'\u0061' <= u_char <= u'\u007a')


def pull_book():
    """拉取最新书籍信息"""
    book_list = get_book_list()
    a_num = 0
    finish_list = []
    key = 'error_pull_book_anzhi'
    redis_utils.set_cache(key, json.dumps([]), 86400)
    #key = 'pull_book_anzhi'
    #redis_data = redis_utils.get_cache(key, refresh_expires=False)
    #redis_data = ''
    #if redis_data:
    #    redis_book_list = json.loads(redis_data)
    #    for i, book in enumerate(redis_book_list):
    #        update_volume_chapter(book['loca_book_id'], book['book_id'], book['max_cid'], i)
    #        update_book(book)


    #else:
    # 取本地书籍对应最新章节id 卷id 更新时间
    for book in book_list:
        print book['book_name']
        print '--------------------------------'
        my_book = Book.query.filter_by(channel_book_id=gen_channel_bind_id(book['book_id'])).first()
        channel_book_id = gen_channel_bind_id(book['book_id'])
        book['channel_book_id'] = channel_book_id
        if my_book:
            book_m = my_book
            ch = BookChapters.query.order_by(BookChapters.chapter_id.desc()).filter(BookChapters.book_id==book_m.book_id).first()
            if ch:
                code = update_volume_chapter(book_m.book_id, book['book_id'], ch.chapter_id)
            else:
                code = update_volume_chapter(book_m.book_id, book['book_id'], 0)
            if code:
                update_book(book)
        else:
            book_m = Book(book)
            db.session.add(book_m)
            db.session.commit()
            update_volume_chapter(book_m.book_id, book['book_id'], 0)
        if book['status'] == 2:
            finish_list.append({'book_id':book['book_id'], 'book_name':book['book_name']})
        db.session.commit()
    redis_data = redis_utils.get_cache(key, refresh_expires=False)
    if redis_data:
        print 'error data----------------------'+ redis_data
    print 'lianzaizhong++++++++++++'+ str(finish_list)


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
    return 'anzhi:%s' % bind_id



if __name__ == '__main__':
    # print update_book_category()
    pull_book()
