from telegram import ParseMode
from telegram.error import BadRequest, TelegramError
from telegram.ext import run_async, CommandHandler
from telegram.utils.helpers import escape_markdown

from tg_bot import dispatcher, OWNER_ID, SUDO_USERS
from tg_bot.modules.helper_funcs import CustomFilters, extract_user, is_user_in_chat
from tg_bot.modules.sql.users_sql import get_all_chats


@run_async
def gban(bot, update, args):
    message = update.effective_message

    user_id = extract_user(message, args)
    if not user_id:
        message.reply_text("You don't seem to be referring to a user.")
        return

    if int(user_id) in SUDO_USERS:
        message.reply_text("I spy, with my little eye... a sudo user war! Why are you guys turning on each other?")
        return

    user_chat = bot.get_chat(user_id)
    if user_chat.type != 'private':
        message.reply_text("That's not a user!")
        return

    message.reply_text("*Blows dust off of banhammer* 😉")

    banner = update.effective_user

    bot.send_message(OWNER_ID,
                     "[{}](tg://user?id={}) has gbanned user [{}](tg://user?id={})".format(
                         escape_markdown(banner.first_name),
                         banner.id,
                         escape_markdown(user_chat.first_name),
                         user_chat.id),
                     parse_mode=ParseMode.MARKDOWN)

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

    user_chat = bot.get_chat(user_id)
    if user_chat.type != 'private':
        message.reply_text("That's not a user!")
        return

    message.reply_text("I'll give {} a second chance, globally.".format(user_chat.first_name))

    banner = update.effective_user

    bot.send_message(OWNER_ID,
                     "[{}](tg://user?id={}) has ungbanned user [{}](tg://user?id={})".format(
                         escape_markdown(banner.first_name),
                         banner.id,
                         escape_markdown(user_chat.first_name),
                         user_chat.id),
                     parse_mode=ParseMode.MARKDOWN)

    chats = get_all_chats()
    for chat in chats:
        chat_id = chat.chat_id
        try:
            if not is_user_in_chat(chat, user_id):
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
