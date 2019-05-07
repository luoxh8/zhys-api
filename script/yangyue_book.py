# -*- coding: utf-8 -*-
"""
Doc: 阳光阅读 

Created on 2017/10/20
@author: wzq 
"""
import hashlib

from base_spider import BaseBookSpider


class YangyueBookSpider(BaseBookSpider):
    """掌阅"""
    CHANNEL_NAME = 'yangyue'


    def __init__(self):
        self.chapter_num_dict = {}  # 保存书籍章节数量

    def req_api(self, url, **kwargs):
        url = 'http://www.ygread.com' + url
        return self.req(url, **kwargs)

    def get_book_list(self, local_cate_dict):
        """获取书籍列表"""
        ret = self.req_api('/Interface/Koudai/booklist').json()
        if not ret or ret['code'] != 200:
            return []

        data = ret['data']

        # 获取本地已有分类
        book_list = []
        for _book in data:
            book_id = int(_book['bookid'])
            ret = self.req_api('/Interface/Koudai/books', bookid=book_id).json()
            if not ret or (ret['code'] != 200):
                continue
            book = ret['data']
            cate_id = local_cate_dict.get('其他')
            print cate_id
            if not cate_id:
                continue
            book_list.append(dict(book_id=book_id,
                                  book_name=book['bookname'],
                                  cate_id=cate_id,
                                  channel_type= int(book['gender']),
                                  author_name=book['pen_name'],
                                  chapter_num=0,
                                  is_publish=2,
                                  status= int(book['status']),
                                  create_time=book['creat_time'],
                                  cover=book['cover'],
                                  intro=book['intro'],
                                  word_count=int(book['words']),
                                  source=self.CHANNEL_NAME,
                                  update_time=_book['lastupdatetime']))
        return book_list

    def get_volume_chapter_list(self, channel_book_id, max_cid, local_book_id):
        """获取卷和章节列表"""
        data = self.req_api('/Interface/Koudai/chapterlist', bookid=channel_book_id).json()
        if not data or data['code'] != 200:
            return [], []
        
        data = data['data']['chapters']
        volume_list = []
        chapter_list = []
        for chap in data:
            chapter_id = int(chap['chapterid'])
            if chapter_id <= max_cid:
                continue
            chap_detail = self.req_api('/Interface/Koudai/content', bookid=channel_book_id,
                                       chapterid=chapter_id).json()

            chapter_list.append({
                'book_id': local_book_id,
                'volume_id': 0,
                'volume_name': '',
                'chapter_id': chapter_id,
                'chapter_name': chap['chapter_name'],
                'word_count': int(chap['number']),
                'create_time': chap['updatetime'],
                'update_time': chap['updatetime'],
                'content': chap_detail['content']
            })
        self.chapter_num_dict[channel_book_id] = data[-1]['chapter_order'] if data else 0
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
    spider = YangyueBookSpider()
    _book_list = spider.get_book_list({'其他': 1})
    import json
    #print json.dumps(_book_list)
    print '==========================='
    for book_ in _book_list:
        v_l, c_l = spider.get_volume_chapter_list(book_['book_id'], 0, 0)
        print v_l
        open('tmp.txt', 'a').write(json.dumps(c_l))
    #    break
