from typing import Optional

from telegram import Message, Chat, Update, Bot
from telegram.error import BadRequest
from telegram.ext import CommandHandler
from telegram.ext.dispatcher import run_async

from tg_bot import dispatcher, LOGGER
from tg_bot.modules.helper_funcs.chat_status import user_admin, can_delete


@run_async
@user_admin
def purge(bot: Bot, update: Update):
    msg = update.effective_message  # type: Optional[Message]
    if msg.reply_to_message:
        chat = update.effective_chat  # type: Optional[Chat]
        if can_delete(chat, bot.id):
            message_id = msg.reply_to_message.message_id
            curr_message_id = msg.message_id
            for m_id in range(curr_message_id, message_id - 1, -1):  # Reverse iteration over message ids
                try:
                    bot.deleteMessage(chat.id, m_id)
                except BadRequest as err:
                    if err.message == "Message can't be deleted":
                        bot.send_message(chat.id, "Cannot delete messages. The messages may be too old, I might not "
                                                  "have delete rights, or this might not be a supergroup.")
                        break

                    elif err.message != "Message to delete not found":
                        LOGGER.exception("Error while purging chat messages.")
            bot.send_message(chat.id, "Purge complete.")
    else:
        msg.reply_text("Reply to a message to select where to start purging from.")


@run_async
@user_admin
def del_message(bot: Bot, update: Update):
    if update.effective_message.reply_to_message:
        chat = update.effective_chat  # type: Optional[Chat]
        if can_delete(chat, bot.id):
            update.effective_message.reply_to_message.delete()
            update.effective_message.delete()
    else:
        update.effective_message.reply_text("Whadya want to delete?")


__help__ = """
*Admin only:*
 - /del: deletes the message you replied to
 - /purge: deletes all messages between this and the replied to message
"""

__name__ = "Purges"


DELETE_HANDLER = CommandHandler("del", del_message)
PURGE_HANDLER = CommandHandler("purge", purge)

dispatcher.add_handler(DELETE_HANDLER)
dispatcher.add_handler(PURGE_HANDLER)
