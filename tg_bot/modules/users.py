from time import sleep

from telegram import TelegramError
from telegram.ext import MessageHandler, Filters, CommandHandler
from telegram.ext.dispatcher import run_async

import tg_bot.modules.sql.users_sql as sql
from tg_bot import dispatcher, OWNER_ID, LOGGER

USERS_GROUP = 4


def get_user_id(username):
    # ensure valid userid
    if len(username) <= 5:
        return None

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
        failed = 0
        for chat in chats:
            try:
                bot.sendMessage(int(chat.chat_id), to_send[1])
                sleep(0.1)
            except TelegramError:
                failed += 1
                LOGGER.warning("Couldn't send broadcast to %s, group name %s", str(chat.chat_id), str(chat.chat_name))

        update.effective_message.reply_text("Broadcast complete. {} groups failed to receive the message, probably "
                                            "due to being kicked.".format(failed))


@run_async
def log_user(bot, update):
    sql.update_user(update.effective_message.from_user.id,
                    update.effective_message.from_user.username,
                    update.effective_chat.id,
                    update.effective_chat.title)
    if update.effective_message.forward_from:
        sql.update_user(update.effective_message.forward_from.id,
                        update.effective_message.forward_from.username)


def __user_info__(user_id):
    if user_id == dispatcher.bot.id:
        return """I've seen them in... Wow. Are they stalking me? They're in all the same places I am... oh. It's me."""
    num_chats = sql.get_user_num_chats(user_id)
    return """I've seen them in {} chats in total.""".format(num_chats)


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
