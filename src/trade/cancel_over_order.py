# -*- coding:utf-8 -*-
# !/usr/bin/env python
import logging
import time

from utils.config_loader import config
from utils.remind_func import remind_tg

logger = logging.getLogger(__name__)


async def cancel_over_order(hot_coin, self_coin_websocket):
    print_prefix = f'[Cancel Over Order]'
    logger.info(print_prefix)

    self_cnt = 0
    while True:
        try:
            print_prefix = f'[Cancel Over Order: {self_cnt}]'
            config.load_config()

            # Check fork_trade_on
            if not config.cancel_over_order_on:
                logger.warning(f'{print_prefix} fork_trade 关闭, 10秒后重试')
                self_cnt = 0
                time.sleep(10)
                continue

            # Get Depth
            self_coin_depth_data = hot_coin.get_depth(limit=50)
            # logger.debug(self_coin_depth_data)
            if 'asks' not in self_coin_depth_data:
                time.sleep(1)
                logger.warning(f'{print_prefix} 深度获取失败 {self_coin_depth_data}')
                continue

            # Check Depth Amount
            over_depth_price_list = []
            first_item = True
            for item in self_coin_depth_data['bids']:
                if first_item:
                    first_item = False
                    continue
                if float(item[1]) > config.cancel_over_order_vol:
                    logger.info(f'{print_prefix} 价格 {item[0]} 盘口单量超额, 当前单量 {item[1]}')
                    over_depth_price_list.append(float(item[0]))
            first_item = True
            for item in self_coin_depth_data['asks']:
                if first_item:
                    first_item = False
                    continue
                if float(item[1]) > config.cancel_over_order_vol:
                    logger.info(f'{print_prefix} 价格 {item[0]} 盘口单量超额, 当前单量 {item[1]}')
                    over_depth_price_list.append(float(item[0]))

            currentOrderData = hot_coin.get_open_order(1000)
            # logger.debug(currentOrderData)

            toCancelOrders = []
            if 'list' in currentOrderData:
                # logger.debug(len(currentOrderData['list']))
                # logger.debug(currentOrderData['list'])
                if len(currentOrderData['list']) > 0:
                    for item in currentOrderData['list']:
                        if float(item['price']) in over_depth_price_list:
                            toCancelOrders.append(item['orderId'])
            else:
                logger.warning(f'{print_prefix} 委托单数据获取错误')
                remind_tg(config.ALERT_PRICE_TG_CHAT, f'{print_prefix} 委托单数据获取错误: {currentOrderData}')

            # 取消委托单
            for item in toCancelOrders:
                logger.info(f'{print_prefix} 撤销委托单ID => {item}')
                logger.info(f'{print_prefix} {hot_coin.cancel_order(item)}')

            # Sleep
            logger.info(f'{print_prefix} 交易完成, {config.cancel_over_order_interval}秒后重新进入')
            time.sleep(config.cancel_over_order_interval)
            self_cnt += 1

        except Exception as e:
            self_cnt = 0
            logger.error(f'Fork Trade: 未知错误')
            logger.exception(e)
            remind_tg(config.ALERT_PRICE_TG_CHAT, f'{print_prefix}, 未知错误: {e}')
            time.sleep(30)
            continue
