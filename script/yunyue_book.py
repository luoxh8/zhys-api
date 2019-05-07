# -*- coding: utf-8 -*-
"""
Doc: 云阅 

Created on 2017/10/20
@author: wzq 
"""
import hashlib
import xmltodict
import datetime
import ujson as json

from base_spider import BaseBookSpider


class YunyueBookSpider(BaseBookSpider):
    """掌阅"""
    CHANNEL_NAME = 'yunyue'
    appid = '641cacd8-af0a-4987-9285-200ed4733b95'

    def __init__(self):
        self.chapter_num_dict = {}  # 保存书籍章节数量

    def req_api(self, path, **kwargs):
        url = 'http://output.91yunyue.com/getresource.svd' + path 
        return self.req(url, **kwargs)

    def confir(self, text):
        """过滤不可见字符"""
        for i in range(0,32):
            if i not in (10, 13):
                text = text.replace(chr(i),'')
        return  text 

    def get_books_data(self):
        text = self.req_api('', domain='getyunyuebooklist', appid=self.appid).text
        text = text[text.find('<books>'):text.find('</books>') + 8]
        text = self.confir(text)
        parse_data = xmltodict.parse(text)
        return parse_data['books']['book']
        
    def get_book_info(self, book_id):
        text = self.req_api('', domain='getyunyuebookinfo', appid=self.appid, bookid=book_id).text
        text = text[text.find('<book>'):text.find('</book>') + 7]
        text = self.confir(text)
        parse_data = xmltodict.parse(text)
        return parse_data['book']
        
    def get_book_list(self, local_cate_dict):
        """获取书籍列表"""
        data = self.get_books_data()

        if not data:
            return []

        # 获取本地已有分类
        book_list = []
        for _book in data:
            book_id = int(_book['id'])
            book = self.get_book_info(book_id)
            cate_id = local_cate_dict.get('其他')
            if not cate_id:
                print '!!!!NO cate_id: ', book
                continue
            book_list.append(dict(book_id=book_id,
                                  book_name=book['title'],
                                  cate_id=cate_id,
                                  channel_type= 1 if int(book['channel']) == 0 else 3,
                                  author_name=book['author'],
                                  chapter_num=0,
                                  is_publish=2,
                                  status=(1 if int(book['isFull']) == 1 else 2),

                                  create_time=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),#book['createTime'],
                                  cover=book['cover'],
                                  intro=book['summary'],
                                  word_count=0,#int(book['wordCount']),
                                  source=self.CHANNEL_NAME,
                                  update_time=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),))#book['createTime']))
        return book_list

    def get_chapter_content(self, book_id, chapter_id):
        text = self.req_api('', domain='getyunyuechaptercontent', appid=self.appid, bookid=book_id, chapterid=chapter_id).text

        text = text[text.find('<content>'):text.find('</content>') + len('</content>')]
        return self.get_xml_content(text)
    
    def get_xml_content(self, xml_text):
        try:
            text = xml_text.replace('^^', '')
            parse_data = xmltodict.parse(text)
            return parse_data['content']
        except:
            try:
                with open('yunyue.error.log', 'w') as f:
                    f.write('11111111')
                text = confir(xml_text)
                parse_data = xmltodict.parse(text)
                return parse_data['content']
            except:
                with open('yunyue.error.log', 'w') as f:
                    f.write('22222222')
                return xml_text[xml_text.find('<content>') + len('<content>'):xml_text.find('</content>')]

    def get_volume_chapter_list(self, channel_book_id, max_cid, local_book_id):
        """获取卷和章节列表"""
        text = self.req_api('', domain='getyunyuechapterlist', appid=self.appid, bookid=channel_book_id).text
        text = text[text.find('<chapters>'):text.find('</chapters>') + len('</chapters>')]
        text = self.confir(text)
        parse_data = xmltodict.parse(text)
        data = parse_data['chapters']['chapter']


        if not data:
            return [], []

        volume_list = []
        chapter_list = []
        for chap in data:
            chapter_id = int(chap['id'])
            if chapter_id <= max_cid:
                continue
            content = self.get_chapter_content(channel_book_id, chapter_id)

            chapter_list.append({
                'book_id': local_book_id,
                'volume_id': 0,
                'volume_name': '',
                'chapter_id': chapter_id,
                'chapter_name': chap['title'],
                'word_count': chap['chapterLength'],
                'create_time': chap['updatetime'],
                'update_time': chap['updatetime'],
                'content': content 
            })
        self.chapter_num_dict[channel_book_id] = int(data[-1]['chapterOrder']) if data else 0
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
    spider = YunyueBookSpider()
    _book_list = spider.get_book_list({'其他': 1})
    #import json
    #print json.dumps(_book_list)
    #print '==========================='
    for book_ in _book_list:
        v_l, c_l = spider.get_volume_chapter_list(book_['book_id'], 0, 0)
        print json.dumps({'code': 0, 'data':v_l[:10]})
        #print json.dumps({'code': 0, 'data':c_l[:1] + c_l[30:31]})
#        open('tmp.txt', 'w').write(json.dumps(c_l))
        break
