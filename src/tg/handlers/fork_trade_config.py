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
    dispatcher.add_handler(CommandHandler('fork_trade_on', fork_trade_on))
    dispatcher.add_handler(CommandHandler('fork_trade_off', fork_trade_off))
    dispatcher.add_handler(CommandHandler('auto_fork_trade_config_on', auto_fork_trade_config_on))
    dispatcher.add_handler(CommandHandler('auto_fork_trade_config_off', auto_fork_trade_config_off))
    dispatcher.add_handler(CommandHandler('fork_trade_config_show', fork_trade_config_show))
    dispatcher.add_handler(CommandHandler('set_fork_trade_amount_max', set_fork_trade_amount_max))
    dispatcher.add_handler(CommandHandler('set_fork_trade_random_amount_min', set_fork_trade_random_amount_min))
    dispatcher.add_handler(CommandHandler('set_fork_trade_random_amount_max', set_fork_trade_random_amount_max))
    dispatcher.add_handler(CommandHandler('set_fork_random_amount_min_min', set_fork_trade_random_amount_min_min))
    dispatcher.add_handler(CommandHandler('set_fork_random_amount_min_max', set_fork_trade_random_amount_min_max))
    dispatcher.add_handler(CommandHandler('set_fork_random_amount_max_min', set_fork_trade_random_amount_max_min))
    dispatcher.add_handler(CommandHandler('set_fork_random_amount_max_max', set_fork_trade_random_amount_max_max))
    dispatcher.add_handler(CommandHandler('set_fork_trade_interval', set_fork_trade_interval))
    dispatcher.add_handler(CommandHandler('set_fork_symbol', set_fork_symbol))


def check_admin(update):
    if update.effective_user.id in config.ADMINS:
        return True
    else:
        rsp = update.message.reply_text('仅管理员可调用此方法')
        rsp.done.wait(timeout=60)
        return False


def set_fork_trade_amount_max(update, context):
    raw_config = configparser.ConfigParser()
    raw_config.read(raw_config_path, encoding='utf-8')
    logger.info('set_fork_trade_amount_max')
    params = update.message.text.replace(f'@{config.BOT_NAME}', '')
    params = params.replace('/set_fork_trade_amount_max', '')
    params = params.replace(' ', '')
    params = params.split(',')
    if params[0] == '':
        text = '参数错误'
    elif update.effective_user.id in config.ADMINS:
        config.fork_trade_amount_max = float(params[0])
        raw_config['Trade']['fork_trade_amount_max'] = params[0]
        with open(raw_config_path, 'w') as configfile:
            raw_config.write(configfile)
        text = '设置成功'
    else:
        text = '仅管理员可调用此方法'
    rsp = update.message.reply_text(text)
    rsp.done.wait(timeout=60)


def set_fork_trade_random_amount_min(update, context):
    raw_config = configparser.ConfigParser()
    raw_config.read(raw_config_path, encoding='utf-8')
    logger.info('set_fork_trade_random_amount_min')
    params = update.message.text.replace(f'@{config.BOT_NAME}', '')
    params = params.replace('/set_fork_trade_random_amount_min', '')
    params = params.replace(' ', '')
    params = params.split(',')
    if params[0] == '':
        text = '参数错误'
    elif update.effective_user.id in config.ADMINS:
        config.fork_trade_random_amount_min = float(params[0])
        raw_config['Trade']['fork_trade_random_amount_min'] = params[0]
        with open(raw_config_path, 'w') as configfile:
            raw_config.write(configfile)
        text = '设置成功'
    else:
        text = '仅管理员可调用此方法'
    rsp = update.message.reply_text(text)
    rsp.done.wait(timeout=60)


def set_fork_trade_random_amount_max(update, context):
    raw_config = configparser.ConfigParser()
    raw_config.read(raw_config_path, encoding='utf-8')
    logger.info('set_fork_trade_random_amount_max')
    params = update.message.text.replace(f'@{config.BOT_NAME}', '')
    params = params.replace('/set_fork_trade_random_amount_max', '')
    params = params.replace(' ', '')
    params = params.split(',')
    if params[0] == '':
        text = '参数错误'
    elif update.effective_user.id in config.ADMINS:
        config.fork_trade_random_amount_max = float(params[0])
        raw_config['Trade']['fork_trade_random_amount_max'] = params[0]
        with open(raw_config_path, 'w') as configfile:
            raw_config.write(configfile)
        text = '设置成功'
    else:
        text = '仅管理员可调用此方法'
    rsp = update.message.reply_text(text)
    rsp.done.wait(timeout=60)


