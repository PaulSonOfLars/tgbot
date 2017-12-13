import time

from telegram import MessageEntity
from telegram.error import Unauthorized, RetryAfter, BadRequest, ChatMigrated, TelegramError
from telegram.ext import run_async, CommandHandler

from tg_bot import dispatcher
from tg_bot.modules.helper_funcs import SudoFilter
from tg_bot.modules.sql.users_sql import get_all_chats
from tg_bot.modules.users import get_user_id


@run_async
def gban(bot, update, args):
    message = update.effective_message
    prev_message = message.reply_to_message

    if message.entities and message.parse_entities([MessageEntity.TEXT_MENTION]):
        entities = message.parse_entities([MessageEntity.TEXT_MENTION])
        print(entities)
        for e in entities:
            user_id = e.user.id
            message.reply_text(user_id)
            return
        else:
            return

    elif len(args) >= 1 and args[0][0] == '@':
        user = args[0]
        user_id = get_user_id(user)
        if not user_id:
            message.reply_text("I don't have that user in my db. You'll be able to interact with them if "
                               "you reply to that person's message instead.")
            return

    elif len(args) >= 1 and args[0].isdigit():
        user_id = int(args[0])

    elif prev_message:
        user_id = prev_message.from_user.id

    else:
        message.reply_text("You don't seem to be referring to a user.")
        return

    message.reply_text("*Blows dust off of banhammer* 😉")  # TODO: get user name from tg?

    chats = get_all_chats()
    for chat in chats:
        chat_id = chat.chat_id
        try:
            bot.kick_chat_member(chat_id, user_id)
        except BadRequest as e:
            if e.message == "User is an administrator of the chat":
                pass
            elif e.message == "Chat not found":
                pass
            elif e.message == "Not enough rights to restrict/unrestrict chat member":
                pass
            elif e.message == "User_not_participant":
                pass
            else:
                message.reply_text("Could not un-gban due to: {}".format(e.message))
                return
        except TelegramError:
            pass

    message.reply_text("Person has been gbanned.")


@run_async
def ungban(bot, update, args):
    message = update.effective_message
    prev_message = message.reply_to_message

    if message.entities and message.parse_entities([MessageEntity.TEXT_MENTION]):
        entities = message.parse_entities([MessageEntity.TEXT_MENTION])
        for e in entities:
            user_id = e.user.id
            break
        else:
            return

    elif len(args) >= 1 and args[0][0] == '@':
        user = args[0]
        user_id = get_user_id(user)
        if not user_id:
            message.reply_text("I don't have that user in my db. You'll be able to interact with them if "
                               "you reply to that person's message instead.")
            return

    elif len(args) >= 1 and args[0].isdigit():
        user_id = int(args[0])

    elif prev_message:
        user_id = prev_message.from_user.id

    else:
        message.reply_text("You don't seem to be referring to a user.")
        return

    message.reply_text("I'll give them a second chance, globally.")  # TODO: get user name from tg?

    chats = get_all_chats()
    for chat in chats:
        chat_id = chat.chat_id
        try:
            bot.unban_chat_member(chat_id, user_id)
        except BadRequest as e:
            if e.message == "User is an administrator of the chat":
                pass
            elif e.message == "Chat not found":
                pass
            elif e.message == "Not enough rights to restrict/unrestrict chat member":
                pass
            elif e.message == "User_not_participant":
                pass
            else:
                message.reply_text("Could not un-gban due to: {}".format(e.message))
                return
        except TelegramError:
            pass

    message.reply_text("Person has been un-gbanned.")


__help__ = ""  # Sudo only module, no help.

GBAN_HANDLER = CommandHandler("gban", gban, pass_args=True, filters=SudoFilter)
UNGBAN_HANDLER = CommandHandler("ungban", ungban, pass_args=True, filters=SudoFilter)

dispatcher.add_handler(GBAN_HANDLER)
dispatcher.add_handler(UNGBAN_HANDLER)
