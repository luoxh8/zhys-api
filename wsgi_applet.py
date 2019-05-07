#coding:utf8
'''
    本文件用于wsgi启动
'''
import os, sys
import traceback
import ConfigParser
from applet_app import create_app_applet

# config.DebugAppletConfig, config.AppletConfig
try:
    cf = ConfigParser.ConfigParser()
    cf.read("conf/uwsgi_applet.ini")
    svrtype = cf.get("xx_server", "type")
    if svrtype == "dev":
        print "run with DebugAppletConfig"
        app = create_app_applet("config.DebugAppletConfig")
    else:
        print "run with AppletConfig"
        app = create_app_applet()
except Exception, e:
    print traceback.format_exc()
    app = create_app_applet()