@restricted_admin
def set_fork_trade_random_amount_min_min(update, context):
    logger.info('set_fork_trade_random_amount_min_min')
    if not context.args or not context.args[0].isdigit:
        update.message.reply_text('参数错误： /set_fork_trade_random_amount_min_min <自动调整复刻盘口最小交易量区间最小值>')
        return
    config.fork_trade_random_amount_min_min = float(context.args[0])
    raw_config = configparser.ConfigParser()
    raw_config.read(raw_config_path, encoding='utf-8')
    raw_config['Trade']['fork_trade_random_amount_min_min'] = context.args[0]
    with open(raw_config_path, 'w') as configfile:
        raw_config.write(configfile)
    rsp = update.message.reply_text('设置成功')
    rsp.done.wait(timeout=60)
    fork_trade_config_show(update, context)


@restricted_admin
def set_fork_trade_random_amount_min_max(update, context):
    logger.info('set_fork_trade_random_amount_min_max')
    if not context.args or not context.args[0].isdigit:
        update.message.reply_text('参数错误： /set_fork_trade_random_amount_min_max <自动调整复刻盘口最小交易量区间最大值>')
        return
    config.fork_trade_random_amount_min_max = float(context.args[0])
    raw_config = configparser.ConfigParser()
    raw_config.read(raw_config_path, encoding='utf-8')
    raw_config['Trade']['fork_trade_random_amount_min_max'] = context.args[0]
    with open(raw_config_path, 'w') as configfile:
        raw_config.write(configfile)
    rsp = update.message.reply_text('设置成功')
    rsp.done.wait(timeout=60)
    fork_trade_config_show(update, context)


@restricted_admin
def set_fork_trade_random_amount_max_min(update, context):
    logger.info('set_fork_trade_random_amount_max_min')
    if not context.args or not context.args[0].isdigit:
        update.message.reply_text('参数错误： /set_fork_trade_random_amount_max_min <自动调整复刻盘口最大交易量区间最小值>')
        return
    config.fork_trade_random_amount_max_min = float(context.args[0])
    raw_config = configparser.ConfigParser()
    raw_config.read(raw_config_path, encoding='utf-8')
    raw_config['Trade']['fork_trade_random_amount_max_min'] = context.args[0]
    with open(raw_config_path, 'w') as configfile:
        raw_config.write(configfile)
    rsp = update.message.reply_text('设置成功')
    rsp.done.wait(timeout=60)
    fork_trade_config_show(update, context)


@restricted_admin
def set_fork_trade_random_amount_max_max(update, context):
    logger.info('set_fork_trade_random_amount_max_max')
    if not context.args or not context.args[0].isdigit:
        update.message.reply_text('参数错误： /set_fork_trade_random_amount_max_max <自动调整复刻盘口最大交易量区间最大值>')
        return
    config.fork_trade_random_amount_max_max = float(context.args[0])
    raw_config = configparser.ConfigParser()
    raw_config.read(raw_config_path, encoding='utf-8')
    raw_config['Trade']['fork_trade_random_amount_max_max'] = context.args[0]
    with open(raw_config_path, 'w') as configfile:
        raw_config.write(configfile)
    rsp = update.message.reply_text('设置成功')
    rsp.done.wait(timeout=60)
    fork_trade_config_show(update, context)


def fork_trade_on(update, context):
    raw_config = configparser.ConfigParser()
    raw_config.read(raw_config_path, encoding='utf-8')
    logger.info('fork_trade_on')
    if not check_admin(update):
        return
    config.fork_trade_on = True
    raw_config['Trade']['fork_trade_on'] = 'True'
    with open(raw_config_path, 'w') as configfile:
        raw_config.write(configfile)
    text = '设置成功'
    rsp = update.message.reply_text(text)
    rsp.done.wait(timeout=60)


