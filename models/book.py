# coding: utf-8
import ujson as json
from base import db
from sqlalchemy.sql import func
from sqlalchemy.dialects.mysql import TEXT, MEDIUMTEXT
from datetime import datetime


class Book(db.Model):
    ''' 书籍基本信息 '''
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'}

    book_id = db.Column(db.Integer(), primary_key=True)  # 书籍ID
    channel_book_id = db.Column(db.String(20), unique=True)  # 渠道书籍id 渠道名:书籍id
    book_name = db.Column(db.String(100))  # 书籍名称
    cate_id = db.Column(db.Integer(), index=True)  # 书籍分类ID
    channel_type = db.Column(db.SmallInteger(), index=True)  # 书籍频道（1：男；2: 女 3: 出版 0: 无此属性默认为0）
    author_name = db.Column(db.String(50))  # 作者
    chapter_num = db.Column(db.Integer())  # 章节数量
    is_publish = db.Column(db.Integer())  # 是否出版（1：是；2：否）
    status = db.Column(db.Integer())  # 连载状态（1：已完结；2：未完结）
    create_time = db.Column(db.DateTime)  # 创建时间（第三方）
    cover = db.Column(db.String(300))  # 封面图片（链接）
    intro = db.Column(TEXT)  # 简介
    word_count = db.Column(db.Integer)  # 字数
    update_time = db.Column(db.DateTime)  # 更新时间
    created = db.Column(db.DateTime, server_default=func.now())  # 创建时间
    showed = db.Column(db.Boolean(), server_default='0')
    source = db.Column(db.String(50), server_default='sina')  # 来源
    free_collect = db.Column(db.Boolean(), server_default='0')  # 是否外链小说
    channel_cate = db.Column(db.String(50), server_default='')  # 渠道方分类名
    ranking = db.Column(db.Integer(), server_default='0') #排序
    is_comic = db.Column(db.Boolean(), server_default='0')  # 是否漫画

    short_des = db.Column(db.String(50), server_default='')  # 短描述

    def get_ch_source(self):
        if self.source == 'sina':
            return u'新浪阅读'
        elif self.source == 'kaixing':
            return u'恺兴阅读'
        elif self.source == 'zhangyue':
            return u'掌阅'
        elif self.source == 'jingyu':
            return u'鲸鱼阅读'
        elif self.source == 'anzhi':
            return u'安之'
        elif self.source == 'riyue':
            return u'日月'
        elif self.source == 'yangyue':
            return u'阳光'
        elif self.source == 'yunyue':
            return u'云阅'
        elif self.source == 'junengwan':
            return u'剧能玩'
        elif self.source == 'feilang':
            return u'飞浪'
        elif self.source == 'maimeng':
            return u'麦萌'
        elif self.source == 'lizhi':
            return u'礼智'
        elif self.source == 'shenju':
            return u'神居动漫'
        elif self.source == 'shidai':
            return u'时代漫王'
        elif self.source == 'huashen':
            return u'画神'
        elif self.source == 'kuman':
            return u'酷漫网'
        elif self.source == 'shenbeike':
            return u'神北克'
        elif self.source == 'wanhuatong':
            return u'万画筒'
        elif self.source == 'zhoumiao':
            return u'周淼漫画'
        elif self.source == 'iciyuan':
            return u'iCiyuan 动漫'
        else:
            return self.source

    def to_admin_dict(self):
        cate = BookCategory.query.filter_by(cate_id=self.cate_id).first()
        cate_name = cate.cate_name if cate else str(self.cate_id)
        return dict(
                    book_id = self.book_id,
                    channel_book_id = self.channel_book_id,
                    book_name = self.book_name,
                    cate_id = self.cate_id,
                    cate_name = cate_name,
                    channel_type = self.channel_type,
                    author_name = self.author_name,
                    chapter_num = self.chapter_num,
                    is_publish = self.is_publish,
                    status = self.status,
                    create_time = self.create_time.strftime('%Y-%m-%d %H:%M:%S'),
                    cover = self.cover if self.cover else 'https://ssl.kdyoushu.com/default_free_book_cover.jpg',
                    intro = self.intro if self.intro else '',
                    word_count = self.word_count,
                    update_time = self.update_time.strftime('%Y-%m-%d %H:%M:%S'),
                    created = self.created.strftime('%Y-%m-%d %H:%M:%S'),
                    showed = int(self.showed),
                    short_des = self.short_des,
                    source = self.get_ch_source())

    def __init__(self, data):
        self.channel_book_id = data['channel_book_id']
        self.book_name = data['book_name']
        self.cate_id = int(data['cate_id'])
        self.channel_type = int(data['channel_type'])
        self.author_name = data['author_name']
        self.chapter_num = data['chapter_num']
        self.is_publish = data['is_publish']
        self.status = data['status']
        self.create_time = data['create_time']
        self.cover = data['cover']
        self.intro = data['intro']
        self.word_count = int(data['word_count'])
        self.update_time = data['update_time']
        self.source = data['source']
        self.created = datetime.now()

    def update(self, data):
        self.book_name = data['book_name']
        self.cate_id = int(data['cate_id'])
        self.channel_type = int(data['channel_type'])
        self.author_name = data['author_name']
        self.chapter_num = data['chapter_num']
        self.is_publish = data['is_publish']
        self.status = data['status']
        self.create_time = data['create_time']
        self.cover = data['cover']
        self.intro = data['intro']
        self.word_count = int(data['word_count'])
        self.update_time = data['update_time']
        self.ranking = data['ranking']

    def to_dict(self):
        cate = BookCategory.query.filter_by(cate_id=self.cate_id).first()
        cate_name = cate.cate_name if cate else str(self.cate_id)
        return dict(
            book_id=self.book_id,
            book_name=self.book_name,
            cate_id=self.cate_id,
            cate_name=cate_name,
            channel_type=self.channel_type,
            author_name=self.author_name,
            chapter_num=self.chapter_num,
            is_publish=self.is_publish,
            status=self.status,
            create_time=self.create_time.strftime('%Y-%m-%d %H:%M:%S'),
            cover=self.cover if self.cover else 'https://ssl.kdyoushu.com/default_free_book_cover.jpg',
            intro=self.intro if self.intro else '',
            word_count=self.word_count,
            source=self.get_ch_source(),
            update_time=self.update_time.strftime('%Y-%m-%d %H:%M:%S'),
            free_collect=1 if self.free_collect else 0,
            is_comic=1 if self.is_comic else 0,
            created=self.created.strftime('%Y-%m-%d %H:%M:%S'),
        )


