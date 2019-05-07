# coding: utf-8
import datetime
from base import db
from flask_login import UserMixin
from sqlalchemy.sql import func
import time
import random


class Image(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    filename = db.Column(db.String(120))
    url = db.Column(db.String(120))
    created = db.Column(db.DateTime(), server_default=func.now())

    def __init__(self, filename):
        self.filename = self.get_filename(filename)

    def get_filename(self, filename):
        tmp = filename.rsplit('.', 1)
        return str(random.randint(10000, 99999)) + '_%s_%s.%s' %(int(time.time()), random.randint(10000, 99999), tmp[1])


class AdminUser(UserMixin, db.Model):
    """后台用户"""
    id = db.Column(db.Integer(), primary_key=True)
    email = db.Column(db.String(20))
    password = db.Column(db.String(128))
    created = db.Column(db.DateTime(), server_default=func.now())
    group_id = db.Column(db.Integer, server_default='-1')

    def __init__(self, email, password, group_id):
        self.email = email
        self.password = password
        self.group_id = group_id

    def to_admin_dict(self):
        group = AdminUserGroup.query.filter_by(id=self.group_id).first()
        group_name = group.name if group else self.group_id
        return dict(id = self.id,
                    email = self.email,
                    group_id = group_name,
                    created = self.created.strftime('%Y-%m-%d %H:%M:%S'))



class AdminUserGroup(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))

    def __init__(self, name):
        self.name = name

    def to_admin_dict(self):
        return dict(id = self.id,
                    name = self.name)

class AdminGroupUrl(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer)
    url_id = db.Column(db.Integer)

    def __init__(self, group_id, url_id):
        self.group_id = group_id
        self.url_id = url_id

    def to_admin_dict(self):
        url = AdminUrl.query.filter_by(id=self.url_id).first()
        return dict(id = self.id,
                    group_id = self.group_id,
                    url_id = self.url_id,
                    path = url.path if url else '',
                    name = url.name if url else ''
                    )
        

class AdminUrl(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    path = db.Column(db.String(128), unique=True)
    name = db.Column(db.String(128))

    def __init__(self, path, name):
        self.path = path
        self.name = name

    def to_admin_dict(self):
        return dict(id = self.id,
                    name = self.name,
                    path = self.path)


class AdminLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    path = db.Column(db.String(128))
    created = db.Column(db.DateTime(), server_default=func.now())

    def __init__(self, user_id, path):
        self.user_id = user_id
        self.path = path

    def to_admin_dict(self):
        return dict(id = self.id,
                    user_id = self.user_id,
                    path = self.path,
                    created = self.created.strftime('%Y-%m-%d %H:%M:%S'))
