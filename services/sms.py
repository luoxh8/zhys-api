#coding:utf-8
'''
    短信发送队列
'''
import redis
import hashlib
import time
import json
import requests
from celery import Celery
from wsgi_api import app as flask_app

app = Celery("tasks", broker=flask_app.config['CELERY_BROKER']['SMS'])
app.conf.update(
    CELERY_TASK_SERIALIZER='json',
    CELERY_ACCEPT_CONTENT=['json'],
    CELERY_RESULT_SERIALIZER='json',
    CELERYD_CONCURRENCY=2,
)

@app.task
def send_sms(phone, content):
    '''
        发送短信
        phone 手机号
        content 短信内容
    '''
    ret_msg = 'msg is %s, phone is %s, ' % (content, phone)
    if send_sms_xiangxun(phone, content):
        ret_msg += 'send msg success.'
    else:
        ret_msg += 'send msg failed.'
    return ret_msg


def get_md5_str(input_str):
    m = hashlib.md5()
    m.update(input_str)
    return m.hexdigest()


def send_sms_xiangxun(tel, msg):
    ''' 享迅 '''
    print 'enter send_sms_xiangxun'
    params = {
        'account': 's11030012',
        'password': get_md5_str('abc123').upper(),
        'mobile': tel,
        'content': msg + u'【口袋有书】',
        'requestId': str(time.time()),
        'extno': '',
    }
    print json.dumps(params)
    url = 'http://www.17int.cn/xxsmsweb/smsapi/send.json'
    headers = {'Accept': 'application/json', 'Content-Type': 'application/json;charset=utf-8'}
    try:
        resp = requests.post(url, data=json.dumps(params), headers=headers)
        print resp.text, resp.status_code
        resp_decode = resp.json()
        return int(resp_decode['status']) == 10
    except:
        print 'xiangxun err'
        return False