def fork_trade_off(update, context):
    raw_config = configparser.ConfigParser()
    raw_config.read(raw_config_path, encoding='utf-8')
    logger.info('fork_trade_off')
    if not check_admin(update):
        return
    config.fork_trade_on = False
    raw_config['Trade']['fork_trade_on'] = 'False'
    with open(raw_config_path, 'w') as configfile:
        raw_config.write(configfile)
    text = '设置成功'
    rsp = update.message.reply_text(text)
    rsp.done.wait(timeout=60)


@restricted_admin
def auto_fork_trade_config_on(update, context):
    raw_config = configparser.ConfigParser()
    raw_config.read(raw_config_path, encoding='utf-8')
    logger.info('auto_fork_trade_config_on')
    config.auto_fork_trade_config_on = True
    raw_config['Trade']['auto_fork_trade_config_on'] = 'True'
    with open(raw_config_path, 'w') as configfile:
        raw_config.write(configfile)
    text = '设置成功'
    rsp = update.message.reply_text(text)
    rsp.done.wait(timeout=60)


@restricted_admin
def auto_fork_trade_config_off(update, context):
    raw_config = configparser.ConfigParser()
    raw_config.read(raw_config_path, encoding='utf-8')
    logger.info('auto_fork_trade_config_off')
    config.auto_fork_trade_config_on = False
    raw_config['Trade']['auto_fork_trade_config_on'] = 'False'
    with open(raw_config_path, 'w') as configfile:
        raw_config.write(configfile)
    text = '设置成功'
    rsp = update.message.reply_text(text)
    rsp.done.wait(timeout=60)


def fork_trade_config_show(update, context):
    logger.info('fork_trade_config_show')
    config.load_config()
    text = f'*#{config.SYMBOL_NAME} 对标交易配置*\n' \
           f'是否开启对标交易：{config.fork_trade_on}\n' \
           f'对标代币：{config.fork_symbol}\n' \
           f'对标间隔时间：{config.fork_trade_interval}s\n' \
           f'买卖1最大挂单数量：{config.fork_trade_amount_max}\n' \
           f'买卖2-5随机挂单量区间 {config.fork_trade_random_amount_min} - {config.fork_trade_random_amount_max}\n' \
           f'是否开启自动配置：{config.auto_fork_trade_config_on}\n' \
           f'自动调整复刻盘口最小交易量区间：{config.fork_trade_random_amount_min_min} - {config.fork_trade_random_amount_min_max}\n' \
           f'自动调整复刻盘口最大交易量区间：{config.fork_trade_random_amount_max_min} - {config.fork_trade_random_amount_max_max}'
    rsp = update.message.reply_markdown(text)
    rsp.done.wait(timeout=60)


@restricted_admin
def set_fork_trade_interval(update, context):
    logger.info('set_fork_trade_interval')
    if not context.args or not context.args[0].isdigit:
        update.message.reply_text('参数错误： /set_fork_trade_interval <间隔时间>')
        return
    config.fork_trade_interval = float(context.args[0])
    raw_config = configparser.ConfigParser()
    raw_config.read(raw_config_path, encoding='utf-8')
    raw_config['Trade']['fork_trade_interval'] = context.args[0]
    with open(raw_config_path, 'w') as configfile:
        raw_config.write(configfile)
    rsp = update.message.reply_text('设置成功')
    rsp.done.wait(timeout=60)


@restricted_admin
def set_fork_symbol(update, context):
    logger.info('set_fork_symbol')
    if not context.args or not context.args[0].isdigit:
        update.message.reply_text('参数错误： /set_fork_symbol <对标代币>')
        return
    config.fork_symbol = context.args[0]
    raw_config = configparser.ConfigParser()
    raw_config.read(raw_config_path, encoding='utf-8')
    raw_config['Trade']['fork_symbol'] = context.args[0]
    with open(raw_config_path, 'w') as configfile:
        raw_config.write(configfile)
    rsp = update.message.reply_text('设置成功')
    rsp.done.wait(timeout=60)
