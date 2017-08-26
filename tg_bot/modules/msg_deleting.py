from telegram.error import BadRequest
from telegram.ext import CommandHandler
from telegram.ext.dispatcher import run_async
from tg_bot import dispatcher
from tg_bot.modules.helper_funcs import can_delete, is_user_admin


@run_async
def purge(bot, update):
    curr_message = update.effective_message
    chat = update.effective_chat
    user_id = curr_message.from_user.id
    if curr_message.reply_to_message and can_delete(chat, bot.id) and is_user_admin(chat, user_id):
        message_id = curr_message.reply_to_message.message_id
        curr_message_id = curr_message.message_id
        for m_id in range(message_id, curr_message_id + 1):  # +1 to include curr message
            try:
                bot.deleteMessage(chat.id, m_id)
            except BadRequest as err:
                print(err)
        bot.send_message(chat.id, "Purge complete.", 'Markdown')


@run_async
def del_message(bot, update):
    curr_message = update.effective_message
    chat = update.effective_chat
    user_id = curr_message.from_user.id
    if curr_message.reply_to_message and can_delete(chat, bot.id) and is_user_admin(chat, user_id):
        update.effective_message.reply_to_message.delete()
        update.effective_message.delete()

__help__ = """
 - /del: deletes the message you replied to
 - /purge: deletes all messages between this and the replied to message
"""

DELETE_HANDLER = CommandHandler("del", del_message)
PURGE_HANDLER = CommandHandler("purge", purge)

dispatcher.add_handler(DELETE_HANDLER)
dispatcher.add_handler(PURGE_HANDLER)
