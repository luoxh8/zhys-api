#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
@Time    : 2017/10/23 上午10:29
@Author  : linjf
@File    : comic_import.py

Desc: 漫画本地数据导入

漫画列表---章节目录，按章节顺序存放图片
        |
        |-image_url.json 图片链接json
        |
        |-data.json 漫画数据json，不包含图片url
'''
import os
import json
import datetime
import time
import random
from qiniu import Auth, put_data

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


COMICS_PATH = '/data/comic_datas/json_data_maimeng'
# COMICS_PATH = '/Users/linjianfeng/工作/广州飞屋/口袋有书/文件/漫画书籍/麦萌/格式化整理'


def upload_img(filename, data, bucket_name='zhys'):
    """上传图片至七牛云空间（数据流形式）"""
    cfg = dict(
        access_key = 'mD9rPwwMevxOL3uC38eOAfno4TZxTjKXEBub4vAk',
        secret_key = 'v1M5HVJpN8s2PtGEorH8Wj6NyiEKgnei9VCQpMZ_',
        buckets = {
            'zhys': 'ssl.kdyoushu.com'
        }
    )
    access_key = cfg['access_key']
    secret_key = cfg['secret_key']
    q = Auth(access_key, secret_key)
    token = q.upload_token(bucket_name, filename)
    ret, info = put_data(token, filename, data)
    assert ret['key'] == filename
    host = cfg['buckets'][bucket_name]
    return 'https://%s/%s'%(host, filename)

class ComicDataJson():
    """漫画书籍文字数据录入，生成json文件"""

    def generate_json(self):
        json_file_path = os.path.join(COMICS_PATH, '15安家有女_14/data.json')
        print json_file_path

        source = 'maimeng'  # 来源
        book_id = 14
        now_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        data = {
            'source': source,
            'channel_book_id': u'%s:%s' % (source, book_id),
            'book_name': u'安家有女',
            'cate_id': -1,
            'channel_type': 0,
            'author_name': u'神棍远',
            'is_publish': 2,  # 是否出版（1：是；2：否）
            'status': 2,  # 连载状态（1：已完结；2：未完结）
            'intro': u'''镖局大小姐安佑菱首次个人出征——女扮男装护送武林盟主的‘宝物’！一路上遇到的，都是狠角色啊！到底为啥！难道得此‘宝物’者可称霸武林吗？？保护物件好说，身边还有个武力值几乎为零的跟班呢！干这行容易吗？可是，如果留在家里，大概会继续和爹因为结婚的事而争吵……安幼菱：我吵不过还躲不过吗？''',
            'create_time': now_str,
            'update_time': now_str,
            'money': 0,
            'money_start_index': 0,
        }

        with open(json_file_path, 'w') as f:
            f.write(json.dumps(data))

        return 'success'


class ComicImport():
    """漫画数据导入类"""

    DB_SESSION = None

    def __init__(self):
        engine = create_engine('mysql://job:aC9TWr2BbgD6dMA9PoA8@localhost/zhys?charset=utf8', echo=True)
        DBSession = sessionmaker(bind=engine)
        self.DB_SESSION = DBSession()

    def _ignore_sys_file(self, file_name):
        """忽略部分特殊文件"""
        if file_name in ['.DS_Store', 'data.json', 'image_url.json', 'image_url_sub.json']:
            return True
        return False

    def _load_json(self, path):
        """加载json文件"""
        data = None
        data_json = ''
        with open(path) as f:
            data_json = f.readline()
        try:
            data = json.loads(data_json)
        except:
            pass
        return data

    def _upload_img(self, file_path):
        """上传指定路径文件"""
        url = ''
        with open(file_path) as f:
            filename = 'comic_img_%s%s.%s' % (
                datetime.datetime.now().strftime('%Y%m%d%H%M%S'),
                random.randint(10000, 99999),
                file_path.split('.')[-1])
            url = upload_img(filename, f.read())
        return url

    def _insert_into_table(self, image_item, data_item):
        """sql数据插入"""
        channel_book_id = data_item['channel_book_id']  # 渠道书籍id 渠道名:书籍id
        book_name = data_item['book_name']  # 书籍名称
        cate_id = data_item['cate_id']  # 书籍分类ID
        channel_type = data_item['channel_type']  # 书籍频道（1：男；2: 女 3: 出版 0: 无此属性默认为0）
        author_name = data_item['author_name']  # 作者
        chapter_num = len(image_item['data'])  # 章节数量
        is_publish = data_item['is_publish']  # 是否出版（1：是；2：否）
        status = data_item['status']  # 连载状态（1：已完结；2：未完结）
        create_time = data_item['create_time']  # 创建时间（第三方）
        cover = image_item['cover']  # 封面图片（链接）
        intro = data_item['intro']  # 简介
        update_time = data_item['update_time']  # 更新时间
        source = data_item['source']  # 来源

        # 查询是否已录入该书籍
        sql_query_book = 'select book_id from book where channel_book_id=:channel_book_id'
        book_id = self.DB_SESSION.execute(sql_query_book, {"channel_book_id": channel_book_id}).scalar()
        if not book_id:
            # 添加书籍
            sql_add_book = 'insert into book(channel_book_id, book_name, cate_id, channel_type, \
                author_name, chapter_num, is_publish, status, create_time, cover, intro, update_time, \
                source, word_count, is_comic) values("%s", "%s", %d, %d, "%s", %d, %d, %d, "%s", "%s", \
                "%s", "%s", "%s", 0, 1)' \
                           % (channel_book_id, book_name, cate_id, channel_type, author_name, chapter_num,
                              is_publish, status, create_time, cover, intro, update_time, source)

            self.DB_SESSION.execute(sql_add_book)
            self.DB_SESSION.commit()

            # 查找新增书籍录入ID（book_id）
            book_id = self.DB_SESSION.execute(sql_query_book, {"channel_book_id": channel_book_id}).scalar()
            if not book_id:
                print u'书籍查询失败'
                return

        # 查询已录入最新章节
        sql_query_last_chapter = 'select chapter_id from book_chapters where book_id=:book_id order by chapter_id desc limit 1'
        last_chapter_index = 0
        last_chapter = self.DB_SESSION.execute(sql_query_last_chapter, {"book_id": book_id}).fetchone()
        if last_chapter:
            last_chapter_index = int(last_chapter.chapter_id)

        # 录入章节信息
        sql_add_chapter = 'insert into book_chapters(book_id, volume_id, chapter_id, chapter_name, ' \
                          'word_count, content_url, money, create_time, update_time) values(:book_id, ' \
                          '1, :chapter_id, :chapter_name, 0, :content_url, :money, :create_time, :update_time)'

        chapters = image_item['data']
        for i in range(len(chapters)):
            chapter = chapters[i]
            chapter_index = int(chapter['chapter_index'])

            if chapter_index <= last_chapter_index:
                continue

            tmp_data = {
                "book_id": book_id,
                "chapter_id": chapter_index,
                "chapter_name": u"第%d话" % chapter_index,
                "content_url": '|'.join(chapter['image_urls']),
                "money": data_item['money'] if (i + 1) >= data_item['money_start_index'] else 0,
                "create_time": create_time,
                "update_time": update_time,
            }
            self.DB_SESSION.execute(sql_add_chapter, tmp_data)
        self.DB_SESSION.commit()

    def fetch_files(self):
        """遍历漫画列表目录，生成相应格式数据"""
        files = os.listdir(COMICS_PATH)
        comic_folders = []

        # 漫画一级目录遍历
        for f in files:
            if self._ignore_sys_file(f):
                continue
            path = os.path.join(COMICS_PATH, f)
            comic_folders.append(path)

        datas = []
        # 图片信息获取，遍历漫画目录
        for root_path in comic_folders:
            files = os.listdir(root_path)
            comic_item = []
            cover = ''

            # 进入漫画目录
            chapter_index = 0
            sort_files = []
            for f in files:
                if self._ignore_sys_file(f):
                    continue

                if f.find('.jpg') > 0 or f.find('.png') > 0:
                    cover = os.path.join(root_path, f)
                    continue

                sort_files.append(f)
            sort_files.sort(key=lambda x: int(x))

            for f in sort_files:
                detail_path = os.path.join(root_path, f)

                chapter_index += 1
                tmp_item = {'chapter_index': chapter_index, 'image_urls': []}

                image_files = os.listdir(detail_path)
                tmp_l = []
                for image_file in image_files:
                    if self._ignore_sys_file(image_file):
                        continue
                    tmp_l.append(image_file)
                tmp_l.sort(key=lambda x: int(x.split('.')[0]))
                tmp_item['image_urls'] = [os.path.join(detail_path, item) for item in tmp_l]

                comic_item.append(tmp_item)

            datas.append({
                'path': root_path,
                'cover': cover,
                'data': comic_item,
            })
        return datas

    def generate_json_file(self, upload_image=False):
        """生成json数据文件"""
        """
            存在image.json文件时，进行检测，根据字典最后一个元素进行匹配更新
        """
        datas = self.fetch_files()
        for item in datas:
            if upload_image:
                json_file_path = os.path.join(item['path'], 'image_url.json')
            else:
                json_file_path = os.path.join(item['path'], 'image_url_sub.json')
            print json_file_path

            if upload_image and os.path.isfile(json_file_path):
                # 已存在json文件，进行更新检测
                print '发现json文件，image_url.json，路径为：', json_file_path
                old_datas = self._load_json(json_file_path)
                old_data_last_index = old_datas['data'][-1]['chapter_index']
                new_data_last_index = item['data'][-1]['chapter_index']
                if new_data_last_index > old_data_last_index:
                    # 进行章节数据更新
                    for new_data in item['data']:
                        if new_data['chapter_index'] <= old_data_last_index:
                            continue

                        tmp_urls = []
                        print new_data['chapter_index']
                        for image_url in new_data['image_urls']:
                            url = self._upload_img(image_url)
                            print url
                            tmp_urls.append(url)
                            time.sleep(0.1)
                        new_data['image_urls'] = tmp_urls
                        print new_data['image_urls']
                        old_datas['data'].append(new_data)
                    # 赋值替换
                    item = old_datas

            elif upload_image and not os.path.isfile(json_file_path):
                print item['cover']
                item['cover'] = self._upload_img(item['cover'])
                for chapter in item['data']:
                    new_image_urls = []
                    print chapter['chapter_index']
                    for image_url in chapter['image_urls']:
                        url = self._upload_img(image_url)
                        print url
                        new_image_urls.append(url)
                        time.sleep(0.1)
                    chapter['image_urls'] = new_image_urls
                    print chapter['image_urls']

            with open(json_file_path, 'w') as f:
                f.write(json.dumps(item))

    def execute_insert(self):
        """加载"""
        files = os.listdir(COMICS_PATH)
        comic_folders = []

        # 漫画一级目录遍历
        for f in files:
            if self._ignore_sys_file(f):
                continue
            path = os.path.join(COMICS_PATH, f)
            comic_folders.append(path)

        # 查找漫画根目录下是否存在图片数据文件（image_url.json）
        for path in comic_folders:
            image_json_file = os.path.join(path, 'image_url.json')
            data_json_file = os.path.join(path, 'data.json')
            if os.path.isfile(image_json_file) and os.path.isfile(data_json_file):
                image_item = self._load_json(image_json_file)
                data_item = self._load_json(data_json_file)
                self._insert_into_table(image_item, data_item)


# 生成文本信息数据文件
data_import = ComicDataJson()
#data_import.generate_json()

# 生成图片数据文件，以及执行数据库插入操作
item = ComicImport()
# print item.fetch_files()
#item.generate_json_file(False)
#item.generate_json_file(True)
#item.execute_insert()


