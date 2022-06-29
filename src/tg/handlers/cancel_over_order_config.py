# -*- coding: utf-8 -*-
# #!/usr/bin/python
import configparser
import logging
import os

from telegram.ext import Dispatcher, CommandHandler
from utils.config_loader import config
from utils.restricted import restricted_admin

logger = logging.getLogger(__name__)

raw_config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'config.ini')


def init(dispatcher: Dispatcher):
    """Provide handlers initialization."""
    dispatcher.add_handler(CommandHandler('cancel_over_order_config_show', cancel_over_order_config_show))
    dispatcher.add_handler(CommandHandler('cancel_over_order_on', cancel_over_order_on))
    dispatcher.add_handler(CommandHandler('cancel_over_order_off', cancel_over_order_off))
    dispatcher.add_handler(CommandHandler('set_cancel_over_order_interval', set_cancel_over_order_interval))
    dispatcher.add_handler(CommandHandler('set_cancel_over_order_vol', set_cancel_over_order_vol))


def cancel_over_order_config_show(update, context):
    logger.info('cancel_over_order_config_show')
    text = f'*#{config.SYMBOL_NAME} 撤销累积单配置*\n' \
           f'开关：{config.cancel_over_order_on}\n' \
           f'执行间隔时间：{config.cancel_over_order_interval}s\n' \
           f'筛选超额盘口挂单量：{config.cancel_over_order_vol}'
    rsp = update.message.reply_markdown(text)
    rsp.done.wait(timeout=60)


@restricted_admin
def cancel_over_order_on(update, context):
    raw_config = configparser.ConfigParser()
    raw_config.read(raw_config_path, encoding='utf-8')
    logger.info('cancel_over_order_on')
    config.cancel_over_order_on = True
    raw_config['Trade']['cancel_over_order_on'] = 'True'
    with open(raw_config_path, 'w') as configfile:
        raw_config.write(configfile)
    text = '设置成功'
    rsp = update.message.reply_text(text)
    rsp.done.wait(timeout=60)


@restricted_admin
def cancel_over_order_off(update, context):
    raw_config = configparser.ConfigParser()
    raw_config.read(raw_config_path, encoding='utf-8')
    logger.info('cancel_over_order_off')
    config.cancel_over_order_on = False
    raw_config['Trade']['cancel_over_order_on'] = 'False'
    with open(raw_config_path, 'w') as configfile:
        raw_config.write(configfile)
    text = '设置成功'
    rsp = update.message.reply_text(text)
    rsp.done.wait(timeout=60)


@restricted_admin
def set_cancel_over_order_interval(update, context):
    logger.info('set_cancel_over_order_interval')
    if not context.args or not context.args[0].isdigit:
        update.message.reply_text('参数错误： /set_cancel_over_order_interval <间隔时间>')
        return
    config.cancel_over_order_interval = float(context.args[0])
    raw_config = configparser.ConfigParser()
    raw_config.read(raw_config_path, encoding='utf-8')
    raw_config['Trade']['cancel_over_order_interval'] = context.args[0]
    with open(raw_config_path, 'w') as configfile:
        raw_config.write(configfile)
    rsp = update.message.reply_text('设置成功')
    rsp.done.wait(timeout=60)


@restricted_admin
def set_cancel_over_order_vol(update, context):
    logger.info('set_cancel_over_order_vol')
    if not context.args or not context.args[0].isdigit:
        update.message.reply_text('参数错误： /set_cancel_over_order_vol <超额挂单量>')
        return
    config.cancel_over_order_vol = float(context.args[0])
    raw_config = configparser.ConfigParser()
    raw_config.read(raw_config_path, encoding='utf-8')
    raw_config['Trade']['cancel_over_order_vol'] = context.args[0]
    with open(raw_config_path, 'w') as configfile:
        raw_config.write(configfile)
    rsp = update.message.reply_text('设置成功')
    rsp.done.wait(timeout=60)

