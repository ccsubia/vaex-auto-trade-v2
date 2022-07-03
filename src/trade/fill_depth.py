# -*- coding:utf-8 -*-
# !/usr/bin/env python
import json
import logging
import random
import time
import zlib
from decimal import *

import websockets
from websockets.exceptions import ConnectionClosedError

from trade.hot_coin_api import HotCoin
from utils.config_loader import config
from utils.remind_func import remind_tg

logger = logging.getLogger(__name__)


async def fill_depth(hot_coin, websocket):
    print_prefix = '[Fill Depth]'
    logger.info(print_prefix)
    self_coin_kline_param = '{\"event\": \"sub\",\"params\": {\"channel\": \"market_' + config.SYMBOL.lower() + '_ticker\", \"cb_id\": \"1\"}}'
    self_cnt = 0
    async for self_coin_websocket in websockets.connect(config.WEBSOCKETS_API, ping_interval=None):
        try:
            await self_coin_websocket.send(self_coin_kline_param)

            while True:
                print_prefix = f'[Fill Depth: {self_cnt}]'
                config.load_config()

                # Check fill_depth_on
                if not config.fill_depth_on:
                    logger.warning('fill_depth 关闭, 10秒后重试')
                    self_cnt = 0
                    time.sleep(10)
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
                self_coin_depth_data = hot_coin.get_depth()
                # logger.debug(self_coin_depth_data)

                sellprice, buyprice = [], []
                depth_data = self_coin_depth_data
                if ('asks' in depth_data) and ('bids' in depth_data):
                    for order in depth_data['asks']:
                        sellprice.append(round(Decimal(order[0]), config.price_decimal_num))
                    for order in depth_data['bids']:
                        buyprice.append(round(Decimal(order[0]), config.price_decimal_num))
                else:
                    logger.warning(f'{print_prefix} 深度获取失败')
                    time.sleep(1)
                    continue
                trade_all_list = []
                start_price = round(Decimal(self_coin_data_price), config.price_decimal_num)
                price_step = round(Decimal(0.1) ** config.price_decimal_num, config.price_decimal_num)
                for i in range(29):
                    fill_sell_price = start_price + price_step * (i + 1)
                    push_sell_price = round(fill_sell_price, config.price_decimal_num)
                    push_sell_amount = round(random.uniform(config.fill_depth_random_amount_min,
                                                            config.fill_depth_random_amount_max), config.vol_decimal_num)
                    if fill_sell_price not in sellprice:
                        trade_all_list.append({'price': push_sell_price, 'amount': push_sell_amount, 'trade_type': 0})

                    fill_buy_price = start_price - price_step * (i + 1)
                    push_buy_price = round(fill_buy_price, config.price_decimal_num)
                    push_buy_amount = round(random.uniform(config.fill_depth_random_amount_min,
                                                           config.fill_depth_random_amount_max), config.vol_decimal_num)
                    if fill_buy_price not in buyprice:
                        trade_all_list.append({'price': push_buy_price, 'amount': push_buy_amount, 'trade_type': 1})

                # 校验限制
                check_error_flag = False
                for item in trade_all_list:
                    if not config.ALERT_PRICE_MAX > item["price"] > config.ALERT_PRICE_MIN:
                        logger.warning(f'{print_prefix}交易价格超出预警区间, 价格: {item["price"]}')
                        remind_tg(config.ALERT_PRICE_TG_CHAT, f'{print_prefix}交易价格超出预警区间, 价格: {item["price"]}')
                        check_error_flag = True
                        break
                if check_error_flag:
                    self_cnt = 0
                    time.sleep(30)
                    continue

                # 发送交易
                for item in trade_all_list:
                    logger.info(
                        f'{print_prefix} 下单方向:{item["trade_type"]}, 价格:{item["price"]}, 下单量:{item["amount"]}')
                    result = hot_coin.trade(item["price"], item["amount"], item["trade_type"])
                    if 'orderId' in result:
                        resultId = result['orderId']
                        logger.info(f'{print_prefix} 下单成功， ID：{resultId}')
                    else:
                        logger.info(f'{print_prefix} 下单失败，{result}')
                # Sleep
                logger.info(f'{print_prefix} 交易完成, {config.fill_depth_interval}秒后重新进入')
                time.sleep(config.fill_depth_interval)
                self_cnt += 1

        except Exception as e:
            logger.error(f'{print_prefix}: 未知错误, 睡眠{config.fill_depth_interval}秒')
            logger.exception(e)
            remind_tg(config.ALERT_PRICE_TG_CHAT, f'未知错误: {print_prefix} {e}')
            time.sleep(config.fill_depth_interval)

