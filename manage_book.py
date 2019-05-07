# coding=utf-8

from flask_script import Manager

from wsgi_api import app
import time
import random
import string
import requests
import xmltodict
from models import db
from models import Book
from models import BookShelf
from models import BookChapters
from models import BookChapterContent
from models import ChannelType
from models import ChannelData


manager = Manager(app)


@manager.command
def book():
    # 逻辑导入部分开始
    from script import book
    book.start()


@manager.option('-c', '--channel', dest='channel', default='')
def update_book(channel):
    import datetime
    print 'Start:', datetime.datetime.now()
    from script.base_book import BookUpdater
    channel = channel.lower()
    channel_class = getattr(getattr(__import__('script.%s_book' % channel), '%s_book' % channel), '%sBookSpider' % channel.capitalize())
    if not channel_class:
        print 'book channel not exist!'
        return
    updater = BookUpdater(channel_class)
    updater.pull_book()
    print 'End:', datetime.datetime.now()


@manager.command
def update_sina_book():
    from script import update_book
    update_book.start()


@manager.command
def update_kaixing_book():
    from script import kaixing_book
    import datetime
    print 'Start:', datetime.datetime.now()
    kaixing_book.pull_book()
    print 'End:', datetime.datetime.now()


@manager.command
def update_anzhi_book():
    from script import anzhi_book
    import datetime
    print 'Start:', datetime.datetime.now()
    anzhi_book.pull_book()


@manager.command
def update_jingyu_book():
    import datetime
    print 'Start:', datetime.datetime.now()
    from script import jingyu_book
    jingyu_book.pull_book()
    print 'End:', datetime.datetime.now()


@manager.command
def update_category_book():
    import datetime
    print 'Start:', datetime.datetime.now()
    from script import update_category
    update_category.update_book_category()
    print 'End:', datetime.datetime.now()


@manager.command
def update_category():
    import datetime
    print 'Start:', datetime.datetime.now()
    from script import update_category
    update_category.update_category()
    print 'End:', datetime.datetime.now()


@manager.command
def update_book_cover():
    """更新书籍封面为七牛地址"""
    from models import db
    from lib.utils import upload_img_by_url
    query = db.session.execute('select cover, book_id from book').fetchall()
    update_list = []
    for book in query:
        if book.cover.startswith('http://ov2eyt2uw.bkt.clouddn.com'):
            continue
        new_cover = upload_img_by_url('book_cover_%s' % book.book_id, book.cover)
        print book, new_cover
        if new_cover != book.cover:
            update_list.append({'book_id': book.book_id, 'cover': new_cover})
    db.session.execute('update book set cover=:cover where book_id=:book_id', update_list)
    db.session.commit()


@manager.command
def fix_book_cover():
    """更新书籍封面为七牛地址"""
    from models import db
    import requests
    from lib.utils import upload_img_by_url
    query = db.session.execute('select cover, book_id from book where book_id>5483665').fetchall()
    update_list = []
    for book in query:
        if not book.cover:
            continue
        try:
            resp = requests.head(book.cover, timeout=1)
            if resp.headers.get('content-type') == 'text/html':
                print resp.headers.get('content-type'), book.cover
                update_list.append({'book_id': book.book_id, 'cover': ''})
            else:
                if book.cover.startswith('http://ov2eyt2uw.bkt.clouddn.com'):
                    continue
                new_cover = upload_img_by_url('book_cover_%s' % book.book_id, book.cover)
                print book, new_cover
                if new_cover != book.cover:
                    update_list.append({'book_id': book.book_id, 'cover': new_cover})

        except Exception, e:
            print "timeout", book.cover, e
            continue

        if len(update_list) >= 100:
            db.session.execute('update book set cover=:cover where book_id=:book_id', update_list)
            db.session.commit()
            update_list = []

    if update_list:
        db.session.execute('update book set cover=:cover where book_id=:book_id', update_list)
        db.session.commit()


@manager.command
def fix_dup_book():
    """修复重复书籍"""
    from models import db
    book_group = db.session.execute('select book_id, book_name, author_name from book where free_collect=1').fetchall()
    book_dict = {}
    delete_books = []
    update_books = []
    for book in book_group:
        book_key = book.book_name + book.author_name
        if book_key not in book_dict:
            book_dict[book_key] = book
            continue

        old_book = book_dict[book_key]
        if book.book_name == old_book.book_name and book.author_name == old_book.author_name:
            delete_books.append({'book_id': book.book_id})
            update_books.append({'book_id': book.book_id, 'new_book_id': old_book.book_id})

    db.session.execute('update free_book set book_id=:new_book_id where book_id=:book_id', update_books)
    db.session.execute('update book_chapters set book_id=:new_book_id where book_id=:book_id', update_books)
    db.session.execute('delete from book where book_id=:book_id', delete_books)
    db.session.commit()


