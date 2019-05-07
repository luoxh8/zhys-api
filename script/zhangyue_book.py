# -*- coding: utf-8 -*-
"""
Doc: 掌阅

Created on 2017/9/27
@author: MT
"""
import hashlib

from base_spider import BaseBookSpider


class ZhangyueBookSpider(BaseBookSpider):
    """掌阅"""
    CHANNEL_NAME = 'zhangyue'
    CLIENT_ID = '46'
    SECRET = 'e99d99201aac1c7313c99171e721d3a8'

    def __init__(self):
        self.chapter_num_dict = {}  # 保存书籍章节数量

    def req_api(self, url, **kwargs):
        url = 'http://api.res.ireader.com' + url
        kwargs['clientId'] = self.CLIENT_ID
        kwargs['resType'] = 'json'
        return self.req(url, **kwargs)

    def get_sign(self, *args):
        """计算签名"""
        sign_args = [self.CLIENT_ID, self.SECRET]
        for i in args:
            sign_args.append(str(i))
        return hashlib.md5(''.join(sign_args)).hexdigest().lower()

    def get_book_list(self, local_cate_dict):
        """获取书籍列表"""
        data = self.req_api('/api/v2/book/bookList', sign=self.get_sign()).json()
        if not data:
            return []

        # 获取本地已有分类
        book_list = []
        for _book in data:
            book_id = int(_book['bookId'])
            book = self.req_api('/api/v2/book/bookInfo', bookId=book_id, sign=self.get_sign(book_id)).json()
            cate_id = local_cate_dict.get(book['category'].encode('utf8')) or local_cate_dict.get('其他')
            if not cate_id:
                print '!!!!NO cate_id: ', book
                continue
            book_list.append(dict(book_id=book_id,
                                  book_name=book['displayName'],
                                  cate_id=cate_id,
                                  channel_type=1,
                                  author_name=book['author'],
                                  chapter_num=0,
                                  is_publish=2,
                                  status=(1 if book['completeStatus'] == 'Y' else 2),
                                  create_time=book['createTime'],
                                  cover=book['cover'],
                                  intro=book['brief'],
                                  word_count=int(book['wordCount']),
                                  source=self.CHANNEL_NAME,
                                  update_time=book['createTime']))
        return book_list

    def get_volume_chapter_list(self, channel_book_id, max_cid, local_book_id):
        """获取卷和章节列表"""
        data = self.req_api('/api/v2/book/chapterList', bookId=channel_book_id,
                            sign=self.get_sign(channel_book_id)).json()
        if not data:
            return [], []

        volume_list = []
        chapter_list = []
        for chap in data:
            chapter_id = int(chap['chapterId'])
            if chapter_id <= max_cid:
                continue
            chap_detail = self.req_api('/api/v2/book/chapterInfo', bookId=channel_book_id,
                                       chapterId=chapter_id, sign=self.get_sign(channel_book_id, chapter_id)).json()

            chapter_list.append({
                'book_id': local_book_id,
                'volume_id': 0,
                'volume_name': '',
                'chapter_id': chapter_id,
                'chapter_name': chap_detail['title'],
                'word_count': cal_word_count(chap_detail['content']),
                'create_time': chap_detail['createTime'],
                'update_time': chap_detail['createTime'],
                'content': chap_detail['content']
            })
        self.chapter_num_dict[channel_book_id] = data[-1]['chapterOrder'] if data else 0
        return volume_list, chapter_list

    def need_update_chap_num(self):
        return True

    def get_chap_num(self, channel_book_id):
        return self.chapter_num_dict.get(channel_book_id, 0)


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


if __name__ == '__main__':
    spider = ZhangyueBookSpider()
    _book_list = spider.get_book_list({'其他': 1})
    import json
    print json.dumps(_book_list)
    print '==========================='
    for book_ in _book_list:
        v_l, c_l = spider.get_volume_chapter_list(book_['book_id'], 0, 0)
        print v_l
        open('tmp.txt', 'a').write(json.dumps(c_l))
        break
