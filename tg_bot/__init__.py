import logging

from telegram.ext import Updater

from tg_bot.config import Development as Configuration

# enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO)

LOGGER = logging.getLogger(__name__)

updater = Updater(Configuration.API_KEY)
dispatcher = updater.dispatcher
