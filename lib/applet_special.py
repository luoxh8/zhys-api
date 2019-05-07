#coding:utf8

from flask import current_app, request

def is_applet_special():
    return request.args.get('platform') == 'applet' and request.args.get('v') in ['1.1.5']
