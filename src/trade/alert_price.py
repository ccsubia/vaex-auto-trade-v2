# -*- coding:utf-8 -*-
# !/usr/bin/env python
import configparser
import logging
import os
import time

from websockets.exceptions import ConnectionClosedError

from trade import utils
from trade.batch_push_trade import batch_push_trade
from utils.config_loader import config
from utils.remind_func import remind_server_jiang, remind_tg

logger = logging.getLogger(__name__)

raw_config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.ini')


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
            ticker_data = hot_coin.get_24h_ticker()
            # logger.info(ticker_data)
            if 'last' in ticker_data:
                data_price = float(ticker_data['last'])
            else:
                logger.debug(ticker_data)
                logger.warning(f'{print_prefix} 获取价格失败, 3秒后重试')
                raise Exception

            # Alert
            if data_price > config.ALERT_PRICE_MAX:
                logger.info(f'{print_prefix} #{config.SYMBOL} 价格预警, 当前价格 {round(data_price, 5)}')
                if config.ALERT_PRICE_TG_ON:
                    remind_tg(config.ALERT_PRICE_TG_CHAT, f'#{config.SYMBOL} 价格预警, 当前价格 {round(data_price, 5)}'
                                                          f', {config.ALERT_PRICE_INTERVAL_MINUTE} 分钟后重试')
                raw_config = configparser.ConfigParser()
                raw_config.read(raw_config_path, encoding='utf-8')
                if int(raw_config['Trade']['auto_batch_push_trade_push_count']) != 0:
                    raw_config['Trade']['auto_batch_push_trade_type'] = str(0)
                    raw_config['Trade']['auto_batch_push_trade_push_count'] = str(0)
                    raw_config['Trade']['auto_batch_push_trade_start_price'] = str(0)
                    raw_config['Trade']['auto_batch_push_trade_price_step'] = str(0)
                    raw_config['Trade']['auto_batch_push_trade_push_first_amount'] = str(0)
                    raw_config['Trade']['auto_batch_push_trade_up_amount'] = str(0)
                    raw_config['Trade']['auto_batch_push_trade_time_interval'] = str(0)
                    with open(raw_config_path, 'w') as configfile:
                        raw_config.write(configfile)
                    remind_tg(config.ALERT_PRICE_TG_CHAT, '开始执行挂单')
                    batch_push_trade(
                        config.auto_batch_push_trade_type,
                        config.auto_batch_push_trade_push_count,
                        config.auto_batch_push_trade_start_price,
                        config.auto_batch_push_trade_price_step,
                        config.auto_batch_push_trade_push_first_amount,
                        config.auto_batch_push_trade_up_amount,
                        config.auto_batch_push_trade_time_interval
                    )
                    remind_tg(config.ALERT_PRICE_TG_CHAT, '执行结束')
                if config.ALERT_PRICE_SERVER_JIANG_ON:
                    remind_server_jiang(f'{config.SYMBOL} 价格预警, 当前价格  {round(data_price, 5)}',
                                        f'当前价格{round(data_price, 5)}')
            elif data_price < config.ALERT_PRICE_MIN:
                logger.info(f'{print_prefix} #{config.SYMBOL} 价格预警, 当前价格 {round(data_price, 5)}')
                if config.ALERT_PRICE_TG_ON:
                    remind_tg(config.ALERT_PRICE_TG_CHAT, f'#{config.SYMBOL} 价格预警, 当前价格 {round(data_price, 5)}'
                                                          f', {config.ALERT_PRICE_INTERVAL_MINUTE} 分钟后重试')
                raw_config = configparser.ConfigParser()
                raw_config.read(raw_config_path, encoding='utf-8')
                if int(raw_config['Trade']['auto_batch_push_trade_push_count2']) != 0:
                    raw_config['Trade']['auto_batch_push_trade_type2'] = str(1)
                    raw_config['Trade']['auto_batch_push_trade_push_count2'] = str(0)
                    raw_config['Trade']['auto_batch_push_trade_start_price2'] = str(0)
                    raw_config['Trade']['auto_batch_push_trade_price_step2'] = str(0)
                    raw_config['Trade']['auto_batch_push_trade_push_first_amount2'] = str(0)
                    raw_config['Trade']['auto_batch_push_trade_up_amount2'] = str(0)
                    raw_config['Trade']['auto_batch_push_trade_time_interval2'] = str(0)
                    with open(raw_config_path, 'w') as configfile:
                        raw_config.write(configfile)
                    remind_tg(config.ALERT_PRICE_TG_CHAT, '开始执行挂单')
                    batch_push_trade(
                        config.auto_batch_push_trade_type,
                        config.auto_batch_push_trade_push_count,
                        config.auto_batch_push_trade_start_price,
                        config.auto_batch_push_trade_price_step,
                        config.auto_batch_push_trade_push_first_amount,
                        config.auto_batch_push_trade_up_amount,
                        config.auto_batch_push_trade_time_interval
                    )
                    remind_tg(config.ALERT_PRICE_TG_CHAT, '执行结束')
                if config.ALERT_PRICE_SERVER_JIANG_ON:
                    remind_server_jiang(f'{config.SYMBOL} 价格预警, 当前价格  {round(data_price, 5)}',
                                        f'当前价格{round(data_price, 5)}')
            else:
                logger.info(
                    f'{print_prefix} #{config.SYMBOL} 未触发价格预警{config.ALERT_PRICE_MIN} - {config.ALERT_PRICE_MAX}'
                    f', 当前价格 {round(data_price, 5)}')
            logger.info(f'{print_prefix} {config.ALERT_PRICE_INTERVAL_MINUTE} 分钟后重入')
            time.sleep(config.ALERT_PRICE_INTERVAL_MINUTE * 60)
            self_cnt += 1
        except Exception as e:
            logger.error(f'Alert Price: 未知错误, 3秒后重试')
            logger.exception(e)
            time.sleep(3)
            break
