# coding: utf-8
from flask_login import LoginManager
from models.user import User

login_manager = LoginManager()


class UserInfo(object):
    def __init__(self, admin_id):
        self.id = admin_id

    def __unicode__(self):
        return u'%s' % (self.id)

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return self.id


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