@manager.command
def remove_dup_free_book():
    """下架正版已有的免费书籍"""
    from models import db
    book_group = db.session.execute(
        'select book_name, author_name from book where free_collect=0').fetchall()
    book_set = {book.book_name + book.author_name for book in book_group}
    delete_books = []
    free_book_group = db.session.execute(
        'select book_id, book_name, author_name from book where free_collect=1').fetchall()
    for book in free_book_group:
        book_key = book.book_name + book.author_name
        if book_key not in book_set:
            continue
        delete_books.append({'book_id': book.book_id})
        print book.book_name, book.author_name, book.book_id

    db.session.execute('update book set showed=0 where book_id=:book_id', delete_books)
    # db.session.execute('delete from book where book_id=:book_id', delete_books)
    # db.session.execute('delete from free_book where book_id=:book_id', delete_books)
    # db.session.execute('delete from book_chapters where book_id=:book_id', delete_books)
    db.session.commit()
    print 'num:', len(delete_books)


@manager.option('-c', '--channel', dest='channel', default='')
def delete_chapters_from_source(channel):
    from models import db
    sql = 'select book_id from book where source="%s"' %(channel)
    books = db.session.execute(sql).fetchall()
    for book in books:
        sql = 'delete from book_volume where book_id=%s'  %book.book_id
        db.session.execute(sql)
        sql = 'delete from book_chapters where book_id=%s'  %book.book_id
        db.session.execute(sql)
        sql = 'delete from book_chapter_content where book_id=%s'  %book.book_id
        db.session.execute(sql)
        db.session.commit()

@manager.command
def send_group_message():
    from lib import redis_utils
    key = 'send_group_message'
    value = random_str(25)
    redis_utils.set_cache(key, value, 10)
    url = 'http://localhost:6794/user/send_group_message'
    data = dict(value=value)
    print requests.get(url, data).text, value


def random_str(length):
    return ''.join(random.sample(string.letters + '1234567890',length))

def calc_word_count_from_chapters(book_id):
    sql = 'select sum(word_count) from book_chapters where book_id=%s' %(book_id)
    return db.session.execute(sql).scalar() or 0

@manager.option('-c', '--channel', dest='channel', default='')
def count_words(channel):
    books = Book.query.filter_by(word_count=0, is_comic=0, source=channel).all()
    for b in books:
        print 'before', b.book_name, b.book_id, b.word_count
        word_count = calc_word_count_from_chapters(b.book_id)
        if word_count:
            b.word_count = word_count
        print 'after', b.book_name, b.book_id, b.word_count
        db.session.add(b)
    db.session.commit()

@manager.command
def update_book_shelf():
    names = ['hot', 'new', 'finish']
    for name in names:
        book_shelfs = BookShelf.query.filter_by(name=name).all()
        for i in book_shelfs:
            book_data = i.to_admin_dict()['book']
            if book_data:
                if book_data['channel_type'] == 1: # man
                    m_name = '%s%s' %(name, '-m')
                    if not BookShelf.query.filter_by(book_id=i.book_id, name=m_name).first():
                        db.session.add(BookShelf(i.book_id, m_name, i.user_id, i.ranking, i.rate, i.showed, 1))
                elif book_data['channel_type'] == 2: # woman
                    f_name = '%s%s' %(name, '-f')
                    if not BookShelf.query.filter_by(book_id=i.book_id, name=f_name).first():
                        db.session.add(BookShelf(i.book_id, f_name, i.user_id, i.ranking, i.rate, i.showed, 2))
        db.session.commit()
    # 非外链小说按男女分类导入精选小说（good-m，good-f）专题
    books = Book.query.filter_by(free_collect=0).all()
    for b in books:
        if b.channel_type == 1:
            if not BookShelf.query.filter_by(book_id=b.book_id, name='good-m').first():
                db.session.add(BookShelf(b.book_id, 'good-m', 0, 0, 0, 1, 1))
        if b.channel_type == 2:
            if not BookShelf.query.filter_by(book_id=b.book_id, name='good-f').first():
                db.session.add(BookShelf(b.book_id, 'good-f', 0, 0, 0, 1, 2))
    db.session.commit()

    # 将外链小说按男女分类导入男生偏爱（free-m）专题和女生偏爱（free-f）专题
    books = Book.query.filter_by(free_collect=1).all()
    for b in books:
        if b.channel_type == 1:
            if not BookShelf.query.filter_by(book_id=b.book_id, name='free-m').first():
                db.session.add(BookShelf(b.book_id, 'free-m', 0, 0, 0, 1, 1))
        if b.channel_type == 2:
            if not BookShelf.query.filter_by(book_id=b.book_id, name='free-f').first():
                db.session.add(BookShelf(b.book_id, 'free-f', 0, 0, 0, 1, 2))
    db.session.commit()

def add_ct_cd(i, platform):
    ct = ChannelType.query.filter_by(platform=platform, name=i.name).first()
    if not ct:
        data = i.to_admin_dict()
        data['platform'] = platform
        ct = ChannelType(data)
        db.session.add(ct)
        db.session.commit()

    cds = ChannelData.query.filter_by(channel_code=i.id).all()
    for cd in cds:
        t_cd = ChannelData.query.filter_by(
                    class_id=cd.class_id, channel_code=ct.id,
                    class_name=cd.class_name).first()
        if not t_cd:
            t_cd = ChannelData(class_id=cd.class_id,
                        channel_code=ct.id, class_name=cd.class_name)
            db.session.add(t_cd)
    db.session.commit()

@manager.command
def add_ios_applet_channel_type():
    cts = ChannelType.query.filter_by(platform='android').all()
    for i in cts:
        add_ct_cd(i, 'ios')
        add_ct_cd(i, 'applet')








if __name__ == "__main__":
    manager.run()
