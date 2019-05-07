# coding: utf-8
from datetime import datetime

from sqlalchemy.sql.schema import PrimaryKeyConstraint

from base import db
from bookshelf import BookShelfName
from sqlalchemy.sql import func
import json

class Topic(db.Model):
    '''话题表(Banner 下方)'''
    id = db.Column(db.Integer(), primary_key=True)
    title = db.Column(db.String(100))
    url = db.Column(db.String(100))
    icon_url = db.Column(db.String(100))
    activity = db.Column(db.String(50))
    ios_activity = db.Column(db.String(50))
    applet_activity = db.Column(db.String(100))
    params = db.Column(db.Text) # 客户端需要参数,保存json
    showed = db.Column(db.Boolean(), default=True)
    remark = db.Column(db.String(100))
    modified = db.Column(db.DateTime(), server_default=func.now())
    created = db.Column(db.DateTime(), server_default=func.now())

    def __init__(self, data):
        self.title = data['title']
        self.url = data['url']
        self.remark = data.get('url', '')
        self.icon_url = data['icon_url']
        self.activity = data['activity']
        self.ios_activity = data['ios_activity']
        self.applet_activity = data.get('applet_activity', '')
        self.params = json.dumps(json.loads(data['params']))
        self.showed = 1 if data.get('showed', 0) == 1 else 0

    def update(self, data):
        self.title = data['title'] if data.has_key('title') else self.title
        self.url = data['url'] if data.has_key('url') else self.url
        self.icon_url = data['icon_url'] if data.has_key('icon_url') else self.icon_url
        self.activity = data['activity'] if data.has_key('activity') else self.activity
        self.ios_activity = data['ios_activity'] if data.has_key('ios_activity') else self.ios_activity
        self.params = json.dumps(json.loads(data['params'])) if data.has_key('params') else self.params
        self.showed = 1 if int(data.get('showed', 0)) == 1 else 0
        if data.has_key('remark'): self.remark = data['remark']
        if data.has_key('applet_activity'): self.applet_activity = data['applet_activity']

    def to_dict(self):
        return dict(
            title = self.title,
            url = self.url,
            icon_url = self.icon_url,
            activity = self.activity,
            ios_activity = self.ios_activity,
            applet_activity = self.applet_activity,
            params = json.loads(self.params),
        )

    def to_admin_dict(self):
        data =  self.to_dict()
        data['id'] = self.id
        data['remark'] = self.remark
        data['showed'] = 1 if self.showed else 0
        data['modified'] = self.modified.strftime('%Y-%m-%d %H:%M:%S')
        data['created'] = self.created.strftime('%Y-%m-%d %H:%M:%S')
        return data


