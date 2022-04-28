# -*- coding:UTF-8 -*-
# !/usr/bin/env python
import hashlib
import hmac
import json
import logging
import re
import time
import traceback
from collections import namedtuple
from datetime import datetime

import requests

logger = logging.getLogger(__name__)


def get_utc_str():
    return datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'


def http_post_request(url, params, timeout=10):
    # lang valueRange ： en_US,ko_KR,zh_CN
    header = {'lang': 'en_US'}
    response = requests.post(url, params, timeout=timeout, headers=header)
    if response.status_code == 200:
        return response.json()
    else:
        return


def http_get_request(url, params, timeout=10):
    # lang valueRange ： en_US,ko_KR,zh_CN
    header = {'lang': 'zh_CN'}
    response = requests.get(url, params, timeout=timeout, headers=header)
    if response.status_code == 200:
        return response.json()
    else:
        return


class HotCoin:
    def __init__(self, base_url='https://openapi.vaex.tech/sapi/v1/', symbol=""):
        self.base_url = base_url
        self.symbol = symbol
        if not self.symbol:
            logging.error("Init error, please add symbol")
        requests.packages.urllib3.disable_warnings()

    def auth(self, key, secret):
        # self.key = bytes(key,'utf-8')
        self.key = key
        self.secret = bytes(secret, 'utf-8')

    def public_request(self, method, api_url, **payload):
        """request public url"""
        r_url = self.base_url + api_url
        # print(r_url)
        try:
            r = requests.request(method, r_url, params=payload)
            r.raise_for_status()
        except requests.exceptions.HTTPError as err:
            logging.error(err)
        if r.status_code == 200:
            return r.json()

    def get_signed(self, sig_str):
        """signed params use sha256"""
        # sig_str = base64.b64encode(sig_str)
        # signature = base64.b64encode(hmac.new(self.secret, sig_str, digestmod=hashlib.sha256).hexdigest())
        signature = hmac.new(self.secret, sig_str, digestmod=hashlib.sha256).digest().hex()
        return signature

    def get_dict_str(sefl, input_dict):
        ret = {}
        for it in input_dict:
            ret[str(it)] = str(input_dict[it])
            # ret[str(it)] = input_dict[it]
        return json.dumps(ret).replace(" ", "")

    def signed_request(self, method, api_url, **payload):
        """request a signed url"""
        if not self.key or not self.secret:
            logging.error("Please config api key and secret")
            exit(-1)
        param = ''
        if payload:
            sort_pay = sorted(payload.items())
            for k in sort_pay:
                param += '&' + str(k[0]) + '=' + str(k[1])
            param = param.lstrip('&')
        timestamp = str(int(time.time() * 1000))
        full_url = self.base_url + api_url
        request_path = '/sapi/v1/' + api_url
        if method == 'GET':
            if param:
                full_url = full_url + '?' + param
                request_path = request_path + '?' + param
            sig_str = timestamp + method + request_path
        elif method == 'POST':
            sig_str = timestamp + method + request_path + self.get_dict_str(payload)
        # print(f"sig_str: {sig_str}")

        signature = self.get_signed(bytes(sig_str, 'utf-8'))

        headers = {
            'X-CH-SIGN': signature,
            'X-CH-APIKEY': self.key,
            'X-CH-TS': timestamp,
            'Content-Type': 'application/json'
        }

        try:
            # print(method)
            # print(full_url)
            # print(headers)
            # print(self.get_dict_str(payload))
            if method == "GET":
                r = requests.request(method, full_url, headers=headers, verify=False)
            else:
                r = requests.request(method, full_url, headers=headers, data=self.get_dict_str(payload), verify=False)
            r.raise_for_status()
        except Exception as e:
            traceback.print_exc()
        if r.status_code == 200:
            return r.json()

    def get_depth(self, limit=100):
        """get market depth"""
        return self.public_request('GET', 'depth', limit=limit, symbol=self.symbol)

    def get_account_info(self):
        """get account info(done)"""
        return self.signed_request('GET', 'account')

    def create_order(self, **payload):
        """create order(done)"""
        return self.signed_request('POST', 'order', **payload)

    def trade(self, price, amount, direction):
        """trade someting, buy(1) or sell(0)"""
        if direction == 1:
            return self.buy(price, amount)
        else:
            return self.sell(price, amount)

    def buy(self, price, amount):
        """buy someting(done)"""
        return self.create_order(symbol=self.symbol, side='BUY', type='LIMIT', price=price, volume=amount)

    def sell(self, price, amount):
        """sell someting(done)"""
        return self.create_order(symbol=self.symbol, side='SELL', type='LIMIT', price=price, volume=amount)

    def get_order(self, order_id):
        """get specfic order(done)"""
        return self.signed_request('GET', 'order', orderId=order_id, symbol=self.symbol)

    def get_open_order(self, limit=100):
        """get specfic order(done)"""
        return self.signed_request('GET', 'openOrders', symbol=self.symbol, limit=limit)

    def create_order_test(self):
        """get specfic order(done)"""
        # {"symbol":"BTCUSDT","price":"9300","volume":"1","side":"BUY","type":"LIMIT"} Copied!
        return self.signed_request('GET', 'order/test', symbol=self.symbol, volume=1, side="BUY", type="LIMIT",
                                   price=9300)

    def cancel_order(self, order_id):
        """cancel specfic order(done)"""
        return self.signed_request('POST', 'cancel', orderId=order_id, symbol=self.symbol)

    def get_current_order(self, limit=100):
        """get current orders"""
        return self.signed_request('GET', 'openOrders', symbol=self.symbol, limit=limit)

    def get_my_trade(self, limit=100):
        """get my trades"""
        return self.signed_request('GET', 'myTrades', symbol=self.symbol, limit=limit)

    def check_trade_status(self, order_ret):
        if 'status' in order_ret:
            if re.search('new|fill', order_ret['status'].lower()):
                return True
            else:
                return False

    def check_depth_status(self, depth_ret):
        if 'asks' in depth_ret and 'bids' in depth_ret:
            return True
        else:
            return False

    def get_depth_list(self, depth_direction='asks', limit=100):
        depth_infos = self.get_depth(limit=100)
        if self.check_depth_status(depth_infos):
            depth_infos = depth_infos[depth_direction]
            if len(depth_infos) > 0:
                return depth_infos

    def get_ticker(self, step='1min'):
        return self.public_request('GET', 'klines', symbol=self.symbol, interval=step)

    def get_24h_ticker(self):
        return self.public_request('GET', 'ticker', symbol=self.symbol)


CancelRecord = namedtuple('CancelRecord', ['orderId', 'side', 'price', 'origQty', 'executedQty', 'time'])

if __name__ == "__main__":
    logging.info("Start...")
    from src.utils.config_loader import config
    config.load_config()
    print(config.SYMBOL)
    hot_coin = HotCoin(symbol=config.SYMBOL)
    hot_coin.auth(key=config.ACCESS_KEY, secret=config.SECRET_KEY)
    # while True:
    #     print(hot_coin.get_depth())
        # time.sleep(3)
    # print(hot_coin.get_account_info())
    # print(hot_coin.get_order())
