# coding=utf-8

from flask import Blueprint, request
from flask_login import login_required
from models import Banner
from models import ChannelType
from models import Topic
from models import ChannelData
from models import BookShelfName 
from models import db
import json
from lib import utils

bp = Blueprint("other", __name__)

@bp.route('/index')
def index():
    return 'other is ok.'

@bp.route('/banner_list')
@login_required
def banner_list():
    page_no = request.args.get("page_no", 1, int)
    num = request.args.get("num", 20, int)
    sql = 'select count(*) from banner'
    total = db.session.execute(sql).scalar() or 0
    banners = Banner.query.paginate(page_no, per_page=num, error_out=False).items
    banner_list = [banner.to_admin_dict() for banner in banners]
    return json.dumps({'code':0, 'data': banner_list, 'total': total})

@bp.route('/add_banner', methods=['POST'])
@login_required
def add_banner():
    data = request.form.to_dict()
    bn = Banner(data)
    db.session.add(bn)
    db.session.commit()
    return json.dumps({'code': 0, 'data': bn.to_admin_dict()})

@bp.route('/update_banner', methods=['POST'])
@login_required
def update_banner():
    _id = request.form.get('id', 0, int)
    bn = Banner.query.filter_by(id=_id).first()
    if not bn:
        return json.dumps({'code': 1, 'msg': 'id: %s banner is not exist.' %(_id)})
    data = request.form.to_dict()

    bn.update(data)
    db.session.add(bn)
    db.session.commit()
    return json.dumps({'code': 0, 'data': bn.to_admin_dict()})

@bp.route('/channel_type_info', methods=['GET'])
@login_required
def channel_type_info():
    _id = request.form.get('channel_code', 0, int) or request.args.get('channel_code', 0, int)
    print _id
    ct = ChannelType.query.filter_by(id=_id).first()
    if not ct:
        return json.dumps({'code': 1, 'msg': 'id: %s channel_type is not exist.' %(_id)})
    return json.dumps({'code': 0, 'data': ct.to_admin_dict()})

@bp.route('/update_channel_type', methods=['POST', 'GET'])
@login_required
def update_channel_type():
    _id = request.form.get('channel_code', 0, int) or request.args.get('channel_code', 0, int)
    ct = ChannelType.query.filter_by(id=_id).first()
    if not ct:
        return json.dumps({'code': 1, 'msg': 'id: %s channel_type is not exist.' %(_id)})
    if request.method == 'GET':
        data = request.args.to_dict()
    else:
        data = request.form.to_dict()

    ct.update(data)
    db.session.add(ct)
    db.session.commit()
    return json.dumps({'code': 0, 'data': ct.to_admin_dict()})

@bp.route('/add_channel_type', methods=['POST', 'GET'])
@login_required
def add_channel_type():
    if request.method == 'GET':
        data = request.args.to_dict()
    else:
        data = request.form.to_dict()
    ct = ChannelType.query.filter_by(name=data['name']).first()
    if ct:
        return json.dumps({'code': 1, 'msg': '%s 已存在.' %data['name']})

    ct = ChannelType(data)
    db.session.add(ct)
    db.session.commit()
    return json.dumps({'code': 0, 'data': ct.to_admin_dict()})

@bp.route('/channel_type_list', methods=['POST', 'GET'])
@login_required
def channel_type_list():
    page_no = request.args.get("page_no", 1, int)
    num = request.args.get("num", 20, int)
    platform = request.args.get('platform')
    sql = 'select count(*) from channel_type'
    total = db.session.execute(sql).scalar() or 0
    channeltypes = ChannelType.query
    if platform:
        channeltypes = channeltypes.filter_by(platform=platform)
    channeltypes = channeltypes.order_by(
                        ChannelType.ranking.desc()).paginate(page_no,
                                per_page=num, error_out=False).items
    data = [ i.to_admin_dict() for i in channeltypes ]
    return json.dumps({'code': 0, 'data': data})

@bp.route('/topic_info', methods=['GET'])
@login_required
def topic_info():
    _id = request.args.get('id', 0, int)
    obj = Topic.query.filter_by(id=_id).first()
    if not obj:
        return json.dumps({'code': 1, 'msg': 'id: %s is not exist.' %(_id)})
    return json.dumps({'code': 0, 'data': obj.to_admin_dict()})

