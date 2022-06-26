# -*- coding:utf-8 -*-
# !/usr/bin/env python
import json
import logging
import random
import time
import zlib

import websockets
from websockets.exceptions import ConnectionClosedError

from trade.hot_coin_api import HotCoin
from utils.config_loader import config
from utils.remind_func import remind_tg

logger = logging.getLogger(__name__)


async def fork_trade(hot_coin, fork_coin_websocket):
    global print_prefix
    logger.info('enter fork trade')
    fork_coin_kline_param = '{\"event\": \"sub\",\"params\": {\"channel\": \"market_' + config.fork_symbol.lower() + 'usdt_ticker\", \"cb_id\": \"1\"}}'
    self_coin_kline_param = '{\"event\": \"sub\",\"params\": {\"channel\": \"market_' + config.SYMBOL.lower() + '_ticker\", \"cb_id\": \"1\"}}'

    self_cnt = 0
    fork_coin_scale = 0
    async for websocket in websockets.connect(config.WEBSOCKETS_API, ping_interval=None):
        fork_coin_websocket = websocket
        await fork_coin_websocket.send(fork_coin_kline_param)
        try:
            async for self_coin_websocket in websockets.connect(config.WEBSOCKETS_API, ping_interval=None):
                await self_coin_websocket.send(self_coin_kline_param)

                while True:
                    print_prefix = f'[Fork Trade: {self_cnt}]'
                    config.load_config()
                    fork_symbol = (config.fork_symbol + 'USDT').upper()
                    # print(fork_symbol)

                    # Check fork_trade_on
                    if not config.fork_trade_on:
                        logger.warning(f'{print_prefix} fork_trade 关闭, 10秒后重试')
                        self_cnt = 0
                        fork_coin_scale = 0
                        time.sleep(10)
                        continue

                    # Get Fork Coin Price
                    fork_coin_recv_text = await fork_coin_websocket.recv()
                    fork_coin_ret = zlib.decompress(fork_coin_recv_text, 16 + zlib.MAX_WBITS).decode('utf-8')
                    fork_coin_ret = json.loads(fork_coin_ret)
                    if 'ping' in fork_coin_ret:
                        logger.info(f'{print_prefix} ping')
                        await fork_coin_websocket.send('{"ping": "ping"}')
                    if 'tick' in fork_coin_ret:
                        fork_coin_data_price = float(fork_coin_ret['tick']['close'])
                        logger.info(f'{print_prefix} WSS => fork_coin_data_price: {fork_coin_data_price}')
                        # logger.info(f'{print_prefix} WSS =>  {fork_coin_ret}')
                    else:
                        fork_coin_ticker_data = HotCoin(symbol=fork_symbol).get_24h_ticker()
                        fork_coin_data_price = 0
                        if 'last' in fork_coin_ticker_data:
                            fork_coin_data_price = float(fork_coin_ticker_data['last'])
                            logger.info(
                                f'{print_prefix} HTTP => fork_coin_data_price: {fork_coin_data_price}')
                        if fork_coin_data_price == 0:
                            logger.warning(f'{print_prefix} 获取fork价格失败{fork_coin_ticker_data}')
                            continue
                    # Get Self Coin Price
                    try:
                        self_coin_recv_text = await self_coin_websocket.recv()
                        self_coin_ret = zlib.decompress(self_coin_recv_text, 16 + zlib.MAX_WBITS).decode('utf-8')
                        self_coin_ret = json.loads(self_coin_ret)
                        if 'ping' in self_coin_ret:
                            logger.info(f'{print_prefix} ping')
                            await self_coin_websocket.send('{"ping": "ping"}')
                        if 'tick' in self_coin_ret:
                            self_coin_data_price = float(self_coin_ret['tick']['close'])
                            logger.info(f'{print_prefix} WSS => self_coin_data_price: {self_coin_data_price}')
                            # logger.info(f'{print_prefix} WSS => {self_coin_ret}')
                        else:
                            time.sleep(1)
                            self_coin_ticker_data = HotCoin(symbol=config.SYMBOL).get_24h_ticker()
                            self_coin_data_price = 0
                            if 'last' in self_coin_ticker_data:
                                self_coin_data_price = float(self_coin_ticker_data['last'])
                                logger.info(
                                    f'{print_prefix} HTTP => self_coin_data_price: {self_coin_data_price}')
                            if self_coin_data_price == 0:
                                logger.warning(f'{print_prefix} 获取self价格失败 {self_coin_ticker_data}')
                                continue
                    except ConnectionClosedError as e:
                        logger.warning(e)
                        logger.warning(f'{print_prefix} self websockets 连接断开, 3秒后重连')
                        time.sleep(3)
                        break

                    # Get Depth
                    fork_coin_depth_data = HotCoin(symbol=fork_symbol).get_depth()
                    self_coin_depth_data = hot_coin.get_depth()
                    # logger.info(fork_coin_depth_data)
                    # logger.info(self_coin_depth_data)
                    if 'asks' not in fork_coin_depth_data:
                        logger.warning(f'{print_prefix} 深度获取失败')
                        time.sleep(1)
                        continue
                    if 'asks' not in self_coin_depth_data:
                        time.sleep(1)
                        logger.warning(f'{print_prefix} 深度获取失败')
                        continue
                    if fork_coin_scale == 0:
                        fork_coin_scale = self_coin_data_price / fork_coin_data_price
                        logger.info(f'{print_prefix} new fork_coin_scale : {fork_coin_scale}')
                    fork_coin_scale = float(fork_coin_scale)

                    # Fork Depth Price
                    fork_coin_b1_price = float(fork_coin_depth_data['bids'][0][0])
                    # print('fork_coin_b1_price', fork_coin_b1_price)
                    fork_coin_s1_price = float(fork_coin_depth_data['asks'][0][0])
                    # print('fork_coin_s1_price', fork_coin_s1_price)

                    # Self Depth Amount 1
                    self_coin_b1_amount = float(self_coin_depth_data['bids'][0][1])
                    # print('self_coin_b1_amount', self_coin_b1_amount)
                    self_coin_s1_amount = float(self_coin_depth_data['asks'][0][1])
                    # print('self_coin_s1_amount', self_coin_s1_amount)

                    # Self Trade Price
                    self_coin_trade_b1_price = fork_coin_b1_price * fork_coin_scale
                    # print('self_coin_trade_b1_price', self_coin_trade_b1_price)
                    self_coin_trade_s1_price = fork_coin_s1_price * fork_coin_scale
                    # print('self_coin_trade_s1_price', self_coin_trade_s1_price)

                    # 发起卖单，消耗买单1
                    trade_b1_price = round(self_coin_trade_b1_price, config.price_decimal_num)
                    # trade_b1_amount = round(self_coin_b1_amount * 1.1, config.vol_decimal_num)
                    trade_b1_amount = round(random.uniform(config.fork_trade_random_amount_min,
                                                           config.fork_trade_random_amount_max), config.vol_decimal_num)
                    trade_b1_type = 0
                    # print('trade_b1_price', trade_b1_price, 'trade_b1_amount', trade_b1_amount, 'trade_b1_type', trade_b1_type)

                    # 发起买单，消耗卖单1
                    trade_s1_price = round(self_coin_trade_s1_price, config.price_decimal_num)
                    # trade_s1_amount = round(self_coin_s1_amount * 1.1, config.vol_decimal_num)
                    trade_s1_amount = round(random.uniform(config.fork_trade_random_amount_min,
                                                           config.fork_trade_random_amount_max), config.vol_decimal_num)
                    trade_s1_type = 1
                    # print('trade_s1_price', trade_s1_price, 'trade_s1_amount', trade_s1_amount, 'trade_s1_type', trade_s1_type)

                    trade_all_list = []
                    # 挂单交易买一卖一
                    if trade_b1_price < self_coin_data_price:
                        logger.debug('1')
                        depth_amount = 0
                        for item in self_coin_depth_data['bids']:
                            if trade_b1_price <= float(item[0]) <= self_coin_data_price:
                                depth_amount = depth_amount + float(item[1])
                        # trade_all_list.append(
                        #     {'price': trade_s1_price, 'depth_amount': self_coin_s1_amount, 'amount': trade_s1_amount, 'trade_type': trade_s1_type})
                        trade_all_list.append(
                            {'price': trade_b1_price, 'depth_amount': depth_amount, 'amount': trade_b1_amount,
                             'trade_type': trade_b1_type})
                    else:
                        logger.debug('2')
                        depth_amount = 0
                        for item in self_coin_depth_data['asks']:
                            if trade_b1_price >= float(item[0]) >= self_coin_data_price:
                                depth_amount = depth_amount + float(item[1])
                        # trade_all_list.append(
                        #     {'price': trade_b1_price, 'depth_amount': self_coin_b1_amount, 'amount': trade_b1_amount, 'trade_type': trade_b1_type})
                        trade_all_list.append(
                            {'price': trade_s1_price, 'depth_amount': depth_amount, 'amount': trade_s1_amount,
                             'trade_type': trade_s1_type})

                    new_hot_coin = HotCoin(symbol=config.SYMBOL)
                    new_hot_coin.auth(key=config.ACCESS_KEY, secret=config.SECRET_KEY)
                    currentOrderData = new_hot_coin.get_open_order(1000)

                    check_error_flag = False
                    owner_order_vol = 0
                    if 'list' in currentOrderData:
                        # logger.debug(len(currentOrderData['list']))
                        # logger.debug(currentOrderData['list'])
                        if len(currentOrderData['list']) > 0:
                            for item in currentOrderData['list']:
                                if trade_all_list[0]['trade_type'] == 0:
                                    if trade_all_list[0]['price'] <= float(item['price']) <= self_coin_data_price \
                                            and item['side'] == 'BUY':
                                        owner_order_vol = owner_order_vol + float(item['origQty']) - float(
                                            item['executedQty'])
                                else:
                                    if trade_all_list[0]['price'] >= float(item['price']) >= self_coin_data_price\
                                            and item['side'] == 'SELL':
                                        owner_order_vol = owner_order_vol + float(item['origQty']) - float(
                                            item['executedQty'])
                        # logger.info(f'{print_prefix}\n'
                        #             f'挂单价格：{trade_all_list[0]["price"]}\n'
                        #             f'{config.SYMBOL_NAME}当前价格：{self_coin_data_price}\n'
                        #             f'Bot委托单量：{owner_order_vol}\n'
                        #             f'盘口交易量：{trade_all_list[0]["depth_amount"]}\n'
                        #             f'非Bot挂单量：{trade_all_list[0]["depth_amount"] - owner_order_vol}')
                        if trade_all_list[0]['depth_amount'] - owner_order_vol > config.fork_trade_amount_max:
                            check_error_flag = True
                            remind_tg(config.ALERT_PRICE_TG_CHAT, f'{print_prefix}非Bot挂单量超额\n'
                                                                  f'挂单价格：{trade_all_list[0]["price"]}\n'
                                                                  f'{config.SYMBOL_NAME}当前价格：{self_coin_data_price}\n'
                                                                  f'Bot委托单量：{owner_order_vol}\n'
                                                                  f'盘口交易量：{trade_all_list[0]["depth_amount"]}\n'
                                                                  f'非Bot挂单量：{trade_all_list[0]["depth_amount"] - owner_order_vol}')
                    else:
                        check_error_flag = True
                        logger.warning(f'{print_prefix} 委托单数据获取错误')

                    # 校验限制
                    for item in trade_all_list:
                        if not config.ALERT_PRICE_MAX > item["price"] > config.ALERT_PRICE_MIN:
                            logger.warning(f'{print_prefix}交易价格超出预警区间, 价格: {item["price"]}')
                            remind_tg(config.ALERT_PRICE_TG_CHAT, f'{print_prefix}交易价格超出预警区间, 价格: {item["price"]}')
                            check_error_flag = True
                            break
                    if check_error_flag:
                        self_cnt = 0
                        fork_coin_scale = 0
                        time.sleep(30)
                        continue

                    # 发送交易
                    for item in trade_all_list:
                        logger.info(
                            f'{print_prefix} 下单方向:{item["trade_type"]}, 价格:{item["price"]}, 下单量:{item["amount"]}')
                        result = hot_coin.trade(item["price"], item["amount"], item["trade_type"])
                        resultId = result['orderId']
                        logger.info(f'{print_prefix} 下单成功， ID：{resultId}')
                    # Sleep
                    logger.info(f'{print_prefix} 交易完成, {config.fork_trade_interval}秒后重新进入')
                    time.sleep(config.fork_trade_interval)
                    self_cnt += 1
        except ConnectionClosedError as e:
            logger.exception(e)
            logger.warning(f'{print_prefix} fork websockets 连接断开, 3秒后重连')
            time.sleep(3)
            continue

        except Exception as e:
            self_cnt = 0
            fork_coin_scale = 0
            logger.error(f'Fork Trade: 未知错误')
            logger.exception(e)
            time.sleep(30)
            continue
