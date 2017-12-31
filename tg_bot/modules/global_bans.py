from telegram.error import BadRequest, TelegramError
from telegram.ext import run_async, CommandHandler

from tg_bot import dispatcher
from tg_bot.modules.helper_funcs import CustomFilters, extract_user
from tg_bot.modules.sql.users_sql import get_all_chats


@run_async
def gban(bot, update, args):
    message = update.effective_message

    user_id = extract_user(message, args)
    if not user_id:
        message.reply_text("You don't seem to be referring to a user.")
        return

    message.reply_text("*Blows dust off of banhammer* 😉")  # TODO: get user name from tg?

    chats = get_all_chats()
    for chat in chats:
        chat_id = chat.chat_id
        try:
            bot.kick_chat_member(chat_id, user_id)
        except BadRequest as excp:
            if excp.message == "User is an administrator of the chat":
                pass
            elif excp.message == "Chat not found":
                pass
            elif excp.message == "Not enough rights to restrict/unrestrict chat member":
                pass
            elif excp.message == "User_not_participant":
                pass
            else:
                message.reply_text("Could not un-gban due to: {}".format(excp.message))
                return
        except TelegramError:
            pass

    message.reply_text("Person has been gbanned.")


@run_async
def ungban(bot, update, args):
    message = update.effective_message

    user_id = extract_user(message, args)
    if not user_id:
        message.reply_text("You don't seem to be referring to a user.")
        return

    message.reply_text("I'll give them a second chance, globally.")  # TODO: get user name from tg?

    chats = get_all_chats()
    for chat in chats:
        chat_id = chat.chat_id
        try:
            bot.unban_chat_member(chat_id, user_id)
        except BadRequest as excp:
            if excp.message == "User is an administrator of the chat":
                pass
            elif excp.message == "Chat not found":
                pass
            elif excp.message == "Not enough rights to restrict/unrestrict chat member":
                pass
            elif excp.message == "User_not_participant":
                pass
            elif excp.message == "Method is available for supergroup and channel chats only":
                pass
            else:
                message.reply_text("Could not un-gban due to: {}".format(excp.message))
                return
        except TelegramError:
            pass

    message.reply_text("Person has been un-gbanned.")


__help__ = ""  # Sudo only module, no help.

GBAN_HANDLER = CommandHandler("gban", gban, pass_args=True, filters=CustomFilters.sudo_filter)
UNGBAN_HANDLER = CommandHandler("ungban", ungban, pass_args=True, filters=CustomFilters.sudo_filter)

dispatcher.add_handler(GBAN_HANDLER)
dispatcher.add_handler(UNGBAN_HANDLER)
