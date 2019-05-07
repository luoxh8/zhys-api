# coding: utf-8

class BaseConfig:
    BABEL_DEFAULT_LOCALE = 'zh_CN'
    SECRET_KEY = 'CmNDp9oi9uj2OeW2P0E1w932lk'

    CELERY_BROKER = {
        'SMS': 'redis://localhost:6379/3',  # 短信发送队列
        'ASYNC_REQ': 'redis://localhost:6379/6',  # 异步请求http
    }

    CHANNEL_URL = 'http://channel-host:6666'
    STATS_URL = 'http://stats-host:6894'  # 统计系统url

    WX_TOKEN = 'GVihOxkzmBfQYKLu7JNe'  # 消息推送令牌
    WX_AESKEY = '425bKHXPIY8zqV57v3a2wY7SpCtYejfrSWxR9ZaThT3'  # 消息加密密钥
    WXAPP_ID = 'wx28c8a74bd01f5e3a'
    # WXAPP_ID = 'wx8e8fc77f7f2ef904'
    WXAPP_SECRET = '1c7efd0054d7ac6aaa84b4205e6e3794'
    # WXAPP_SECRET = '0624061fa7638f0538299c6973ff059a'

    # 充值金额选项列表 单位元
    RECHARGE_OPTIONS = {
        'applet': [6, 12, 30, 50, 98, 198],
        'app': [6, 12, 30, 50, 98, 198],
    }

    # ios m_id 对应bundle_id
    IOS_BUNDLE_ID = {
        -1: ['com.zhihui.zhysread', 'com.zhys.reader', 'com.xia.reader'],  # 默认
        1: ['com.xiazhuan.zhysread'],
        2: ['com.xiaer.zhysread'],
        3: ['com.xia.reader'],
    }
    # ios内购购买项配置
    IAP_PRODUCT_CFG = {
        # 旧版本
        '7': 600,
        '12': 1200,
        '30': 3000,
        '50': 5000,
        '98': 9800,
        '198': 19800,

        # 新版本
        '600': 600,
        '1200': 1200,
        '3000': 3000,
        '5000': 5000,
        '9800': 9800,
        '19800': 19800,
    }

    REDIS_SETTINGS = {
        'HOST': '127.0.0.1',
        'PORT': 6379,
        'DB': 4,
    }

    QINIU_SETTINGS = dict(
        access_key='mD9rPwwMevxOL3uC38eOAfno4TZxTjKXEBub4vAk',
        secret_key='v1M5HVJpN8s2PtGEorH8Wj6NyiEKgnei9VCQpMZ_',
        buckets={
            'zhys': 'ov2eyt2uw.bkt.clouddn.com'
        }
    )

    # 接口验证秘钥
    API_SECRET_KEYS = {
        'android': {
            '1.0.5': '8dudsx0onwekqmpfypzrsub1c5ebitok',
            '1.0.6': 'd5aolquwijst63h4cksrbgpbpeiy1x8n',
            '1.0.7': 'vytg4opl9khjednutbmkbzgypfrfv5sz',
            '1.0.9': 'gq7pjpr69k4tdyfhcamfwmniueyli8zz',
            '1.1.0': 'xlvqw1wjtiarvciupfjmy8rpdxdm7hh4',
            '1.2.0': '8d0mb3uduqvwfe9wskq41x2jx7k5nsjz',
            '1.2.1': 'bhwcczyefqtv79axp3mf6byhmjegdul0',
            '1.2.2': 'p1iadkq9ocjx4ywcjuz50ewfhlqgx8v3',
            '1.2.3': 'mgquzx9r27uieqc8ygnf5tsodhb3pcef',
            '1.2.4': 'tfsc2ua893zydnlej6ip04m5wqhgvors',
        },
        'ios': {
            '1.0.0': '1jperf0ingjlwh2mhtwodba4g9azosyb',
            '1.0.1': '8tlucpd0aud2rjzyb6c3xvyff4jrahoq',
            '1.0.2': 'mazpjfqr9wxdye1vzo6qslcl2dcuau7t',
            '1.0.3': 'fyuka4lek2s8fmxvhiehbu6z0qcdrmad',
            '1.0.4': 'oa3kguj6vcprlhklfxdqebtigbhj0yda',
            '1.0.5': 'nfhyqlyredcsxho2zk4gmdjt18aogubu',
            '1.0.6': '1jperf0ingjlwh2mhtwodba4g9azosyb',
        },
        'ios_other': {
            '1.2.2': 'gnm1wrcofjezpi845yrx9vh7qndcmp60',
            '1.2.3': '1vtzhcuybbwqr09gcnd4xfgtkra6le8q',
        }
    }


