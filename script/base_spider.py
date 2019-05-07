# -*- coding: utf-8 -*-
"""
Doc: 
Created by MT at 2017/10/16
"""
import requests
from requests.adapters import HTTPAdapter
import abc


class BaseBookSpider(object):
    """书籍爬虫"""
    # 请求失败时重试三次
    session = requests.Session()
    session.mount('', HTTPAdapter(max_retries=3))

    @abc.abstractproperty
    def CHANNEL_NAME(self):
        pass

    def req(self, url, retry=3, **kwargs):
        """请求对方接口"""
        print 'API=== %s ===' % url, kwargs

        # kwargs['url'] = url
        # resp = self.session.get('http://dev.api.kdyoushu.com:7000/other/tmp_proxy', params=kwargs)
        resp = self.session.get(url, params=kwargs)

        retry = retry - 1
        if not resp.text and retry > 0:
            return self.req(url, retry=retry, **kwargs)
        print 'API=== return', resp.text[:100]
        return resp

    def gen_channel_bind_id(self, bind_id):
        """生成渠道相关id"""
        return '%s:%s' % (self.CHANNEL_NAME, bind_id)

    def finish_callback(self):
        """书籍成功添加完成时回调"""
        pass

    @abc.abstractmethod
    def get_book_list(self, local_cate_dict):
        """获取书籍列表"""
        pass

    @abc.abstractmethod
    def get_volume_chapter_list(self, real_book_id, max_cid, local_book_id):
        """获取卷和章节列表"""
        pass

    def need_update_chap_num(self):
        """是否需要更新章节数量"""
        return False

    def get_chap_num(self, channel_book_id):
        """获取章节数量"""
        return 0
