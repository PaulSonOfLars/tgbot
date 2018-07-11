import html
import json

from typing import Optional, List

import requests
from telegram import Message, Chat, Update, Bot, MessageEntity
from telegram import ParseMode
from telegram.ext import CommandHandler, run_async, Filters, MessageHandler

from tg_bot import dispatcher, LOGGER


@run_async
def rem_slash_commands(bot: Bot, update: Update) -> str:
    msg = update.effective_message  # type: Optional[Message]
    try:
        msg.delete()
    except BadRequest as excp:
        LOGGER.info("silently failing")
        LOGGER.info(excp)


__help__ = """
I remove messages starting with a /command in groups and supergroups."
"""

__mod_name__ = "anticommand"

REM_SLASH_COMMANDS = MessageHandler(Filters.command, rem_slash_commands)

dispatcher.add_handler(REM_SLASH_COMMANDS)