class DebugConfig(BaseConfig):
    SQLALCHEMY_DATABASE_URI = 'mysql://root:root@127.0.0.1/zhys'
    BASE_URL = 'http://dev.api.kdyoushu.com:7000'
    DEBUG = True
    PORT = 5000

    DEFINES = {
        'SMSCAPTCHA_ACTION': {
            'REGISTER': 1,
            'RESETPWD': 2,
            'SET_NOTIFY_PHONE': 3,
            'PHONERESETPWD': 4,
            'bind_phone': 5,
            'switch_user': 6,
            'modify_phone_verify': 7,
            'modify_phone': 8,
            'oauth_bind_cancel': 9,
        }
    }
    CAPTCHA_SETTINGS = {
        'acts': ['register', 'resetpwd', 'login', 'ad_pic', 'set_notify_phone', 'bind_phone', 'switch_user',
                 'modify_phone_verify', 'modify_phone', 'oauth_bind_cancel'],
        'expires': 600,
    }
    CAPTCHA_EXPIRES = 60


class ReleaseConfig(BaseConfig):
    SQLALCHEMY_DATABASE_URI = 'mysql://job:aC9TWr2BbgD6dMA9PoA8@127.0.0.1/zhys'
    BASE_URL = 'http://api.kdyoushu.com:7000'
    PORT = 6791

    LOGGING = {  # 配置日志
        'SMTP': {  # 邮箱日志发送， 如果没有配置， 则不开启
            'HOST': 'smtp.exmail.qq.com',  # smtp 服务器地址
            'TOADDRS': ['linjf@pv.cc', 'mat@pv.cc', 'wangzq@pv.cc', 'liuzy@pv.cc'],  # smtp 收件人
            'SUBJECT': u'[zhys] error from api',  # smtp 主题
            'USER': 'xxdebug@pv.cc',  # smtp账号
            'PASSWORD': 'jNy2dD5QWmxe19Xg',  # smtp账号密码
        },
        'FILE': {  # 文件日志， 如果没有对应的配置，则不开启
            # 'PATH': '/data/log/zhys/zhys-api.log',
            'PATH': './log/zhys-api.log',
            'MAX_BYTES': 1024 * 1024 * 10,  # 单个文件大小默认10M
            'BACKUP_COUNT': 5,  # 文件滚动数量，默认5
        }
    }

    DEFINES = {
        'SMSCAPTCHA_ACTION': {
            'REGISTER': 1,
            'RESETPWD': 2,
            'SET_NOTIFY_PHONE': 3,
            'bind_phone': 5,
            'switch_user': 6,
            'modify_phone_verify': 7,
            'modify_phone': 8,
            'oauth_bind_cancel': 9,
        }
    }
    CAPTCHA_SETTINGS = {
        'acts': ['register', 'resetpwd', 'login', 'ad_pic', 'set_notify_phone', 'bind_phone', 'switch_user',
                 'modify_phone_verify', 'modify_phone', 'oauth_bind_cancel'],
        'expires': 600,
    }
    CAPTCHA_EXPIRES = 60


class DebugAdminConfig(BaseConfig):
    SQLALCHEMY_DATABASE_URI = 'mysql://job:3b0qltxTrIUiIYKokXKc@127.0.0.1/zhys'
    LOGIN_URL = 'http://dev.admin.kdyoushu.com:7000/login.html'
    DEBUG = True
    PORT = 6790