class FreeBook(db.Model):
    """外链书籍基本信息"""
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'}

    id = db.Column(db.Integer(), primary_key=True)
    book_id = db.Column(db.Integer(), index=True)  # 书籍ID
    channel_book_id = db.Column(db.String(20), unique=True)  # 渠道书籍id 渠道名:书籍id
    chapter_num = db.Column(db.Integer())  # 章节数量
    status = db.Column(db.Integer())  # 连载状态（1：已完结；2：未完结）
    create_time = db.Column(db.DateTime)  # 创建时间（第三方）
    word_count = db.Column(db.Integer)  # 字数
    update_time = db.Column(db.DateTime)  # 更新时间
    showed = db.Column(db.Boolean(), server_default='0')
    free_source = db.Column(db.String(50), server_default='', index=True)  # 来源
    channel_cate = db.Column(db.String(50), server_default='')  # 渠道方分类名
    last_chapter_name = db.Column(db.String(100), server_default='')  # 最新章节名
    created = db.Column(db.DateTime, server_default=func.now())  # 创建时间

    def get_parse_rule(self):
        """获取解析规则"""
        if self.free_source == 'wudu':
            return '吾读', '//*[@id="acontent"]/text()'
        elif self.free_source == 'dushu88':
            return '88读书', '//*[@id="nr1"]/text()'
        elif self.free_source == 'kanshu':
            return '看书', '//*[@id="chapcont"]/text()'
        elif self.free_source == 'zwdu':
            return '八一中文网', '//*[@id="nr1"]/text()'
        elif self.free_source == 'xxbiquge':
            return '新笔趣阁', '//*[@id="chaptercontent"]/text()'
        elif self.free_source == 'lingdian':
            return '零点看书', '//*[@id="novelcontent"]/p/text()'
        elif self.free_source == 'hkslg':
            return '顺隆书院', '//div[contains(@class,"contents")]/text()'
        elif self.free_source == 'mianhuatang':
            return '棉花糖小说网', '//*[@id="nr1"]/text()'
        return '', ''

    def to_dict(self):
        source_name, parse_rule = self.get_parse_rule()
        return dict(chapter_num=self.chapter_num,
                    status=self.status,
                    create_time=self.create_time.strftime('%Y-%m-%d %H:%M:%S'),
                    word_count=self.word_count,
                    update_time=self.update_time.strftime('%Y-%m-%d %H:%M:%S'),
                    free_source=self.free_source,
                    source=source_name,
                    parse_rule=parse_rule,
                    created=self.created.strftime('%Y-%m-%d %H:%M:%S'))


