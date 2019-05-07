#coding:utf8
'''
    本文件用于wsgi启动
'''
import os, sys
import traceback
import ConfigParser
from main_app import create_app_main

# config.DebugConfig, config.ReleaseConfig
try:
    cf = ConfigParser.ConfigParser()
    cf.read("conf/uwsgi_api.ini")
    svrtype = cf.get("xx_server", "type")
    if svrtype == "dev":
        print "run with DebugConfig"
        app = create_app_main("config.DebugConfig")
    else:
        app = create_app_main()
except Exception, e:
    print traceback.format_exc()
    app = create_app_main()
