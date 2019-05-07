# coding=utf-8
import logging
import ujson as json
from lib import sina
from models import db
from models import BookCategory, Book, BookVolume, BookChapters, BookChapterContent
from flask import current_app
import datetime

from models.book import ChannelBookCategory

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


def add_book_volumes(real_book_id, local_book):
    """更新书籍卷"""
    ret = json.loads(sina.get_chapters(real_book_id))
    local_book_id = local_book['book_id']
    if ret['code'] == 0:
        max_vid = local_book.get('max_vid', 0)
        max_cid = local_book.get('max_cid', 0)

        # 过滤出大于等于本地最大卷id的卷
        new_volume_group = filter(lambda x: x['volume_id'] >= max_vid, ret['data'])
        print '**volume: ', max_vid
        for volume in new_volume_group:
            print volume['volume_id']
            if volume['volume_id'] > max_vid:
                # 增加卷
                volume['book_id'] = local_book_id
                db.session.add(BookVolume(volume))

            new_chapter_group = volume['chapters']
            # 过滤出大于本地最新卷中最大章节id的章节
            if volume['volume_id'] == max_vid:
                new_chapter_group = filter(lambda x: x['chapter_id'] > max_cid, new_chapter_group)
            print '==chapter: ', max_cid
            for chapter in new_chapter_group:
                print chapter['chapter_id']
                add_book_chapters(local_book_id, chapter)

            if new_chapter_group:
                local_book['max_cid'] = new_chapter_group[-1]['chapter_id']

            # 有更新 则 更新卷
            if volume['volume_id'] == max_vid and new_chapter_group:
                update_volume(volume)

        if new_volume_group:
            local_book['max_vid'] = new_volume_group[-1]['volume_id']


def update_volume(volume):
    """更新卷"""
    db.session.execute('''
            update book_volume set
                volume_name=:BookVolum,
                create_time=:volume_name,
                chapter_count=:create_time,
                update_time=:chapter_count
            where book_id=:book_id and volume_id=:volume_id''', {
        "volume_name": volume['volume_name'],
        "create_time": volume['create_time'],
        "chapter_count": int(volume['chapter_count']),
        "update_time": volume['update_time'],
        "book_id": volume['book_id'],
        "volume_id": volume['volume_id'],
    })


def add_book_chapters(local_book_id, chapter):
    """增加章节"""
    real_book_id = chapter['book_id']
    volume_id = chapter['volume_id']
    chapter_id = chapter['chapter_id']
    chapter['book_id'] = local_book_id
    db.session.add(BookChapters(chapter))

    ret = json.loads(sina.get_chapter_content(real_book_id, chapter_id))
    if ret['code'] == 0:
        ret['data']['volume_id'] = volume_id
        ret['data']['book_id'] = local_book_id
        db.session.add(BookChapterContent(ret['data']))


def gen_channel_bind_id(book_id):
    """生成渠道相关id"""
    return 'sina:%s' % book_id


def add_books():
    """更新书籍"""
    # 取书籍列表
    ret = json.loads(sina.get_book_list())
    if ret['code'] != 0:
        return

    # 取本地书籍对应最新章节id 卷id 更新时间
    local_latest_books = get_local_book_latest()

    # 获取本地已有分类
    local_cate_dict = {cate.channel_cate_id: cate.cate_id for cate in ChannelBookCategory.query.all()}
    for d in ret['data']:
        real_book_id = int(d['book_id'])
        channel_book_id = gen_channel_bind_id(real_book_id)
        r = json.loads(sina.get_book_info(real_book_id))
        if r['code'] == 0:
            # 获取本地分类id
            cate_id = local_cate_dict.get(gen_channel_bind_id(r['data']['cate_id']))
            if not cate_id:
                print '!!!!NO cate_id: ', d
                continue
            r['data']['cate_id'] = cate_id
            r['data']['channel_book_id'] = channel_book_id
            r['data']['source'] = 'sina'

            local_book = local_latest_books.get(channel_book_id, {})
            if not local_book:
                # 增加书
                _book = Book(r['data'])
                db.session.add(_book)
                db.session.commit()
                local_book['book_id'] = _book.book_id

                # 增加章节
                add_book_volumes(real_book_id, local_book)
            else:
                # 更新书
                update_book(r['data'])
                remote_book = r['data']
                print '##book: ', channel_book_id, remote_book['chapter_num'], remote_book['word_count'], \
                    remote_book['update_time'], local_book
                if remote_book['chapter_num'] > local_book['chapter_num'] or \
                        remote_book['word_count'] > local_book['word_count'] or \
                        remote_book['update_time'] > local_book['update_time']:
                    add_book_volumes(real_book_id, local_book)

            # # 更新缓存
            # local_book.update(
            #     {"update_time": remote_book['update_time'],
            #      "word_count": int(remote_book['word_count']),
            #      "chapter_num": remote_book['chapter_num']})
            # local_book.setdefault('max_vid', 0)
            # local_book.setdefault('max_cid', 0)

            # 以书为单位提交 防止出现异常 又要从头开始
            try:
                db.session.commit()
            except Exception:
                db.session.rollback()

                # 若中断会导致缓存未更新而重复添加中断之前的书籍章节 TODO 待优化
                # cache_latest_book_info(local_latest_books)


def get_local_book_latest():
    """获取本地已缓存书籍最新信息"""
    cache_key = 'local_latest_book_info'
    data = current_app.redis.get(cache_key)
    if data:
        data = json.loads(data)
        data = {int(k): v for k, v in data.iteritems()}
        return data
    else:
        import time
        t1 = time.time()
        local_latest_books = db.session.execute('''
            select b.channel_book_id, b.book_id, max(bc.volume_id) as volume_id,
                max(bc.chapter_id) as chapter_id,
                b.update_time, b.chapter_num, b.word_count
            from book_chapters bc right join book b
            on bc.book_id=b.book_id where b.source='sina' group by b.book_id
        ''').fetchall()
        print '查询时间', time.time() - t1
        local_latest_books = {b.channel_book_id: {"max_vid": int(b.volume_id or 0),
                                                  "max_cid": int(b.chapter_id or 0),
                                                  "book_id": int(b.book_id),
                                                  "update_time": b.update_time.__str__(),
                                                  "word_count": int(b.word_count),
                                                  "chapter_num": int(b.chapter_num)} for b in local_latest_books}
        return local_latest_books


def cache_latest_book_info(data):
    """缓存最新书籍信息"""
    cache_key = 'local_latest_book_info'
    current_app.redis.set(cache_key, json.dumps(data))


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
            create_time=:create_time,
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
        "create_time": data['create_time'],
        "cover": data['cover'],
        "intro": data['intro'],
        "word_count": int(data['word_count']),
        "update_time": data['update_time'],
        "book_id": data['book_id'],
    })


def start():
    print 'Start update book...', datetime.datetime.now()
    add_books()
    print 'End update book', datetime.datetime.now()
