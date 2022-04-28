# -*- coding:utf-8 -*-
# !/usr/bin/env python
import json
import logging
import os
import random
import time
import traceback
import zlib
from datetime import datetime

import websockets
from websockets.exceptions import ConnectionClosedError

from trade import utils
from trade.hot_coin_api import HotCoin
from utils.config_loader import config
from utils.csv_tool import read_csv_file, save_csv, add_csv_rows

logger = logging.getLogger(__name__)

k_line_path = os.path.join(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'csv'), 'kLine.csv')
past_k_line_path = os.path.join(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'csv'), 'past_kLine.csv')


def get_datetime(value):
    return datetime.strptime(str(value), '%Y%m%d%H%M%S')


def get_datetime_str(datetime_value):
    return datetime_value.strftime('%Y%m%d%H%M%S')


async def fork_trade(hot_coin, fork_coin_websocket):
    logger.info('enter fork trade')
    fork_coin_kline_param = '{\"event\":\"sub\",\"params\":{\"channel\":\"market_btcusdt_kline_1min\",\"cb_id\":\"1\"}}'

    self_coin_kline_param = '{\"event\":\"sub\",\"params\":{\"channel\":\"market_hspcusdt_kline_1min\",\"cb_id\":\"1\"}}'
    async with websockets.connect(config.WEBSOCKETS_API, ping_interval=None) as new_websocket:
        self_coin_websocket = new_websocket
        time.sleep(1)
        await self_coin_websocket.send(self_coin_kline_param)
        await fork_coin_websocket.send(fork_coin_kline_param)

        self_cnt = 0
        fork_coin_scale = 0
        while True:
            try:
                print_prefix = f'[Period Trade: {self_cnt}]'
                config.load_config()

                # Check PERIOD_TRADE_ON
                # if not config.PERIOD_TRADE_ON:
                #     logger.warning('PERIOD_TRADE turn off')
                #     time.sleep(config.DEFAULT_PERIOD_TRADE_INTERVAL_TIME)
                logger.info(f'{print_prefix} Start time {utils.get_now_time_str("%Y/%m/%d %H:%M:%S")}...')

                # Get Fork Coin Price
                fork_coin_recv_text = await fork_coin_websocket.recv()
                fork_coin_ret = zlib.decompress(fork_coin_recv_text, 16 + zlib.MAX_WBITS).decode('utf-8')
                fork_coin_ret = json.loads(fork_coin_ret)
                logger.info(fork_coin_ret)
                if 'ping' in fork_coin_ret:
                    await fork_coin_websocket.send('{"pong": "pong"}')
                if 'tick' in fork_coin_ret:
                    fork_coin_data_price = float(fork_coin_ret['tick']['close'])
                else:
                    logger.warning(f'{print_prefix} 获取价格失败, 3秒后重试')
                    time.sleep(3)
                    continue
                # Get Self Coin Price
                self_coin_recv_text = await self_coin_websocket.recv()
                self_coin_ret = zlib.decompress(self_coin_recv_text, 16 + zlib.MAX_WBITS).decode('utf-8')
                self_coin_ret = json.loads(self_coin_ret)
                logger.debug(self_coin_ret)
                if 'ping' in self_coin_ret:
                    await self_coin_websocket.send('{"pong": "pong"}')
                if 'ticks' in self_coin_ret:
                    self_coin_data_price = float(self_coin_ret['tick']['close'])
                    logger.info(f'self_coin_data_price: {self_coin_data_price}')
                else:
                    self_coin_ticker_data = hot_coin.get_ticker(86400)
                    print(self_coin_ticker_data)
                    if 'last' in self_coin_ticker_data:
                        self_coin_data_price = float(self_coin_ticker_data['last'])
                        logger.info(f'self_coin_data_price: {self_coin_data_price}')
                    else:
                        logger.warning(self_coin_ticker_data)
                        logger.warning(f'{print_prefix} 获取价格失败')
                        raise Exception

                # Get Depth
                fork_coin_depth_data = HotCoin(symbol='BTCUSDT').get_depth()
                self_coin_depth_data = hot_coin.get_depth()
                logger.info(fork_coin_depth_data)
                logger.info(self_coin_depth_data)
                if 'asks' not in fork_coin_depth_data:
                    logger.warning(f'{print_prefix} 深度获取失败')
                    continue
                if 'asks' not in self_coin_depth_data:
                    logger.warning(f'{print_prefix} 深度获取失败')
                    continue
                if fork_coin_scale == 0:
                    fork_coin_scale = self_coin_data_price / fork_coin_data_price
                print('fork_coin_scale', fork_coin_scale)

                # Current Price
                print('fork_coin_data_price', fork_coin_data_price)
                print('self_coin_data_price', self_coin_data_price)

                # Fork Depth Price
                fork_coin_b1_price = float(fork_coin_depth_data['bids'][0][0])
                print('fork_coin_b1_price', fork_coin_b1_price)
                fork_coin_s1_price = float(fork_coin_depth_data['asks'][0][0])
                print('fork_coin_s1_price', fork_coin_s1_price)

                # Self Depth Price
                self_coin_b1_price = float(self_coin_depth_data['bids'][0][0])
                print('self_coin_b1_price', self_coin_b1_price)
                self_coin_s1_price = float(self_coin_depth_data['asks'][0][0])
                print('self_coin_s1_price', self_coin_s1_price)

                # Self Depth Amount
                self_coin_b1_amount = float(self_coin_depth_data['bids'][0][1])
                print('self_coin_b1_amount', self_coin_b1_amount)
                self_coin_b2_amount = float(self_coin_depth_data['bids'][1][1])
                print('self_coin_b2_amount', self_coin_b2_amount)
                self_coin_s1_amount = float(self_coin_depth_data['asks'][0][1])
                print('self_coin_s1_amount', self_coin_s1_amount)
                self_coin_s2_amount = float(self_coin_depth_data['asks'][1][1])
                print('self_coin_s2_amount', self_coin_s2_amount)

                # Self Trade Price
                self_coin_trade_b1_price = fork_coin_b1_price * fork_coin_scale
                print('self_coin_trade_b1_price', self_coin_trade_b1_price)
                self_coin_trade_s1_price = fork_coin_s1_price * fork_coin_scale
                print('self_coin_trade_s1_price', self_coin_trade_s1_price)

                # Self Trade Price
                self_coin_trade_b1_price = fork_coin_b1_price * fork_coin_scale
                print('self_coin_trade_b1_price', self_coin_trade_b1_price)
                self_coin_trade_s1_price = fork_coin_s1_price * fork_coin_scale
                print('self_coin_trade_s1_price', self_coin_trade_s1_price)

                # 发起卖单，消耗买单
                trade1_price = round(self_coin_trade_b1_price, 8)
                trade1_amount = round(self_coin_b1_amount + self_coin_b2_amount * 0.1, 4)
                trade1_type = 0
                print('trade1_price', trade1_price, 'trade1_amount', trade1_amount, 'trade1_type', trade1_type)

                # 发起买单，消耗卖单
                trade2_price = round(self_coin_trade_s1_price, 8)
                trade2_amount = round(self_coin_s1_amount + self_coin_s2_amount * 0.1, 4)
                trade2_type = 1
                print('trade2_price', trade2_price, 'trade2_amount', trade2_amount, 'trade2_type', trade2_type)

                # time.sleep(2)
                if trade1_price > config.ALERT_PRICE_MAX:
                    print('交易价格1过高', trade1_price)
                    continue
                if trade1_price < config.ALERT_PRICE_MIN:
                    print('交易价格1过低', trade1_price)
                    continue
                if trade2_price > config.ALERT_PRICE_MAX:
                    print('交易价格2过高', trade2_price)
                    continue
                if trade2_price < config.ALERT_PRICE_MIN:
                    print('交易价格2过低', trade2_price)
                    continue
                if trade1_amount > 2000:
                    print('交易量1超额', trade1_amount)
                    continue
                if trade2_amount > 2000:
                    print('交易量2超额', trade2_amount)
                    continue
                # logger.info(f'{print_prefix} 下单方向:{side_str1}, 价格:{put_trade_amount}, 下单量:{put_trade_amount}')
                result = hot_coin.trade(trade1_price, trade1_amount, trade1_type)
                print(result)
                time.sleep(10)
                return
                result1Id = result['data']['ID']
                print('result1Id', result1Id)
                result2 = hot_coin.trade(trade2_price, trade2_amount, trade2_type)
                result2Id = result2['data']['ID']
                print('result2Id', result2Id)
                # logger.info(f'{print_prefix} 下单方向:{side_str2}, 价格:{trade_price}, 下单量:{trade_amount}')
                # result = hot_coin.trade(trade_price, trade_amount, direction)
                print(hot_coin.get_order(result1Id))
                print(hot_coin.get_order(result2Id))

                # Sleep
                logger.info(f'{print_prefix} 1秒后重新进入')
                time.sleep(1)
                self_cnt += 1
                continue
            except Exception as e:
                logger.error(e)
                logger.error(f'Period Trade: 未知错误, 10 秒后重试')
                traceback.print_exc()
                time.sleep(10)
                break
