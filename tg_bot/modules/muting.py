from telegram.ext import CommandHandler, MessageHandler, Filters
from telegram.ext.dispatcher import run_async
import tg_bot.modules.sql.muting_sql as sql


def can_delete(bot, update):
    return update.effective_chat.get_member(bot.id).can_delete_messages


def is_user_admin(chat, user_id):
    return chat.get_member(user_id).status == 'administrator'


@run_async
def del_muted(bot, update):
    curr_message = update.effective_message
    chat_id = update.effective_chat.id
    user_id = curr_message.from_user.id

    if can_delete(bot, update):
        if sql.is_user_muted(chat_id, user_id):
            curr_message.delete()
        else:
            raise DispatcherHandlerContinue


def mute(bot, update):
    curr_message = update.effective_message
    chat = update.effective_chat
    print(curr_message.reply_to_message)
    if curr_message.reply_to_message:
        user_id = curr_message.reply_to_message.from_user.id
        if not is_user_admin(chat, user_id):
            sql.mute_user(chat.id, user_id)
        else:
            curr_message.reply_text("Cannot mute an admin!")


def unmute(bot, update, args):
    # TODO
    pass

MUTE_HANDLER = CommandHandler("mute", mute)
UNMUTE_HANDLER = CommandHandler("unmute", unmute, pass_args=True)
DEL_MUTED_HANDLER = MessageHandler(Filters.all, del_muted)

# NOTE: nice to keep msg_deleting first in loadorder.txt to get this to work properly.
# Currently disabled because HandlerContinue wont import
# dispatcher.add_handler(DEL_MUTED_HANDLER)
# dispatcher.add_handler(MUTE_HANDLER)
# dispatcher.add_handler(UNMUTE_HANDLER)