class BookCategory(db.Model):
    ''' 书籍分类信息 '''
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'}

    cate_id = db.Column(db.Integer(), primary_key=True)  # 分类ID
    cate_name = db.Column(db.String(50))  # 分类名称
    parent_id = db.Column(db.Integer(), server_default='-1')  # 上级ID  1:男生, 2:出版, 3:女生
    showed = db.Column(db.Boolean(), server_default='1')
    icon = db.Column(db.String(100))
    created = db.Column(db.DateTime, server_default=func.now())  # 创建时间

    def __init__(self, cate_name, parent_id=-1):
        self.cate_name = cate_name
        self.parent_id = parent_id

    def to_dict(self):
        return dict(
            style = 1, # 1没有榜单头样式 2有榜单头样式
            cate_id = self.cate_id,
            icon = self.icon,
            cate_name = self.cate_name,
            parent_id = self.parent_id,
            created = self.created.strftime('%Y-%m-%d %H:%M:%S')
        )

    def to_admin_dict(self):
        return dict(
            cate_id = self.cate_id,
            showed = 1 if self.showed else 0,
            cate_name = self.cate_name,
            parent_id = self.parent_id,
            icon = self.icon if self.icon else '',
            created = self.created.strftime('%Y-%m-%d %H:%M:%S')
        )

class ChannelBookCategory(db.Model):
    ''' 渠道书籍分类信息 '''
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'}

    channel_cate_id = db.Column(db.String(20), primary_key=True)  # 分类ID（第三方）
    cate_id = db.Column(db.Integer(), index=True)  # 分类ID

    def __init__(self, channel_cate_id, cate_id):
        self.channel_cate_id = channel_cate_id
        self.cate_id = cate_id


class BookVolume(db.Model):
    ''' 书籍卷节信息 '''
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'}

    id = db.Column(db.Integer(), primary_key=True)  # ID
    book_id = db.Column(db.Integer(), index=True)  # 书籍ID
    volume_id = db.Column(db.Integer(), index=True)  # 卷ID
    volume_name = db.Column(db.String(100))  # 卷名
    create_time = db.Column(db.DateTime, default=datetime.now())  # 创建时间（第三方）
    chapter_count = db.Column(db.Integer, default=0)  # 卷字数
    update_time = db.Column(db.DateTime, default=datetime.now())  # 更新时间（第三方）
    created = db.Column(db.DateTime, server_default=func.now())  # 创建时间

    def __init__(self, data):
        self.book_id = int(data['book_id'])
        self.volume_id = int(data['volume_id'])
        self.volume_name = data['volume_name']
        now = datetime.now()
        self.create_time = data.get('create_time', now)
        self.chapter_count = int(data.get('chapter_count', 0))
        self.update_time = data.get('update_time', now)

    def update(self, data):
        self.volume_name = data['volume_name']
        self.create_time = data['create_time']
        self.chapter_count = int(data['chapter_count'])
        self.update_time = data['update_time']

    def to_dict(self):
        return dict(
            book_id = self.book_id,
            volume_id = self.volume_id,
            volume_name = self.volume_name,
            chapter_count = self.chapter_count
        )


class BookChapters(db.Model):
    ''' 书籍章节信息 '''
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'}

    id = db.Column(db.Integer(), primary_key=True)  # ID
    book_id = db.Column(db.Integer(), index=True)  # 书籍ID
    volume_id = db.Column(db.Integer(), index=True)  # 卷ID
    chapter_id = db.Column(db.Integer(), index=True)  # 章节ID
    chapter_name = db.Column(db.String(100))  # 章节名称
    word_count = db.Column(db.Integer)  # 字数
    # alter table book_chapters modify column content_url text;
    content_url = db.Column(TEXT, server_default='')  # 章节内容url （外链小说【url直存】，漫画【'|'分隔，格式化字符串存储】）

    # add by wangzq@pv.cc 2017-9-12
    money = db.Column(db.Integer, server_default='0')  # 分/千字（漫画：单章节计费）

    create_time = db.Column(db.DateTime)  # 创建时间（第三方）
    update_time = db.Column(db.DateTime)  # 更新时间（第三方）
    free_source = db.Column(db.String(50), server_default='', index=True)  # 外链 源名
    created = db.Column(db.DateTime, server_default=func.now())  # 创建时间

    def __init__(self, data):
        self.book_id = int(data['book_id'])
        self.volume_id = int(data['volume_id'])
        self.chapter_id = int(data['chapter_id'])
        self.chapter_name = data['chapter_name']
        self.word_count = int(data['word_count'])
        self.create_time = data['create_time']
        self.update_time = data['update_time']

    def to_dict(self):
        content_url = ''
        if self.content_url and self.content_url.find('|') == -1:
            content_url = self.content_url
        return dict(
            book_id = self.book_id,
            volume_id = self.volume_id,
            chapter_id = self.chapter_id,
            chapter_name = self.chapter_name,
            word_count = self.word_count,
            content_url = content_url,
        )

    def to_admin_dict(self):
        return dict(
            id = self.id,
            book_id = self.book_id,
            volume_id = self.volume_id,
            chapter_id = self.chapter_id,
            chapter_name = self.chapter_name,
            word_count = self.word_count,
            money = self.money
        )