@bp.route('/update_topic', methods=['POST', 'GET'])
@login_required
def update_topic():
    _id = request.form.get('id', 0, int) or request.args.get('id', 0, int)
    obj = Topic.query.filter_by(id=_id).first()
    if not obj:
        return json.dumps({'code': 1, 'msg': 'id: %s is not exist.' %(_id)})
    if request.method == 'GET':
        data = request.args.to_dict()
    else:
        data = request.form.to_dict()

    obj.update(data)
    db.session.add(obj)
    db.session.commit()
    return json.dumps({'code': 0, 'data': obj.to_admin_dict()})

@bp.route('/add_topic', methods=['POST', 'GET'])
@login_required
def add_topic():
    if request.method == 'GET':
        data = request.args.to_dict()
    else:
        data = request.form.to_dict()

    obj = Topic(data)
    db.session.add(obj)
    db.session.commit()
    return json.dumps({'code': 0, 'data': obj.to_admin_dict()})

@bp.route('/topic_list', methods=['POST', 'GET'])
@login_required
def topic_list():
    page_no = request.args.get("page_no", 1, int)
    num = request.args.get("num", 20, int)
    sql = 'select count(*) from topic'
    total = db.session.execute(sql).scalar() or 0
    topics = Topic.query.order_by(Topic.modified.asc()).paginate(page_no, per_page=num, error_out=False).items
    data = [ i.to_admin_dict() for i in topics ]
    return json.dumps({'code': 0, 'data': data})

@bp.route('/channel_data_list', methods=['POST', 'GET'])
@login_required
def channel_data_list():
    channel_code =  request.args.get('channel_code', 0, int)
    if not channel_code:
        return json.dumps({'code': 1, 'msg': 'channel_code not exist.'})
    banners = ChannelData.query.filter_by(channel_code=channel_code, class_name='banner')
    banners = banners.order_by(ChannelData.ranking.asc())
    banner_list = [ i.to_admin_dict() for i in banners ]

    topics = ChannelData.query.filter_by(channel_code=channel_code, class_name='topic')
    topics = topics.order_by(ChannelData.ranking.asc())
    topic_list = [ i.to_admin_dict() for i in topics ]


    bookshelfnames = ChannelData.query.filter_by(channel_code=channel_code, class_name='book_shelf_name')
    bookshelfnames = bookshelfnames.order_by(ChannelData.ranking.asc())
    bookshelfname_list = [ i.to_admin_dict() for i in bookshelfnames ]
    data = dict(banners=banner_list, topics=topic_list, bookshelfnames=bookshelfname_list)

    return json.dumps({'code': 0, 'data': data})

@bp.route('/del_channel_data', methods=['POST', 'GET'])
@login_required
def del_channel_data():
    _id = request.args.get('id', 0, int) or request.form.get('id', 0, int)
    sql = 'delete from channel_data where id=%s' %(_id)
    print sql
    db.session.execute(sql)
    db.session.commit()
    return json.dumps({'code': 0, 'msg': 'ok.'})

@bp.route('/add_channel_data', methods=['POST', 'GET'])
@login_required
def add_channel_data():
    class_id = request.args.get('class_id', 0, int) or request.form.get('class_id', 0, int)
    class_name = request.args.get('class_name', '') or request.form.get('class_name', '')
    channel_code = request.args.get('channel_code', 0, int) or request.form.get('channel_code', 0, int)
    ranking = request.args.get('ranking', 0, int) or request.form.get('ranking', 0, int)
    if class_id and class_name in ('banner', 'topic', 'book_shelf_name') and channel_code:
        if not ChannelType.query.filter_by(id=channel_code).first():
            return json.dumps({'code': 1, 'msg': 'channeltype not exist.'})
        if class_name == 'banner' and not Banner.query.filter_by(id=class_id).first():
            return json.dumps({'code': 2, 'msg': 'banner not exist.'})
        if class_name == 'topic' and not Topic.query.filter_by(id=class_id).first():
            return json.dumps({'code': 3, 'msg': 'topic not exist.'})
        if class_name == 'book_shelf_name' and not BookShelfName.query.filter_by(id=class_id).first():
            return json.dumps({'code': 3, 'msg': 'bookshelfname not exist.'})
        cd = ChannelData(class_id=class_id, channel_code=channel_code, class_name=class_name, ranking=ranking)
        db.session.add(cd)
        db.session.commit()
        return json.dumps({'code': 0, 'data': cd.to_admin_dict()})
    else:
        return json.dumps({'code': 4,
            'msg': 'class_id: %s, class_name: %s, channel_code: %s' %(class_id, class_name, channel_code)})