class Banner(db.Model):
    """广告表"""
    id = db.Column(db.Integer(), primary_key=True)
    title = db.Column(db.String(100))
    platform = db.Column(db.String(50))
    activity = db.Column(db.String(50))
    ios_activity = db.Column(db.String(50))
    applet_activity = db.Column(db.String(100))
    params = db.Column(db.String(150)) # 客户端需要参数,保存字典
    sex = db.Column(db.Integer(), default=1) # 0: 所有 1：男；2: 女
    url = db.Column(db.String(150))
    banner_url = db.Column(db.String(150))
    level = db.Column(db.Integer(), default=0)
    showed = db.Column(db.Boolean(), default=False)
    modified = db.Column(db.DateTime(), server_default=func.now())
    created = db.Column(db.DateTime(), server_default=func.now())
    m_id = db.Column(db.Integer(), server_default='-1')
    channel_list = db.Column(db.String(50)) # 1|2|3 所属频道列表

    def get_string_channels(self, channels):
        channels = channels.split('|')
        array = [ i for i in channels if ChannelType.query.filter_by(id=int(i)).first() ]
        array.sort()
        return '|'.join(set(array))

    def get_array_channels(self):
        try:
            array = self.channel_list.split('|')
            return [int(i) for i in array]
        except:
            return []

    def __init__(self, data):
        self.title = data.get('title', '')
        self.platform = data.get('platform', '')
        self.activity = data.get('activity', '')
        self.ios_activity = data.get('ios_activity', '')
        self.applet_activity = data.get('applet_activity', '')
        self.params = json.dumps(json.loads(data.get('params', json.dumps({}))))
        self.sex = int(data.get('sex', 0))
        self.url = data.get('url', '')
        self.banner_url = data['banner_url']
        self.level = int(data.get('level', 0))
        self.showed = 1 if int(data.get('showed', 0)) == 1 else 0
        self.m_id = int(data.get('m_id', -1))

        if self.sex == 1:
            self.channel_list = '3'
        elif self.sex == 2:
            self.channel_list = '2'
        else:
            self.channel_list = '2|3'
        #self.channel_list = self.get_string_channels(data['channel_list'])

    def update(self, data):
        self.title = data.get('title', '')
        self.platform = data.get('platform', '')
        self.activity = data.get('activity', '')
        self.ios_activity = data.get('ios_activity', '')
        self.applet_activity = data.get('applet_activity', '')
        self.params = json.dumps(json.loads(data.get('params', json.dumps({}))))
        self.sex = int(data.get('sex', 0))
        self.url = data.get('url', '')
        self.banner_url = data['banner_url']
        self.level = int(data.get('level', 0))
        self.showed = 1 if int(data.get('showed', 0)) == 1 else 0
        self.m_id = int(data.get('m_id', -1))
        print 'update', self.showed

        #self.channel_list = '1|2'
        #self.channel_list = self.get_string_channels(data['channel_list'])
        self.modified = datetime.now()

    def update_channel_list(self):
        if self.sex == 1:
            self.channel_list = '3'
        elif self.sex == 2:
            self.channel_list = '2'
        else:
            self.channel_list = '2|3'

        self.modified = datetime.now()



    def to_admin_dict(self):
        return dict(
            id = self.id,
            m_id = self.m_id,
            title = self.title,
            platform = self.platform,
            activity = self.activity,
            ios_activity = self.ios_activity,
            applet_activity = self.applet_activity,
            params = json.loads(self.params),
            sex = self.sex,
            url = self.url,
            banner_url = self.banner_url,
            level = self.level,
            showed = int(self.showed),
            channel_list = self.get_array_channels(),
            created = self.created.strftime('%Y-%m-%d %H:%M:%S'),
            modified = self.modified.strftime('%Y-%m-%d %H:%M:%S')
        )

    def to_dict(self):
        return dict(
            id = self.id,
            title = self.title,
            platform = self.platform,
            activity = self.activity,
            ios_activity = self.ios_activity,
            applet_activity = self.applet_activity,
            params = json.loads(self.params),
            sex = self.sex,
            url = self.url,
            banner_url = self.banner_url,
            level = self.level
        )

class ChannelType(db.Model):
    ''' 首页频道表 '''
    id = db.Column(db.Integer(), primary_key=True) # channel_code
    name = db.Column(db.String(20))

    platform = db.Column(db.String(50), server_default='android')
    ranking = db.Column(db.Integer(), server_default='0')
    showed = db.Column(db.Boolean(), default=False)
    modified = db.Column(db.DateTime(), server_default=func.now())
    created = db.Column(db.DateTime(), server_default=func.now())

    def __init__(self, data):
        self.name = data['name']
        self.ranking = int(data.get('ranking', 0))
        if data.has_key('platform'):
            self.platform = data['platform']
        if data.has_key('showed'):
            self.showed = 1

    def update(self, data):
        if data.has_key('name'):
            self.name = data['name']
        if data.has_key('ranking'):
            self.ranking = data['ranking']
        if data.has_key('platform'):
            self.platform = data['platform']
        if data.has_key('showed'):
            self.showed = data['showed']


    def to_admin_dict(self):
        return dict(
            channel_code = self.id,
            ranking = self.ranking,
            name = self.name,
            platform = self.platform,
            showed = 1 if self.showed else 0,
            modified = self.modified.strftime('%Y-%m-%d %H:%M:%S'),
            created = self.created.strftime('%Y-%m-%d %H:%M:%S'),
        )
    
    def to_dict(self):
        return dict(
            channel_code = self.id,
            channel_name = self.name,
            platform = self.platform,
        )

class ChannelData(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    class_id = db.Column(db.Integer())
    channel_code = db.Column(db.Integer())
    class_name = db.Column(db.String(20)) # banner, topic, book_shelf_name
    ranking = db.Column(db.Integer(), server_default='0')
    created = db.Column(db.DateTime(), server_default=func.now())

    def update(self, data):
        if data.has_key('ranking'):
            self.ranking = data['ranking']

    def to_admin_dict(self):
        data = dict(id=self.id, ranking=self.ranking)
        if self.class_name == 'banner':
            obj = Banner.query.filter_by(id=self.class_id).first()
        elif self.class_name == 'book_shelf_name':
            obj = BookShelfName.query.filter_by(id=self.class_id).first()
        elif self.class_name == 'topic':
            obj = Topic.query.filter_by(id=self.class_id, showed=1).first()
        else:
            obj = None
        data['class_data'] = obj.to_admin_dict() if obj else {}
        return data
