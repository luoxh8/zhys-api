#coding:utf-8
'''
    异步requests
'''
import redis
import hashlib
import time
import json
import requests
from celery import Celery
from applet_app import create_app_applet

flask_app = create_app_applet()
current_app = flask_app

app = Celery("async_req", broker=flask_app.config['CELERY_BROKER']['ASYNC_REQ'])
app.conf.update(
    CELERY_TASK_SERIALIZER='json',
    CELERY_ACCEPT_CONTENT=['json'],
    CELERY_RESULT_SERIALIZER='json',
    CELERYD_CONCURRENCY=2,
)
TaskBase = app.Task


class ContextTask(TaskBase):
    abstract = True

    def __call__(self, *args, **kwargs):
        with flask_app.app_context():
            return TaskBase.__call__(self, *args, **kwargs)


app.Task = ContextTask


@app.task
def get(url, params):
    resp = requests.get(url, params=params)
    print resp.text


@app.task
def post(url, data):
    resp = requests.post(url, data=data)
    print resp.text


@app.task
def send_custom_msg(data):
    """微信客服接口 发消息"""
    from lib.wxauth import send_custom_msg
    send_custom_msg(data)

