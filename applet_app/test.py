# coding: utf-8
import ujson as json
from flask import Blueprint


test = Blueprint('test', __name__)


@test.route('/hello')
def hello():
    return 'hello'
