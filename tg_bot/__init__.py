import logging

import os
from telegram.ext import Updater

HEROKU = bool(os.environ.get('HEROKU', False))
if not HEROKU:
    from tg_bot.config import Development as Config

# enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO)

LOGGER = logging.getLogger(__name__)

if HEROKU:
    TOKEN = os.environ.get('TOKEN', None)
else:
    TOKEN = Config.API_KEY

updater = Updater(TOKEN, workers=6)

dispatcher = updater.dispatcher
