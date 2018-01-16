import sys
from time import sleep

from telegram import TelegramError
from telegram.ext import MessageHandler, Filters, CommandHandler
from telegram.ext.dispatcher import run_async

import tg_bot.modules.sql.users_sql as sql
from tg_bot import dispatcher, OWNER_ID

USERS_GROUP = 2


def get_user_id(username):
    if username.startswith('@'):
        user = sql.get_userid_by_name(username[1:])
    else:
        user = sql.get_userid_by_name(username)

    if user:
        return user.user_id

    return None


@run_async
def broadcast(bot, update):
    to_send = update.effective_message.text.split(None, 1)
    if len(to_send) >= 2:
        chats = sql.get_all_chats() or []
        for chat in chats:
            try:
                bot.sendMessage(int(chat.chat_id), to_send[1])
                sleep(0.1)
            except TelegramError:
                print("Couldn't send broadcast to {}, group name {}".format(chat.chat_id, chat.chat_name),
                      file=sys.stderr)


@run_async
def log_user(bot, update):
    if update.effective_message.from_user.username:
        sql.update_user(update.effective_message.from_user.id,
                        update.effective_message.from_user.username,
                        update.effective_chat.id,
                        update.effective_chat.title)


def __stats__():
    return "{} users, across {} chats".format(sql.num_users(), sql.num_chats())


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


__help__ = ""  # no help string

__name__ = "Users"


BROADCAST_HANDLER = (CommandHandler("broadcast", broadcast, filters=Filters.user(OWNER_ID)))
USER_HANDLER = MessageHandler(Filters.all & Filters.group, log_user)

dispatcher.add_handler(USER_HANDLER, USERS_GROUP)
dispatcher.add_handler(BROADCAST_HANDLER)
