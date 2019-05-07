# -*- coding: utf-8 -*-
"""
Doc: 更新书籍分类脚本
Created by MT at 2017/10/13
"""
from models import BookCategory, Book, db


def update_book_category():
    cate_dict = {cate.cate_name.encode('utf8'): cate.cate_id for cate in BookCategory.query.all()}

    num = 0
    for line in open('script/book_cate.txt').readlines():
        book_name, sex, cate_name = line.split()
        book = Book.query.filter_by(book_name=book_name, free_collect=0).first()
        if not book:
            print "No book", book_name
            continue
        cate_id = cate_dict.get(cate_name)
        if not cate_id:
            print "No category", cate_name
            continue
        book.cate_id = cate_id
        book.channel_cate = ''
        book.channel_type = 1 if sex == '男频' else 2
        book.ranking = 1
        num += 1
    db.session.commit()
    print 'success:', num


def update_category():
    """根据源网站分类更改新分类"""
    import codecs
    cate_dict = {cate.cate_name.encode('utf8'): (cate.cate_id, cate.parent_id) for cate in BookCategory.query.filter_by(showed=1).all()}
    with codecs.open('script/file_cate.txt', 'r') as f:
        for row in f.readlines():
            row = row.split('|')
            if not row or len(row) != 4:
                print 'Error format', row
                continue
            _, channel_cate, source, cate_name = [i.strip() for i in row]
            print channel_cate, source, cate_name
            cate_id, parent_id = cate_dict.get(cate_name, (0, 0))
            if not cate_id:
                print 'No category', cate_name
                continue
            if parent_id == 1:
                channel_type = 1
            elif parent_id == 3:
                channel_type = 2
            else:
                channel_type = 3
            r_c = db.session.execute("""UPDATE book b
SET b.cate_id = :new_cate_id, b.channel_cate = '', b.channel_type = :channel_type
WHERE b.free_collect = 1 AND b.source = :source AND b.channel_cate = :channel_cate
""", {'new_cate_id': cate_id, 'source': source, 'channel_cate': channel_cate, 'channel_type': channel_type}).rowcount
            db.session.commit()
            print "row count", r_c


def add_category():
    """增加分类"""
    cate_dict = {cate.cate_name.encode('utf8'): cate.cate_id for cate in BookCategory.query.all()}
    cate_str = {
        "现代都市": 1,
        "玄幻奇幻": 1,
        "武侠仙侠": 1,
        "军事历史": 1,
        "悬疑灵异": 1,
        "游戏竞技": 1,
        "科幻末世": 1,
        "现代言情": 3,
        "古代言情": 3,
        "总裁豪门": 3,
        "穿越架空": 3,
        "青春校园": 3,
        "耽美同人": 3,
    }
    for cate_name, parent in cate_str.iteritems():
        if cate_name not in cate_dict:
            db.session.add(BookCategory(cate_name, parent))
    db.session.commit()

