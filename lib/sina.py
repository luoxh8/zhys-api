# coding: utf-8
'''
    新浪小说内容输出
'''
import hashlib
import datetime
import requests
from requests.adapters import HTTPAdapter
import xmltodict
import ujson as json

APP_KEY = 'vq2cLCRngy'
CP_NAME = 'weidian'

# 请求失败时重试三次
session = requests.Session()
session.mount('http://api.open.book.sina.com.cn', HTTPAdapter(max_retries=3))


def get_sign():
    ''' 生成秘钥 '''
    today = datetime.datetime.now().strftime('%Y%m%d')
    tmp_str = '%s%s%s' % (today, CP_NAME, APP_KEY)
    return hashlib.md5(tmp_str).hexdigest()


def get_book_list():
    ''' 获取书籍列表 '''
    url = 'http://api.open.book.sina.com.cn/cpoutput/%s/books?sign=%s' % (CP_NAME, get_sign())
    headers = {'Content-Type': 'text/plain'}
    resp = session.get(url, headers=headers)
    print url
    # print 'get_book_list, result is', resp.text.encode('utf8')
    resp_data = xmltodict.parse(resp.text.encode('utf8'))
    result = resp_data['root']['result']
    # print result['data']

    # 异常状态处理
    if result['status']['code'] != '0':
        return json.dumps({'code': -1, 'msg': result['status']['msg']})

    # 成功状态处理
    datas = []
    for item in result['data']['books']:
        datas.append({
            'book_id': int(item['book_id']),
            'book_name': item['book_name'],
            'cp_id': item['cp_id'],
            'cate_id': item['cate_id'],
        })
    return json.dumps({'code': 0, 'data': datas})


def get_book_info(book_id):
    ''' 获取书籍基本信息 '''
    url = 'http://api.open.book.sina.com.cn/cpoutput/%s/book_info?book_id=%s&sign=%s' % (CP_NAME, book_id, get_sign())
    resp = session.get(url)
    # print 'get_book_info, result is', resp.text
    resp_data = xmltodict.parse(resp.text.encode('utf8'))
    result = resp_data['root']['result']

    # 异常状态处理
    if result['status']['code'] != '0':
        return json.dumps({'code': -1, 'msg': result['status']['msg']})

    # 成功状态处理
    item = result['data']
    data = {
        'id': item['id'],
        'book_id': int(item['book_id']),
        'book_name': item['book_name'],
        'cate_id': int(item['cate_id']),
        'channel_type': int(item['channel_type']),
        'author_name': item['author_name'],
        'end_date': item['end_date'],
        'chapter_num': int(item['chapter_num']),
        'is_publish': int(item['is_publish']),
        'status': int(item['status']),
        'create_time': datetime.datetime.fromtimestamp(int(item['create_time'])).__str__(),
        'cover': item['cover'],
        'intro': item['intro'],
        'word_count': int(item['word_count']),
        'update_time': datetime.datetime.fromtimestamp(int(item['update_time'])).__str__(),
    }
    return json.dumps({'code': 0, 'data': data})


def get_chapters(book_id):
    ''' 获取书籍章节信息 '''
    url = 'http://api.open.book.sina.com.cn/cpoutput/%s/chapters?book_id=%s&sign=%s' % (CP_NAME, book_id, get_sign())
    resp = session.get(url)
    # print 'get_chapters, result is', resp.text
    resp_data = xmltodict.parse(resp.text.encode('utf8'))
    result = resp_data['root']['result']

    # 异常状态处理
    if result['status']['code'] != '0':
        return json.dumps({'code': -1, 'msg': result['status']['msg']})

    # 成功状态处理
    datas = []
    for item in result['data'].values():
        tmp_item = {
            'book_id': int(item['book_id']),
            'volume_id': int(item['volume_id']),
            'volume_name': item['volume_name'],
            'create_time': datetime.datetime.fromtimestamp(int(item['create_time'])).__str__(),
            'chapter_count': int(item['chapter_count']),
            'update_time': datetime.datetime.fromtimestamp(int(item['update_time'])).__str__(),
            'chapters': [],
        }
        # 遍历录入章节信息
        chapters = item['chapters']
        if not isinstance(item['chapters'], list):
            chapters = [item['chapters']]
        for chapter in chapters:
            tmp_item['chapters'].append({
                'chapter_id': int(chapter['chapter_id']),
                'chapter_name': chapter['chapter_name'],
                'book_id': int(chapter['book_id']),
                'volume_id': int(chapter['volume_id']),
                'word_count': int(chapter['word_count']),
                'order_num': chapter['order_num'],
                'create_time': datetime.datetime.fromtimestamp(int(chapter['create_time'])).__str__(),
                'update_time': datetime.datetime.fromtimestamp(int(chapter['update_time'])).__str__(),
            })
        datas.append(tmp_item)
    return json.dumps({'code': 0, 'data': datas})


def get_chapter_content(book_id, chapter_id):
    ''' 获取书籍章节内容'''
    url = 'http://api.open.book.sina.com.cn/cpoutput/%s/chapter_content?book_id=%s&chapter_id=%s&sign=%s' \
          % (CP_NAME, book_id, chapter_id, get_sign())
    resp = session.get(url)
    # print 'get_chapters, result is', resp.text
    resp_data = xmltodict.parse(resp.text.encode('utf8'))
    result = resp_data['root']['result']

    # 异常状态处理
    if result['status']['code'] != '0':
        return json.dumps({'code': -1, 'msg': result['status']['msg']})

    # 成功状态处理
    item = result['data']
    data = {
        'id': item['id'],
        'book_id': int(item['book_id']),
        'chapter_id': int(item['chapter_id']),
        'content': item['content'],
    }
    return json.dumps({'code': 0, 'data': data})


if __name__ == '__main__':
    pass
    # print get_book_list()
    # print get_book_info(153920)
    # print get_chapters(205771)
    # import time
    # t1 = time.time()
    # print get_chapter_content(153920, 1242)
    # t2 = time.time()
    # print t2-t1
