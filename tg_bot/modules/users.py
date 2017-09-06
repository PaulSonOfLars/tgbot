from telegram.ext import MessageHandler, Filters
from telegram.ext.dispatcher import run_async

from tg_bot import dispatcher
import tg_bot.modules.sql.users_sql as sql

USERS_GROUP = 2


def get_user_id(username):
    if username.startswith('@'):
        user = sql.get_user_by_name(username[1:])
    else:
        user = sql.get_user_by_name(username)

    if user:
        return user.user_id

    return None


@run_async
def log_user(bot, update):
    if update.effective_message.from_user.username:
        sql.update_user(update.effective_message.from_user.id,
                        update.effective_message.from_user.username,
                        update.effective_chat.id,
                        update.effective_chat.title)


USER_HANDLER = MessageHandler(Filters.all & Filters.group, log_user)

dispatcher.add_handler(USER_HANDLER, USERS_GROUP)
