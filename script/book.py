# coding=utf-8
import random
import logging
import ujson as json
from lib import sina 
from models import db
from models import BookCategory, Book, BookVolume, BookChapters, BookChapterContent


logger = logging.getLogger("book")
logger.setLevel(logging.INFO)

handler = logging.FileHandler("log/book.log")
formatter = logging.Formatter("[%(asctime)s] %(levelname)s %(funcName)s # %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)



def add_book_category():
    categorys = [(1001, u'武侠仙侠'),
                 (1002, u'玄幻奇幻'),
                 (1003, u'网游竞技'),
                 (1004, u'都市异能'),
                 (1005, u'都市生活'),
                 (1006, u'悬疑灵异'),
                 (1007, u'悬疑推理'),
                 (1008, u'科幻探险'),
                 (1009, u'灵异奇谈'),
                 (1010, u'热血都市'),
                 (1011, u'抗战烽火'),
                 (1012, u'现代修真'),
                 (1013, u'奇幻修真'),
                 (1014, u'商战职场'),
                 (1015, u'谍战特工'),    
                 (1016, u'历史军事'),
                 (1017, u'军事战争'),
                 (1018, u'虚拟游戏'),
                 (1019, u'末世危机'),
                 (1020, u'寻墓探险'),
                 (1021, u'恐怖惊悚'),
                 (1022, u'历史架空'),
                 (2001, u'青春文学'),
                 (2002, u'心灵鸡汤'),
                 (2003, u'职场商战'),
                 (2004, u'影视娱乐'),
                 (2005, u'言情小说'),
                 (2006, u'现代都市'),
                 (2007, u'经管理财'),
                 (2008, u'历史风云'),
                 (2009, u'悬疑灵异'),
                 (2010, u'铁血军事'),
                 (2011, u'生活休闲'),
                 (2012, u'励志成功'),
                 (2013, u'官场沉浮'),
                 (2014, u'奇幻科幻'),
                 (2015, u'武侠仙侠'),
                 (3001, u'青春校园'),
                 (3002, u'豪门总裁'),
                 (3003, u'穿越架空'),
                 (3004, u'婚恋情感'),
                 (3005, u'公闱宅斗'),
                 (3006, u'幻想异能'),
                 (3007, u'重生种田'),
                 (3008, u'浪漫纯爱'),
                 (3009, u'古言架空'),
                 (3010, u'民国情缘'),
                 (3011, u'娱乐明星'),
                 (3012, u'女尊王朝'),
                 (3013, u'现代言情'),
                 (3014, u'同人美文'),
                 (3015, u'武侠仙侠'),
                 ]
    for cate in categorys:
        db.session.add(BookCategory(cate[0], cate[1]))

    db.session.commit()
    return 'add_book_category() is ok.'

def add_book_volume(data):
    bv = BookVolume.query.filter_by(book_id=data['book_id'], volume_id=data['volume_id']).first()
    if not bv:
        db.session.add(BookVolume(data))
    else:
        bv.update(data)
        db.session.add(bv)

def add_book_volumes(book_id):
    ret = json.loads(sina.get_chapters(book_id))
    if ret['code'] == 0:
        for data in ret['data']:
            add_book_volume(data)
            for chapter in data['chapters']:
                add_book_chapters(chapter)


def add_book_chapters(chapter):
    book_id = chapter['book_id']
    volume_id = chapter['volume_id']
    chapter_id = chapter['chapter_id']
    bc = BookChapters.query.filter_by(book_id=book_id, 
                                      volume_id=volume_id,
                                      chapter_id=chapter_id).first()
    if not bc:
        db.session.add(BookChapters(chapter))

    ret = json.loads(sina.get_chapter_content(book_id, chapter_id))
    if ret['code'] == 0:
        ret['data']['volume_id'] = volume_id
        bcc = BookChapterContent.query.filter_by(book_id=book_id,
                                                 volume_id=volume_id,
                                                 chapter_id=chapter_id).first()
        if not bcc:
            db.session.add(BookChapterContent(ret['data']))
        else:
            bcc.update(ret['data'])
            db.session.add(bcc)
    db.session.commit()



def add_book(data):
    book = Book.query.filter_by(book_id=int(data['book_id'])).first()
    if not book:
        db.session.add(Book(data))
    else:
        book.update(data)
        db.session.add(book)

def add_books():
    ret = json.loads(sina.get_book_list())
    if ret['code'] == 0:
        for d in ret['data']:
            r = json.loads(sina.get_book_info(d['book_id']))
            if r['code'] == 0:
                add_book(r['data'])
                add_book_volumes(d['book_id'])

    db.session.commit()


def start():
    #logger.info(add_book_category())
    add_books()
