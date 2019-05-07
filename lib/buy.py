# -*- coding: utf-8 -*-
"""
Doc:

Created on 2017/8/30
@author: MT
"""
import ujson as json
import requests
from flask_login import current_user
from flask import request, current_app
from models.book import BookChapters, PurchasedBook, BuyRankings, Book
from models.user import UserBalance, UserBalanceLog
from models import db
import datetime

def get_word_money(word_count):
    """计算字数对应书币"""
    return (int(word_count) + 199) / 200

def buy_book(book_id, volume_chapter, platform):
    """购买书籍"""
    volume_chapter_dict = {}
    for x in [v.split(',') for v in volume_chapter.split('|')]:
        volume_chapter_dict.setdefault(int(x[0]), []).append(int(x[1]))

    user_balance = UserBalance.query.filter_by(user_id=current_user.id).with_lockmode('update').first()
    if not user_balance:
        return {"code": -2, "msg": "书币不足"}

    purchased = PurchasedBook.query.filter_by(user_id=current_user.id, book_id=book_id).with_lockmode('read').first()
    buy_info = {}
    if purchased:
        buy_info = json.loads(purchased.buy_info)

    # 判断是否漫画
    book = Book.query.filter_by(book_id=book_id).first()
    is_comic = False
    if book and book.is_comic:
        is_comic = True

    money = 0
    chapter_table_ids = []
    buy_chapter_ids = []
    buy_chapter_moneys = []
    for volume_id, chapter_ids in volume_chapter_dict.iteritems():
        purchased_chapters = buy_info.get(str(volume_id), [])
        if [c_id for c_id in chapter_ids if c_id in purchased_chapters]:
            return {"code": -1, "msg": "章节已购买，无法重复购买"}

        chapters = BookChapters.query.filter(BookChapters.book_id == book_id,
                                             BookChapters.volume_id == volume_id,
                                             BookChapters.chapter_id.in_(chapter_ids)).all()
        tmp_chapters_moneys = []
        if is_comic:
            tmp_chapters_moneys = [c.money for c in chapters]
        else:
            tmp_chapters_moneys = [get_word_money(c.word_count) for c in chapters]
        money += sum(tmp_chapters_moneys)
        chapter_table_ids.extend([str(c.id) for c in chapters])

        buy_chapter_ids.extend(chapter_ids)
        buy_chapter_moneys.extend(tmp_chapters_moneys)

    if not money:
        return {"code": -1, "msg": "章节不存在"}

    if user_balance.balance < money:
        return {"code": -2, "msg": "书币不足"}

    # 扣除书币 增加日志
    user_balance.balance -= money
    _chapter_ids = chapter_table_ids if len(chapter_table_ids) <= 2 else [chapter_table_ids[0], chapter_table_ids[-1]]
    db.session.add(UserBalanceLog(current_user.id, 2, money, 'buy_book',
                                  '%s-%s' % (book_id, '|'.join(_chapter_ids)), 'buy book', platform, book_id))
    # 记录已购买章节
    if not purchased:
        purchased = PurchasedBook(user_id=current_user.id, book_id=book_id,
                                  buy_info='{}')
        db.session.add(purchased)
    for volume_id, chapter_ids in volume_chapter_dict.iteritems():
        buy_info.setdefault(str(volume_id), []).extend(chapter_ids)
    purchased.buy_info = json.dumps(buy_info)
    db.session.commit()

    #添加购买排行统计
    today = datetime.date.today()
    buy_ranking = BuyRankings.query.filter_by(book_id=book_id, created=str(today)).first()
    if buy_ranking:
        buy_ranking.buy_num = int(buy_ranking.buy_num) + 1
    else:
        book_info = Book.query.filter_by(book_id=book_id).first()
        buy_ranking = BuyRankings(book_id, book_info.channel_type, book_info.author_name, book_info.is_publish,
            book_info.status, today, 1, book_info.book_name, book_info.created)
    db.session.add(buy_ranking)
    db.session.commit()

    resp = requests.get(current_app.config['STATS_URL'] + '/book/book_chapter_collect',
                 params={'book_id': book_id,
                         'chapters': '|'.join([str(i) for i in buy_chapter_ids]),
                         'money': '|'.join([str(i) for i in buy_chapter_moneys]),
                         'user_id': current_user.id,
                         'type': 'buy',
                         'platform': platform,
                         's': request.args.get('s', '')})
    print resp.text
    return {"code": 0}


def next_auto_buy():
    """是否自动购买下一章"""
    buy_next = request.form.get('auto_buy', -1, int)
    book_id = request.form.get('book_id', 0, int)
    if buy_next == -1 or not book_id:
        return
    buy_next = True if buy_next == 1 else False
    if db.session.execute('select 1 from purchased_book where user_id=%s and book_id=%s limit 1' %
                                  (current_user.id, book_id)).scalar():
        db.session.execute('update purchased_book set auto_buy=%s where user_id=%s and book_id=%s' % (buy_next, current_user.id, book_id))
    else:
        db.session.execute('insert into purchased_book(user_id, book_id, buy_info, auto_buy) '
                           'values (:user_id, :book_id, :buy_info, :auto_buy) '
                           'ON DUPLICATE KEY UPDATE auto_buy=:auto_buy',
                           {'user_id': current_user.id, 'book_id': book_id, 'buy_info': '{}',
                            'auto_buy': buy_next})
    try:
        db.session.commit()
    except Exception:
        import traceback
        traceback.print_exc()
