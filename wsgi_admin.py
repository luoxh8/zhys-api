# coding:utf8
'''
    本文件用于wsgi启动
'''
import ConfigParser
import traceback

from admin_app import create_app_admin

# config.DebugAdminConfig, config.ReleaseAdminConfig
try:
    cf = ConfigParser.ConfigParser()
    cf.read("conf/uwsgi_admin.ini")
    svrtype = cf.get("xx_server", "type")
    if svrtype == "dev":
        print "run with DebugAdminConfig"
        app = create_app_admin("config.DebugAdminConfig")
    else:
        app = create_app_admin()
except Exception, e:
    print traceback.format_exc()
    app = create_app_admin()