class ReleaseAdminConfig(BaseConfig):
    SQLALCHEMY_DATABASE_URI = 'mysql://job:aC9TWr2BbgD6dMA9PoA8@127.0.0.1/zhys'
    LOGIN_URL = 'http://yd.xiaoxianetwork.com/login.html'
    PORT = 6792

    LOGGING = {  # 配置日志
        'SMTP': {  # 邮箱日志发送， 如果没有配置， 则不开启
            'HOST': 'smtp.exmail.qq.com',  # smtp 服务器地址
            'TOADDRS': ['linjf@pv.cc', 'mat@pv.cc', 'wangzq@pv.cc', 'liuzy@pv.cc'],  # smtp 收件人
            'SUBJECT': u'[zhys] error from admin',  # smtp 主题
            'USER': 'xxdebug@pv.cc',  # smtp账号
            'PASSWORD': 'jNy2dD5QWmxe19Xg',  # smtp账号密码
        },
        'FILE': {  # 文件日志， 如果没有对应的配置，则不开启
            'PATH': './log/zhys-admin.log',
            'MAX_BYTES': 1024 * 1024 * 10,  # 单个文件大小默认10M
            'BACKUP_COUNT': 5,  # 文件滚动数量，默认5
        }
    }


class DebugAppletConfig(BaseConfig):
    SQLALCHEMY_DATABASE_URI = 'mysql://root:root@127.0.0.1/zhys'
    BASE_URL = 'https://devzhysapi2.xiaoxianetwork.com'
    DEBUG = True
    PORT = 6793

    DEFINES = {
        'SMSCAPTCHA_ACTION': {
            'REGISTER': 1,
            'RESETPWD': 2,
            'SET_NOTIFY_PHONE': 3,
            'PHONERESETPWD': 4,
        }
    }
    CAPTCHA_SETTINGS = {
        'acts': ['register', 'resetpwd', 'login', 'ad_pic', 'set_notify_phone'],
        'expires': 600,
    }
    ALLOW_SOURCE = ['kaixing', 'riyue', 'yangyue', 'junengwan', 'maimeng']


class AppletConfig(BaseConfig):
    SQLALCHEMY_DATABASE_URI = 'mysql://job:aC9TWr2BbgD6dMA9PoA8@127.0.0.1/zhys'
    BASE_URL = 'https://api2.kdyoushu.com'
    PORT = 6794

    LOGGING = {  # 配置日志
        'SMTP': {  # 邮箱日志发送， 如果没有配置， 则不开启
            'HOST': 'smtp.exmail.qq.com',  # smtp 服务器地址
            'TOADDRS': ['linjf@pv.cc', 'mat@pv.cc', 'wangzq@pv.cc', 'liuzy@pv.cc'],  # smtp 收件人
            'SUBJECT': u'[zhys] error from api',  # smtp 主题
            'USER': 'xxdebug@pv.cc',  # smtp账号
            'PASSWORD': 'jNy2dD5QWmxe19Xg',  # smtp账号密码
        },
        'FILE': {  # 文件日志， 如果没有对应的配置，则不开启
            'PATH': './log/zhys-applet.log',
            'MAX_BYTES': 1024 * 1024 * 10,  # 单个文件大小默认10M
            'BACKUP_COUNT': 5,  # 文件滚动数量，默认5
        }
    }

    DEFINES = {
        'SMSCAPTCHA_ACTION': {
            'REGISTER': 1,
            'RESETPWD': 2,
            'SET_NOTIFY_PHONE': 3,
        }
    }
    CAPTCHA_SETTINGS = {
        'acts': ['register', 'resetpwd', 'login', 'ad_pic', 'set_notify_phone'],
        'expires': 600,
    }
    CAPTCHA_EXPIRES = 60
    ALLOW_SOURCE = ['kaixing', 'riyue', 'yangyue', 'yunyue', 'junengwan', 'maimeng', 'shenju', 'shidai']
