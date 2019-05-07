# -*- coding: utf-8 -*-
"""
Doc: 礼智 

Created on 2017/11/7
@author: wzq 
"""
import os
import codecs
import hashlib
import datetime
import ujson as json
from qiniu import Auth, put_data
#from lib import utils
import copy
from lxml import etree
import xlrd

from base_spider import BaseBookSpider


class LizhiBookSpider(BaseBookSpider):
    """礼智"""
    CHANNEL_NAME = 'lizhi'
    start_book_id = 1500
    xls_book = {} # 保存xls文件里书籍的信息
    prefix = 'script'
    cover_files = []
    content_files = []

    def set_cover_files(self):
        self.cover_files =  os.listdir('/data/novel_datas/lizhi/cover')

    def set_content_files(self):
        self.content_files =  os.listdir('/data/novel_datas/lizhi/word')

    def get_cover(self, book_id):
        _id = book_id - self.start_book_id
        filename = '%03d.jpg' %(_id)
        if filename in self.cover_files:
            return '/data/novel_datas/lizhi/cover/%s' %(filename)
        else:
            return '/data/novel_datas/lizhi/cover/default.jpg' 

    def get_book_id(self, filename):
        end_num = 0
        for i, c in enumerate(filename):
            if c not in '1234567890':
                end_num = i
                break
        book_id = filename[:end_num].strip()
        return int(book_id) if book_id else 0


    def get_content_file(self, book_id):
        _id = book_id - self.start_book_id
        for filename in self.content_files:
            if self.get_book_id(filename) == _id:
                return '/data/novel_datas/lizhi/word/%s' %(filename)
        return '' 
       
    def set_xls_book(self):
        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        data = xlrd.open_workbook('/data/novel_datas/lizhi/lizhi.xls')
        table = data.sheets()[0]
        for row in xrange(1,table.nrows):
            values = table.row_values(row)
            book_id = int(values[0]) + self.start_book_id
            self.xls_book[book_id] = {}
            self.xls_book[book_id]['book_name'] = values[1]
            self.xls_book[book_id]['author_name'] = values[2]
            self.xls_book[book_id]['word_count'] = int(values[3])
            self.xls_book[book_id]['create_time'] = values[4] if values[4] else now
            self.xls_book[book_id]['update_time'] = values[5] if values[5] else now
            self.xls_book[book_id]['status'] = 1 if u'完本' in values[7] else 2
            self.xls_book[book_id]['intro'] = values[10]
            self.xls_book[book_id]['cover'] = self.get_cover(book_id)
            self.xls_book[book_id]['content_file'] = self.get_content_file(book_id)
            self.xls_book[book_id]['chapters'] = self.get_chapters(book_id)


    def get_chapters(self, book_id):
        filename = self.xls_book[book_id]['content_file']
        if not filename:
            return []
        chapter_list=[]
        with codecs.open(filename, "r", "utf-8") as f:
            text = f.read()
            html = etree.HTML(text)
            result = html.xpath('//h2')
            for i, r in enumerate(result):
                data = {}
                content = r.getnext()
                if content is None:
                    continue
                content_text = ''
                for item in content:
                    if item.text and item.tag != 'style':
                        content_text += item.text
                if content_text != '':
                    data['chapter_id'] = i
                    data['chapter_name'] = r.text.strip()
                    data['content'] = content_text
                    chapter_list.append(data)
        return chapter_list


    def __init__(self):
        self.chapter_num_dict = {}  # 保存书籍章节数量
        self.set_cover_files()
        self.set_content_files()
        self.set_xls_book()

        #for key in self.xls_book:
        #    if not self.xls_book[key]['content_file']:
        #        print key
        #        print self.xls_book[key]['cover']
        #        print self.xls_book[key]['content_file']

    def get_book_list(self, local_cate_dict):
        """获取书籍列表"""
        if not self.xls_book:
            return []

        # 获取本地已有分类
        book_list = []
        for book_id in self.xls_book:
            book = self.xls_book[book_id]
            cate_id = local_cate_dict.get('其他')
            if not cate_id:
                print '!!!!NO cate_id: ', book
                continue
            book_list.append(dict(
                                  book_id=book_id,
                                  book_name=book['book_name'],
                                  cate_id=cate_id,
                                  channel_type= 1,
                                  author_name=book['author_name'],
                                  chapter_num=len(book['chapters']),
                                  is_publish=2,
                                  status=book['status'],
                                  create_time=book['create_time'],
                                  cover=book['cover'],
                                  intro=book['intro'],
                                  word_count=book['word_count'],
                                  source=self.CHANNEL_NAME,
                                  update_time=book['update_time'],
                            )
            )
        return book_list

    def get_volume_chapter_list(self, channel_book_id, max_cid, local_book_id):
        """获取卷和章节列表"""
        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        if not self.xls_book.get(channel_book_id):
            return [], []

        data = self.xls_book[channel_book_id]['chapters']
        volume_list = []
        chapter_list = []
        for chap in data:
            chapter_list.append({
                'book_id': local_book_id,
                'volume_id': 0,
                'volume_name': '',
                'chapter_id': chap['chapter_id'],
                'chapter_name': chap['chapter_name'],
                'word_count': cal_word_count(chap['content']),
                'create_time': now,
                'update_time': now,
                'content': chap['content']
            })
        self.chapter_num_dict[channel_book_id] = int(data[-1]['chapter_id']) if data else 0
        print 'get_volume_chapter_list', len(chapter_list)
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
    spider = LizhiBookSpider()
    #_book_list = spider.get_book_list({'其他': 1})
    #import json
    #print json.dumps(_book_list)
    #print '==========================='
    #for book_ in _book_list:
    #    v_l, c_l = spider.get_volume_chapter_list(book_['book_id'], 0, 0)
    #    print json.dumps({'code': 0, 'data':c_l[:1]})
        #print json.dumps({'code': 0, 'data':c_l[:1] + c_l[30:31]})
    #    open('tmp.txt', 'w').write(json.dumps(c_l))
    #    break

    #with codecs.open("/data/novel_datas/lizhi/word/200媚朝纲：庶女毒心.doc", "r", "utf-8") as f:
    #    text = f.read()
    #    html = etree.HTML(text)
    #    result = html.xpath('//h2')
    #    chapter_list=[]
    #    for i, r in enumerate(result):
    #        data = {}
    #        content = r.getnext()
    #        content_text = ''
    #        for item in content:
    #            if item.text and item.tag != 'style':
    #                content_text += item.text
    #        if content_text != '':
    #            data['title'] = r.text.strip()
    #            data['content'] = content_text
    #            print i
    #            print 'title:------', data['title']
    #            print 'content:------', data['content'][:10]
    #        if i > 200:
    #            break
    #data = xlrd.open_workbook('/data/novel_datas/lizhi/lizhi.xls')
    #table = data.sheets()[0]
    #print table.nrows
    #for row in xrange(1,table.nrows):
    #    print 'row-----:', row
    #    values = table.row_values(row)
    #    #if values:
    #    print 'value-----:', values[0]

        #contents = html.xpath('//pre')
        #content_list = []
        #for content in contents:
        #    print dir(content)
        #    break
            #content_text = []
            #for item in content:
            #    if item.text and item.tag != 'style':
            #        content_text.append(item.text)
            #print dir(content)
            #content_list.append(''.join(content_text))
        #    for b in content:
        #        if b.text and len(b.text) > 1:
        #            print b.text
        #            content_list.append(b.text)
        #    if len(content_list) == 2:
        #        break
        #tmp_list = title_list[len(title_list)-len(content_list):]
        #for i, tmp in enumerate(tmp_list):
        #    print tmp
        #    print content_list[i][:10]
    #files =  os.listdir('/data/novel_datas/lizhi/cover')
    #help(os.listdir)
    #cover_files = [f for f in files]
    #print cover_files
