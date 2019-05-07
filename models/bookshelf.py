# coding: utf-8
from base import db
from sqlalchemy.sql import func
from sqlalchemy.dialects.mysql import TEXT, MEDIUMTEXT
from book import Book
import datetime

class BookShelf(db.Model):
    ''' 书架 '''
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'}

    id = db.Column(db.Integer(), primary_key=True)
    book_id = db.Column(db.Integer(), index=True)                   # 书籍ID
    name = db.Column(db.String(100))                                # 书架名称('myself', 'hot', 'new', 'recommend', 'finish') 
    user_id = db.Column(db.Integer())                               # 用户id, 用于myself 自己的书架
    ranking = db.Column(db.Integer(), default=0)                    # 用于排序
    rate = db.Column(db.Integer(), default=0)                       # 阅读进度(百分率分子)
    showed = db.Column(db.Boolean(), default=True)                  # 是否显示
    sex = db.Column(db.Integer(), server_default='0')               # 热门和新书需要区分男女频（1：男；2: 女)
    created = db.Column(db.DateTime, server_default=func.now())     # 创建时间
    updated = db.Column(db.DateTime, server_default=func.now())     # 更新时间 

    db.Index('ix_book_id_name_user_id', book_id, name, user_id, unique=True)

    def __init__(self, book_id, name, user_id, ranking, rate, showed, sex):
        self.book_id = book_id
        self.name = name
        self.user_id = user_id
        self.ranking = ranking
        self.rate = rate
        self.showed = showed
        self.sex = sex


    def to_admin_dict(self):
        book = Book.query.filter_by(book_id=self.book_id).first()
        return dict(id = self.id,
                    book_id = self.book_id,
                    book = book.to_admin_dict() if book else {},
                    name = self.name,
                    user_id = self.name,
                    ranking = self.ranking,
                    rate = self.rate,
                    showed = int(self.showed) if self.showed else 0,
                    sex = self.sex,
                    created = self.created.strftime('%Y-%m-%d %H:%M:%S'))

class BookShelfName(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(100))
    nickname = db.Column(db.String(100))
    showed = db.Column(db.Boolean(), default=True)
    icon_url = db.Column(db.String(150))
    style = db.Column(db.SmallInteger(), server_default='1')  # 1横, 2竖 
    remark = db.Column(db.String(100))

    updated = db.Column(db.DateTime, server_default=func.now())
    created = db.Column(db.DateTime, server_default=func.now())

    def update(self, data):
        if data.has_key('nickname'): self.nickname = data['nickname']
        if data.has_key('showed'): self.showed = int(data['showed'])
        if data.has_key('icon_url') and 'http' in data['icon_url']:
            self.icon_url = data['icon_url']
        if data.has_key('style'):
            self.style = int(data['style'])
        if data.has_key('remark'): self.remark = data['remark']
        self.updated = datetime.datetime.now()

    def __init__(self, data):
        self.name = data['name']
        self.nickname = data['nickname']
        self.remark = data.get('remark', '')
        self.showed = 1 if int(data.get('showed', 1)) == 1 else 0
        self.icon_url = data.get('icon_url', '')
        self.channel_list = '1|2'
        self.style = int(data.get('style', 1)) 

    def to_dict(self):
        data =  dict(
            name=self.name,
            title=self.nickname,
            icon=self.icon_url if self.icon_url else '',
            style=self.style,
            more=u'查看更多',
            activity = '',
            ios_activity = '',
            applet_activity = '',
            params = {},
            books = [],
        )
        #if self.name == 'hot':
        #    data['activity'] = 'MainChannelActivity'
        #    data['ios_activity'] = 'RecommendViewController'
        #    data['applet_activity'] = '/pages/chapterList/chapterList?book_id=185061'
        return data

    def to_admin_dict(self):
        return dict(
                id = self.id,
                name = self.name,
                nickname = self.nickname,
                showed = 1 if self.showed else 0,
                icon_url = self.icon_url,
                style = self.style,
                remark = self.remark,
                created = self.created.strftime('%Y-%m-%d %H:%M:%S'),
                updated = self.updated.strftime('%Y-%m-%d %H:%M:%S'),
            )
