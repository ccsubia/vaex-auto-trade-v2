# -*- coding: utf-8 -*-
# #!/usr/bin/python
import logging
import os

from telegram.ext import Dispatcher, CommandHandler

from utils.config_loader import config
from utils.restricted import restricted_admin

logger = logging.getLogger(__name__)

raw_config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'config.ini')


def init(dispatcher: Dispatcher):
    """Provide handlers initialization."""
    dispatcher.add_handler(CommandHandler('get_config_file', get_config_file))


@restricted_admin
def get_config_file(update, context):
    logger.info('get_config_file')
    if update.effective_user.id in config.ADMINS:
        update.message.reply_document(document=open(raw_config_path, 'rb'))
