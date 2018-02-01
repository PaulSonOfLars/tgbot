from telegram.error import BadRequest
from telegram.ext import Filters, MessageHandler, CommandHandler, run_async

from tg_bot import dispatcher
from tg_bot.modules.helper_funcs.chat_status import is_user_admin, user_admin, can_restrict
from tg_bot.modules.sql import antiflood_sql as sql

FLOOD_GROUP = 3


@run_async
def check_flood(bot, update):
    user = update.effective_user
    chat = update.effective_chat
    message = update.effective_message

    # ignore admins
    if is_user_admin(chat, user.id):
        sql.update_flood(chat.id, None)
        return

    should_ban = sql.update_flood(chat.id, user.id)
    if should_ban:
        try:
            chat.kick_member(user.id)
            message.reply_text("I like to leave the flooding to natural disasters. But you, you were just a "
                               "disappointment. Get out.")

        except BadRequest:
            message.reply_text("I can't kick people here, give me permissions first!")


@run_async
@user_admin
@can_restrict
def set_flood(bot, update, args):
    chat = update.effective_chat
    message = update.effective_message

    if len(args) >= 1:
        val = args[0].lower()
        if val == "off" or val == "no" or val == "0":
            sql.set_flood(chat.id, 0)
            message.reply_text("Antiflood has been disabled.")

        elif val.isdigit():
            amount = int(val)
            if amount <= 0:
                sql.set_flood(chat.id, 0)
                message.reply_text("Antiflood has been disabled.")

            elif amount < 3:
                message.reply_text("Antiflood has to be either 0 (disabled), or a number bigger than 3!")

            else:
                sql.set_flood(chat.id, amount)
                message.reply_text("Antiflood has been updated and set to {}".format(amount))

        else:
            message.reply_text("Unrecognised argument - please use a number, 'off', or 'no'.")


@run_async
def flood(bot, update):
    chat = update.effective_chat

    flood_settings = sql.get_flood(chat.id)
    if not flood_settings or flood_settings.limit == 0:
        update.effective_message.reply_text("I'm not currently enforcing flood control!")
    else:
        update.effective_message.reply_text(
            "I'm currently banning users if they send more than {} consecutive messages.".format(flood_settings.limit))


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


__help__ = """
 - /flood: Get the current flood control setting

*Admin only:*
 - /setflood <int/'no'/'off'>: enables or disables flood control
"""

__name__ = "AntiFlood"

FLOOD_BAN_HANDLER = MessageHandler(Filters.all & ~Filters.status_update, check_flood)
SET_FLOOD_HANDLER = CommandHandler("setflood", set_flood, pass_args=True)
FLOOD_HANDLER = CommandHandler("flood", flood)

dispatcher.add_handler(FLOOD_BAN_HANDLER, FLOOD_GROUP)
dispatcher.add_handler(SET_FLOOD_HANDLER)
dispatcher.add_handler(FLOOD_HANDLER)
