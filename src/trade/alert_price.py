# -*- coding:utf-8 -*-
# !/usr/bin/env python
import json
import logging
import time
import traceback
import zlib
from datetime import datetime

import websockets
from websockets.exceptions import ConnectionClosedError

from trade import utils
from utils.config_loader import config
from utils.remind_func import remind_server_jiang, remind_tg

logger = logging.getLogger(__name__)


def get_datetime(value):
    return datetime.strptime(str(value), '%Y%m%d%H%M%S')


def get_datetime_str(datetime_value):
    return datetime_value.strftime('%Y%m%d%H%M%S')


async def alert_price(hot_coin, websocket):
    self_cnt = 0
    while True:
        try:
            print_prefix = f'[Alert Price: {self_cnt}]'
            config.load_config()

            # Check PERIOD_TRADE_ON
            if not config.ALERT_PRICE_TG_ON and not config.ALERT_PRICE_SERVER_JIANG_ON:
                logger.warning(f'{print_prefix} Alert Price turn off , Sleep {config.ALERT_PRICE_INTERVAL_MINUTE} 分钟')
                time.sleep(config.ALERT_PRICE_INTERVAL_MINUTE)
            logger.info(f'{print_prefix} Start time {utils.get_now_time_str("%Y/%m/%d %H:%M:%S")}...')

            # Get Price
            try:
                ticker_data = hot_coin.get_ticker()
                logger.info(ticker_data)
                if 'last' in ticker_data:
                    data_price = float(ticker_data['last'])
                else:
                    logger.debug(ticker_data)
                    logger.warning(f'{print_prefix} 获取价格失败, 3秒后重试')
                    raise Exception
            except ConnectionClosedError as err:
                logger.warning(err)
                logger.warning(f'{print_prefix} websockets 连接断开, 3秒后重连')
                time.sleep(3)
                continue

            # Alert
            if data_price > config.ALERT_PRICE_MAX or data_price < config.ALERT_PRICE_MIN:
                logger.info(f'{print_prefix} #{config.SYMBOL} 价格预警, 当前价格 {round(data_price, 5)}')
                if config.ALERT_PRICE_TG_ON:
                    remind_tg(config.ALERT_PRICE_TG_CHAT, f'#{config.SYMBOL} 价格预警, 当前价格 {round(data_price, 5)}'
                                                          f', {config.ALERT_PRICE_INTERVAL_MINUTE} 分钟后重试')
                if config.ALERT_PRICE_SERVER_JIANG_ON:
                    remind_server_jiang(f'{config.SYMBOL} 价格预警, 当前价格  {round(data_price, 5)}', f'当前价格{round(data_price, 5)}')
            else:
                logger.info(f'{print_prefix} #{config.SYMBOL} 未触发价格预警{config.ALERT_PRICE_MIN} - {config.ALERT_PRICE_MAX}'
                            f', 当前价格 {round(data_price, 5)}, {config.ALERT_PRICE_INTERVAL_MINUTE} 分钟后重试')
            time.sleep(config.ALERT_PRICE_INTERVAL_MINUTE * 60)
        except Exception as e:
            logger.error(e)
            logger.error(f'Alert Price: 未知错误, 3秒后重试')
            traceback.print_exc()
            time.sleep(3)
            break
