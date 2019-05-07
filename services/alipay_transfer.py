# coding: utf-8
import requests
import base64
import json
import datetime

from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from Crypto.Cipher import PKCS1_OAEP
from Crypto.Hash import SHA, MD5
from Crypto.Random import atfork

from models import db, TransferOrder


ALIPAY_URL = 'https://openapi.alipay.com/gateway.do'
ALIPAY_APPID = '2017100909208083'

RSA_PRIVATE_KEY = '''-----BEGIN RSA PRIVATE KEY-----
MIICXQIBAAKBgQDMKICkJharL0jSIl5RyUdiqgrm3Wad5CfeQUA+Q7QpxvbDkcx4
rb0xFJ6C+dycMB6shZutdSCvdUn6j6XQGGyN0aBYWqvzG6Qbhdb28NsXYXJbXKYv
3cFbRdJdtrLjgBfPDgey1FTy4NJV/HXIIZ0hp1pUkQEQL41euccsyBpyzQIDAQAB
AoGADjIex8syNlMCYEIthshVI2IpgeYRNZdgwk6NNgclJuaD0BN6QUXratdBMmBH
W8Do0Rw1N/l1/V1NeJO2duLL4WzP3BLuCSFj50RB2ojw6P2muh9zVc4JupgZJYvk
0Oyz3wi6l8zlwfCbQ2UmYE1rjWl0Z7aM8pj0a8tFn6Mo+i0CQQDmOnbv6gG0rTo+
Iav/7lPx9EnQf/ppHzHGHx4Q0vFuocs36LheGIIkshDsb6/oJUESbLmzkz3MeRge
duAJX1tDAkEA4wL1bY9vqjTrRUkpwHmakCW23gewsAn/mast1mRA2xfDpfEbopW3
GsX+JMQd90yvtQQCoH7kM2I1NX82gs+wrwJAFVSlYGUV8195XfhQr02tiWVQ0XiK
AuNZATow1u40YEOtSGjPbChpJm05FC7k5WVOOh7ItdKWjzNJAMmSyEuFcQJBAM8o
GwkgtHixE+VFL5maHqbeE7Mnd2Adr6buY8TZ9ak5VWuvy1UhpFcFSLcKVIIg89KO
10rYoKwXOZEZBoh2uLcCQQDcfiPzIakGYwaaQsb7IxkNXc/HCIv5GqqBLlMniuQ4
CGl0nslXyXFNjzZ9szltpMmWqErGS58ozPdvJ/Hab1aT
-----END RSA PRIVATE KEY-----'''

ALIPAY_RSA_PUBLIC_KEY = '''-----BEGIN PUBLIC KEY-----
MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQDDI6d306Q8fIfCOaTXyiUeJHkr
IvYISRcc73s3vF1ZT7XN8RNPwJxo8pWaJMmvyTn9N4HQ632qJBVHf8sxHi/fEsra
prwCtzvzQETrNRwVxLO5jVmRGi60j8Ue1efIlzPXV9je9mkjzOmdssymZkh2QhUr
CmZYI/FCEa3/cNMW0QIDAQAB
-----END PUBLIC KEY-----'''


def get_sign(params):
    ''' 生成签名 '''
    ks = params.keys()
    ks.sort()
    params_str = ''
    for k in ks:
        v = params[k]
        if k not in ('sign') and v != '':
            params_str += '%s=%s&' % (k, v)
    params_str= params_str[:-1]
    
    params_str = SHA.new(params_str)
    private_key = RSA.importKey(RSA_PRIVATE_KEY)
    atfork()
    signer = PKCS1_v1_5.new(private_key)
    _sign = signer.sign(params_str)
    _sign=base64.b64encode(_sign)

    return _sign


def verify_sign(data, sign):
    tmp_str = '{'
    for (k, v) in data.items():
        tmp_str += '"%s":"%s",' % (k, v)
    tmp_str = tmp_str[:-1] + '}'
    print tmp_str
    pub_key = RSA.importKey(ALIPAY_RSA_PUBLIC_KEY)
    verifier = PKCS1_v1_5.new(pub_key)
    new_str = SHA.new(tmp_str)
    x = verifier.verify(new_str, base64.b64decode(sign))
    return x



def execute_alipay_transfer(account, real_name, amount, bind_id):
    ''' 支付宝api请求调用 '''
    from uuid import uuid1
    order_id = uuid1().hex

    # 添加支付宝转账订单
    transfer_order = TransferOrder(order_id, amount * 100, account, real_name, bind_id, 'bonus_activity')
    db.session.add(transfer_order)
    db.session.commit()

    data = {
        'app_id': ALIPAY_APPID,
        'method': 'alipay.fund.trans.toaccount.transfer',
        'format': 'json',
        'charset': 'utf-8',
        'sign_type': 'RSA',
        'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'version': '1.0',
        'biz_content': json.dumps({
            'out_biz_no': order_id,
            'payee_type': 'ALIPAY_LOGONID',
            'payee_account': account,
            'amount': str(amount),
            'payer_show_name': '测试付款方姓名',  # 付款方姓名
            'payee_real_name': real_name,  # 收款方真实姓名
            'remark': '%s元' % str(amount),  # 转账备注（商品名称）
        })
    }
    data['sign'] = get_sign(data)

    resp = requests.get(ALIPAY_URL, params=data)
    print 'transfer result is', resp.text

    from collections import OrderedDict
    resp_dict = json.loads(resp.text, object_pairs_hook=OrderedDict)
    if not resp_dict.has_key('alipay_fund_trans_toaccount_transfer_response'):
        return json.dumps({'code': -1, 'msg': u'response error'})
    if not resp_dict['alipay_fund_trans_toaccount_transfer_response'].has_key('code'):
        return json.dumps({'code': -1, 'msg': u'response error'})

    response_data = resp_dict['alipay_fund_trans_toaccount_transfer_response']
    if response_data['code'] != '10000':
        print 'sub_msg is %s, order_id is %s' % (response_data['sub_msg'], response_data['out_biz_no'])
        return json.dumps({'code': -1, 'msg': 'code is not 10000'})

    flag_verify = verify_sign(response_data, resp_dict['sign'])
    if not flag_verify:
        return json.dumps({'code': -1, 'msg': 'sign verify error'})

    # 更新订单状态
    order_id = response_data['out_biz_no']
    print 'transfer order id is %s' % order_id
    
    item = TransferOrder.query.filter_by(order_id=order_id).first()
    if item:
        item.status = 1
        db.session.commit()
    
    return json.dumps({'code': 0})


if __name__ == '__main__':
    from uuid import uuid1
    execute_alipay_transfer(uuid1().hex, '737411721@qq.com', '林坚烽1', 1)
