#coding:utf8
'''
    本文件用于wsgi启动
'''
from applet_app import create_app_applet


app = create_app_applet("config.DebugAppletConfig")


if __name__ == '__main__':
    app.run()