class BookChapterContent(db.Model):
    ''' 书籍章节内容信息 '''
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'}

    id = db.Column(db.Integer(), primary_key=True)  # ID
    book_id = db.Column(db.Integer)  # 书籍ID
    volume_id = db.Column(db.Integer)  # 卷ID
    chapter_id = db.Column(db.Integer)  # 章节ID
    content = db.Column(MEDIUMTEXT)  # 章节内容
    created = db.Column(db.DateTime, server_default=func.now())  # 创建时间

    db.Index('ix_book_id_chapter_id', book_id, chapter_id)

    def __init__(self, data):
        self.book_id = int(data['book_id'])
        self.volume_id = int(data['volume_id'])
        self.chapter_id = int(data['chapter_id'])
        self.content = data['content'].replace(u'　', '').replace(' ', '')

    def update(self, data):
        self.content = data['content'].replace(u'　', '').replace(' ', '')


class BookMark(db.Model):
    ''' 书签 '''
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'}

    id = db.Column(db.Integer(), primary_key=True)  # ID
    user_id = db.Column(db.Integer)  # 用户id
    book_id = db.Column(db.Integer)  # 书籍ID
    volume_id = db.Column(db.Integer)  # 卷ID
    chapter_id = db.Column(db.Integer)  # 章节ID
    params = db.Column(db.String(100))  #客户端字段
    created = db.Column(db.DateTime, server_default=func.now())  # 创建时间

    def to_dict(self):
        return dict(
            id = self.id,
            user_id = self.user_id,
            book_id = self.book_id,
            volume_id = self.volume_id,
            chapter_id = self.chapter_id,
            created = self.created,
            params = self.params
        )


class PurchasedBook(db.Model):
    """已购买书籍信息"""
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'}

    id = db.Column(db.Integer(), primary_key=True)  # ID
    user_id = db.Column(db.Integer(), index=True)  # 用户id
    book_id = db.Column(db.Integer(), index=True)  # 书籍ID
    buy_info = db.Column(db.Text(), default='{}')  # 已购买章节 {'卷id':[章节id,...]}
    auto_buy = db.Column(db.Boolean, default=False)  # 是否自动购买下一章
    created = db.Column(db.DateTime, server_default=func.now())  # 创建时间

    db.UniqueConstraint('user_id', 'book_id')


class BuyRankings(db.Model):
    """ 购买排行(用于书籍排行) """
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'}
    
    id = db.Column(db.Integer(), primary_key=True)  # ID
    book_id = db.Column(db.Integer(), index=True)  # 书籍ID
    book_name = db.Column(db.String(100))  # 书籍名称
    channel_type = db.Column(db.SmallInteger(), index=True) #1男2女
    author_name = db.Column(db.String(50))#作者
    is_publish = db.Column(db.Integer())  # 是否出版（1：是；2：否）
    status = db.Column(db.Integer())# 连载状态（1：已完结；2：未完结）
    created = db.Column(db.DateTime)  # 创建时间
    buy_num = db.Column(db.Integer()) #购买次数
    book_time = db.Column(db.DateTime)  # 创建时间

    
    def __init__(self, book_id, channel_type, author_name, is_publish, status, created, buy_num, book_name, book_time):
        self.book_id = book_id
        self.channel_type = channel_type
        self.author_name = author_name
        self.is_publish = is_publish
        self.status = status
        self.created = created
        self.buy_num = buy_num
        self.book_name = book_name
        self.book_time = book_time
