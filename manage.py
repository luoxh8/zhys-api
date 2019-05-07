# coding: utf-8
'''
    python manage.py -a main（admin） -d run
'''
from flask import Flask
from flask_migrate import Migrate, MigrateCommand
from flask_script import Manager, Command

import models
from admin_app import create_app_admin
from applet_app import create_app_applet
from main_app import create_app_main

manager = Manager(Flask(__name__))


class MyServer(Command):
    def __call__(self, app, *args, **kwargs):
        app.run(host='0.0.0.0', port=app.config['PORT'])


def manager_app(app_name, debug=False):
    print '%s At %s mode' % (app_name, ('debug' if debug else 'normal'))
    if app_name == 'main':
        config = 'config.DebugConfig' if debug else 'config.ReleaseConfig'
        app = create_app_main(config)
    elif app_name == 'admin':
        config = 'config.DebugAdminConfig' if debug else 'config.ReleaseAdminConfig'
        app = create_app_admin(config)
    elif app_name == 'applet':
        config = 'config.DebugAppletConfig' if debug else 'config.AppletConfig'
        app = create_app_applet(config)
    migrate = Migrate(app, models.db)
    return app


manager = Manager(manager_app)

manager.add_option('-a', '--app', dest='app_name', default='main', choices=['main', 'admin', 'applet'])
manager.add_option('-d', '--debug', dest='debug', action='store_true')

manager.add_command('run', MyServer())
manager.add_command('db', MigrateCommand)

if __name__ == '__main__':
    manager.run()
