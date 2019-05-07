#coding:utf8
from flask import current_app
from redis import StrictRedis
import time

def init_app(app):
    cfg = app.config['REDIS_SETTINGS']
    app.redis = StrictRedis(cfg['HOST'], cfg['PORT'])
    return app.redis

def count_online(rds, key, item, dur=60,  expires=600):
    ts = int(time.time())
    rds_key = '%s-%d'%(key, ts // dur)
    rds.sadd(rds_key, item)
    rds.expire(rds_key, expires)

def count(rds, key, inc=1,  dur=60, expires=600):
    ts = int(time.time())
    rds_key = '%s-%d'%(key, ts // dur)
    rds.incr(rds_key, inc)
    rds.expire(rds_key, expires)

def set_cache(key, value, expires=300):
    rds = current_app.redis
    rds.setex(key,  expires, value)
#    rds.set(key, value)
#    rds.expire(key, expires)

def get_cache(key, expires=300, refresh_expires=True):
    rds = current_app.redis
    if refresh_expires:
        rds.expire(key, expires) 
    return rds.get(key)

