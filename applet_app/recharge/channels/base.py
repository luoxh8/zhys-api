# -*- coding: utf-8 -*-
"""
Doc:

Created on 2017/9/1
@author: MT
"""
import abc


class BasePay(object):
    __metaclass__ = abc.ABCMeta

    SERVICE_CFG = []  # 支持的支付类型

    @abc.abstractmethod
    def verify(self):
        """
        验证订单 返回订单Id和订单金额 单位分
        """
        pass

    def post_order(self, user_id, order_id, money, notify_url, pay_type, **kwargs):
        """提交订单"""
        return {}
