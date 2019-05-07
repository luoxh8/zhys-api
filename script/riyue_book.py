# -*- coding: utf-8 -*-
"""
Doc: 日月 

Created on 
@author:  
"""
import hashlib

from base_spider import BaseBookSpider


class RiyueBookSpider(BaseBookSpider):
    """日月"""
    CHANNEL_NAME = 'riyue'
    #CLIENT_ID = '46'
    #SECRET = 'e99d99201aac1c7313c99171e721d3a8'

    def __init__(self):
        self.chapter_num_dict = {}  # 保存书籍章节数量

    def req_api(self, url, **kwargs):
        url = 'http://www.riyuezw.com' + url
        #kwargs['clientId'] = self.CLIENT_ID
        #kwargs['resType'] = 'json'
        return self.req(url, **kwargs)
    
    def get_time(self, t):
        import time
        time_s = time.mktime(time.strptime(t, '%Y%m%d%H%M%S'))
        time_local = time.localtime(time_s)
        my_time = time.strftime("%Y-%m-%d %H:%M:%S",time_local)
        return my_time

    def get_book_list(self, local_cate_dict):
        """获取书籍列表"""
        ret = self.req_api('/api/koudai/get_book_list.php').json()
        if not ret:
            return []

        data = ret

        # 获取本地已有分类
        book_list = []
        for _book in data:
            book_id = int(_book['articleid'])
            ret = self.req_api('/api/koudai/get_book_info.php', aid=book_id).json()
            if not ret:
                continue
            book = ret
            cate_id = local_cate_dict.get(book['sort'].encode('utf8')) or local_cate_dict.get('其他')
            if not cate_id:
                cate_id = 3024
                print '!!!!NO cate_id: ', book
                #continue
            create_time = self.get_time(book['postdate'])
            update_time = self.get_time(book['lastupdate'])

            book_list.append(dict(book_id=book_id,
                                  book_name=book['articlename'],
                                  cate_id=cate_id,
                                  channel_type=1,
                                  author_name=book['author'],
                                  chapter_num=book['chapters'],
                                  is_publish=2,
                                  status=(1 if book['fullflag'] else 2),
                                  create_time=create_time,
                                  cover=book['cover'],
                                  intro=book['intro'],
                                  word_count=int(book['words']),
                                  source=self.CHANNEL_NAME,
                                  update_time=update_time))
        return book_list

    def get_volume_chapter_list(self, channel_book_id, max_cid, local_book_id):
        """获取卷和章节列表"""
        data = self.req_api('/api/koudai/get_chapter_list.php', aid=channel_book_id).json()
        if not data:
            return [], []

        volume_list = []
        chapter_list = []
        for chap in data:
            chapter_id = int(chap['chapterid'])
            if chapter_id <= max_cid:
                continue
            chap_detail = self.req_api('/api/koudai/get_chapter_content.php', aid=channel_book_id,
                                       chapterid=chapter_id).json()

            chapter_list.append({
                'book_id': local_book_id,
                'volume_id': 0,
                'volume_name': '',
                'chapter_id': chapter_id,
                'chapter_name': chap_detail['chaptername'],
                'word_count': chap_detail['words'],
                'create_time': self.get_time(chap_detail['postdate']),
                'update_time': self.get_time(chap_detail['lastupdate']),
                'content': chap_detail['content']
            })
        self.chapter_num_dict[channel_book_id] = len(data) if data else 0
        return volume_list, chapter_list

    def need_update_chap_num(self):
        return False

    def get_chap_num(self, channel_book_id):
        return self.chapter_num_dict.get(channel_book_id, 0)

if __name__ == '__main__':
    spider = RiyueBookSpider()
    _book_list = spider.get_book_list({'其他': 1})
    import json
    print json.dumps(_book_list)
    print '==========================='
    for book_ in _book_list:
        v_l, c_l = spider.get_volume_chapter_list(book_['book_id'], 0, 0)
        print v_l
        open('tmp.txt', 'a').write(json.dumps(c_l))
        break
