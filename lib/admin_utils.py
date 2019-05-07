import requests
from flask import current_app
from models import AdminUser, AdminUserGroup, AdminUrl, AdminGroupUrl

def requests_get(url, params): 
    return requests.get(url, params=params)

def requests_post(url, data):
    return requests.post(url, data=data)

def requests_all(url, data, action):
    if action == 'get':
        return requests_get(url, data)
    elif action == 'post':
        return requests_post(url, data)


def get_urls(group_id):
    redis = current_app.redis
    key = "group-url-%s" % group_id
    paths = redis.lrange(key, 0,-1)
    if not paths:
        paths = []
        group_urls = AdminGroupUrl.query.filter_by(group_id=group_id).all()
        for group_url in group_urls:
            url = AdminUrl.query.get(group_url.url_id)
            if url:
                paths.append(url.path)
        if paths:
            redis.lpush(key, *paths)
            redis.expire(key, 3600)
    return paths

def del_group_urls_redis(group_id):
    key = "group-url-%s" % group_id
    current_app.redis.delete(key)
