# -*- coding: utf-8 -*-
"""
Doc: 
Created by MT at 2017/10/13
"""
import hashlib

from lib import utils
from models import Book, BookVolume, BookChapters, BookChapterContent
from models import db
from models.book import BookCategory


class BookUpdater():
    """书籍更新类"""

    def __init__(self, spider_class):
        """
        :param spider_class: 具体渠道爬虫类
        """
        self.spider = spider_class()

    def get_local_img_url(self, filename):
        with open(filename, 'r') as f:
            m2 = hashlib.md5()
            m2.update(filename.encode('utf-8'))
            name = m2.hexdigest()[:8] + filename[-4:]
            img_url = utils.upload_img(name, f.read())
            return img_url

    def pull_book(self):
        """拉取最新书籍信息"""
        local_cate_dict = {cate.cate_name.encode('utf8'): cate.cate_id for cate in BookCategory.query.all()}
        book_list = self.spider.get_book_list(local_cate_dict)
        # print local_cate_dict
        print "book num:", len(book_list)
        if not book_list:
            return

        # 取本地书籍对应最新章节id 卷id 更新时间
        local_latest_books = self.get_local_book_latest()
        for book in book_list:
            channel_book_id = book['book_id']
            bind_book_id = self.spider.gen_channel_bind_id(book['book_id'])
            book['channel_book_id'] = bind_book_id
            local_book = local_latest_books.get(bind_book_id, {})
            if not local_book:
                if self.spider.CHANNEL_NAME == 'feilang':
                    book['cover'] = self.get_local_img_url(book['cover'])
                book_m = Book(book)
                book_m.word_count = 0
                db.session.add(book_m)
                db.session.commit()

                # 增加章节
                local_book = {'book_id': book_m.book_id}
                self.update_volume_chapter(book['book_id'], local_book)

                book_m.word_count = book['word_count']
                if self.spider.CHANNEL_NAME in ['feilang', 'lizhi']:
                    book_m.cover = self.get_local_img_url(book_m.cover)
                else:
                    book_m.cover = utils.upload_img_by_url('book_cover_%s' % book_m.book_id, book_m.cover)
                if self.spider.need_update_chap_num():
                    book_m.chapter_num = self.spider.get_chap_num(channel_book_id)
            else:
                # 书籍信息不包含章节数量的情况
                if self.spider.need_update_chap_num():
                    book['chapter_num'] = local_book['chapter_num']
                if book['word_count'] > local_book['word_count'] or \
                        book['update_time'] > local_book['update_time']:
                    # 更新章节
                    self.update_volume_chapter(book['book_id'], local_book)
                    if self.spider.need_update_chap_num():
                        book['chapter_num'] = self.spider.get_chap_num(channel_book_id)

                # 更新书籍
                book['book_id'] = local_book['book_id']

                if self.spider.CHANNEL_NAME in ['feilang', 'lizhi']:
                    book['cover'] = self.get_local_img_url(book['cover'])
                else:
                    book['cover'] = utils.upload_img_by_url('book_cover_%s' % book['book_id'], book['cover'])

                if book['word_count'] == 0:
                    book['word_count'] = local_book['word_count']
                _update_book(book)
            try:
                db.session.commit()
                self.spider.finish_callback()
            except Exception as e:
                print e
                db.session.rollback()

    def update_volume_chapter(self, real_book_id, local_book):
        """更新卷章节"""
        local_book_id = local_book['book_id']
        max_cid = local_book.get('max_cid', 0)
        volume_list, chapter_list = self.spider.get_volume_chapter_list(real_book_id, max_cid, local_book_id)
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

    def get_local_book_latest(self):
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
        ''' % self.spider.CHANNEL_NAME).fetchall()
        print '查询时间', time.time() - t1
        local_latest_books = {b.channel_book_id: {"max_vid": int(b.volume_id or 0),
                                                  "max_cid": int(b.chapter_id or 0),
                                                  "book_id": int(b.book_id),
                                                  "update_time": b.update_time.__str__(),
                                                  "word_count": int(b.word_count),
                                                  "chapter_num": int(b.chapter_num)} for b in local_latest_books}
        print "local_latest_books: ", local_latest_books
        return local_latest_books


def _update_book(data):
    """更新书籍信息"""
    db.session.execute('''
UPDATE book
SET
  book_name    = :book_name,
  author_name  = :author_name,
  chapter_num  = :chapter_num,
  status       = :status,
  intro        = :intro,
  cover        = :cover,
  word_count   = :word_count,
  update_time  = :update_time
WHERE book_id = :book_id''', {
        "book_name": data['book_name'],
        "author_name": data['author_name'],
        "chapter_num": data['chapter_num'],
        "status": data['status'],
        "intro": data['intro'],
        "cover": data['cover'],
        "word_count": int(data['word_count']),
        "update_time": data['update_time'],
        "book_id": data['book_id'],
    })
