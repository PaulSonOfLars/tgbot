import logging
import os

from telegram.ext import Updater

# enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO)

LOGGER = logging.getLogger(__name__)

HEROKU = bool(os.environ.get('HEROKU', False))

if not HEROKU:
    from tg_bot.config import Development as Config
    TOKEN = Config.API_KEY
    OWNER_ID = Config.OWNER_ID
    MESSAGE_DUMP = Config.MESSAGE_DUMP
    OWNER_USERNAME = Config.OWNER_USERNAME

else:
    TOKEN = os.environ.get('TOKEN', None)
    OWNER_ID = int(os.environ.get('OWNER_ID', None))
    MESSAGE_DUMP = os.environ.get('MESSAGE_DUMP', None)
    OWNER_USERNAME = os.environ.get("OWNER_USERNAME", None)

updater = Updater(TOKEN, workers=6)

dispatcher = updater.dispatcher
