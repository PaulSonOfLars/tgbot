from io import BytesIO

from telegram import MessageEntity
from telegram.error import BadRequest, TelegramError
from telegram.ext import run_async, CommandHandler, MessageHandler, Filters
from telegram.utils.helpers import escape_markdown

import tg_bot.modules.sql.global_bans_sql as sql
from tg_bot import dispatcher, OWNER_ID, SUDO_USERS, SUPPORT_USERS, STRICT_GBAN
from tg_bot.modules.helper_funcs import CustomFilters, extract_user, can_restrict, user_not_admin, send_to_list
from tg_bot.modules.sql.users_sql import get_all_chats

GBAN_ENFORCE_GROUP = 6


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

    if int(user_id) in SUPPORT_USERS:
        message.reply_text("OOOH someone's trying to gban a support user! *grabs popcorn*")
        return

    if user_id == bot.id:
        message.reply_text("-_- So funny, lets gban myself why don't I? Nice try.")
        return

    try:
        user_chat = bot.get_chat(user_id)
    except BadRequest as excp:
        message.reply_text(excp.message)
        return

    if user_chat.type != 'private':
        message.reply_text("That's not a user!")
        return

    reason = ""

    if message.entities and message.parse_entities([MessageEntity.TEXT_MENTION]):
        entities = message.parse_entities([MessageEntity.TEXT_MENTION])
        end = entities[0].offset + entities[0].length
        reason = message.text[end:].strip()

    else:
        split_message = message.text.split(None, 2)
        if len(split_message) >= 3:
            reason = split_message[2]

    message.reply_text("*Blows dust off of banhammer* 😉")

    banner = update.effective_user
    send_to_list(bot, SUDO_USERS + SUPPORT_USERS,
                 "[{}](tg://user?id={}) is gbanning user [{}](tg://user?id={}) "
                 "because:\n{}".format(escape_markdown(banner.first_name),
                                       banner.id,
                                       escape_markdown(user_chat.first_name),
                                       user_chat.id, reason or "No reason given"),
                 markdown=True)

    sql.gban_user(user_id, user_chat.username or user_chat.first_name, reason)

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
                message.reply_text("Could not gban due to: {}".format(excp.message))
                send_to_list(bot, SUDO_USERS + SUPPORT_USERS, "Could not gban due to: {}".format(excp.message))
                sql.ungban_user(user_id)
                return
        except TelegramError:
            pass

    send_to_list(bot, SUDO_USERS + SUPPORT_USERS, "gban complete!")
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

    banner = update.effective_user

    message.reply_text("I'll give {} a second chance, globally.".format(user_chat.first_name))

    send_to_list(bot, SUDO_USERS + SUPPORT_USERS,
                 "[{}](tg://user?id={}) has ungbanned user [{}](tg://user?id={})".format(
                     escape_markdown(banner.first_name),
                     banner.id,
                     escape_markdown(user_chat.first_name),
                     user_chat.id),
                 markdown=True)

    sql.ungban_user(user_id)

    chats = get_all_chats()
    for chat in chats:
        chat_id = chat.chat_id
        try:
            member = bot.get_chat_member(chat_id, user_id)
            if member.status == 'kicked':
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
                bot.send_message(OWNER_ID, "Could not un-gban due to: {}".format(excp.message))
                return
        except TelegramError:
            pass

    send_to_list(bot, SUDO_USERS + SUPPORT_USERS, "un-gban complete!")

    message.reply_text("Person has been un-gbanned.")


@run_async
def gbanlist(bot, update):
    banned_users = sql.get_gban_list()

    if not banned_users:
        update.effective_message.reply_text("There aren't any gbanned users! You're kinder than I expected...")
        return

    banfile = 'Screw these guys.\n'
    for user in banned_users:
        banfile += "[x] {} - {}\n".format(user["name"], user["user_id"])
        if user["reason"]:
            banfile += "Reason: {}\n".format(user["reason"])

    with BytesIO(str.encode(banfile)) as output:
        output.name = "gbanlist.txt"
        update.effective_message.reply_document(document=output, filename="gbanlist.txt",
                                                caption="Here is the list of currently gbanned users.")


@run_async
@can_restrict
@user_not_admin
def enforce_gban(bot, update):
    user = update.effective_message.from_user
    if sql.is_user_gbanned(user.id):
        update.effective_chat.kick_member(user.id)
        update.effective_message.reply_text("This is a bad person, they shouldn't be here!")


def __user_info__(user_id):
    is_gbanned = sql.is_user_gbanned(user_id)

    text = "Globally banned: *{}*"
    if is_gbanned:
        text = text.format("Yes")
        user = sql.get_gbanned_user(user_id)
        if user.reason:
            text += "\nReason: {}".format(escape_markdown(user.reason))
    else:
        text = text.format("No")
    return text


__help__ = ""  # Sudo only module, no help.

__name__ = "GBans"

GBAN_HANDLER = CommandHandler("gban", gban, pass_args=True,
                              filters=CustomFilters.sudo_filter | CustomFilters.support_filter)
UNGBAN_HANDLER = CommandHandler("ungban", ungban, pass_args=True,
                                filters=CustomFilters.sudo_filter | CustomFilters.support_filter)
GBAN_LIST = CommandHandler("gbanlist", gbanlist,
                           filters=CustomFilters.sudo_filter | CustomFilters.support_filter)

GBAN_ENFORCER = MessageHandler(Filters.all & Filters.group, enforce_gban)

dispatcher.add_handler(GBAN_HANDLER)
dispatcher.add_handler(UNGBAN_HANDLER)
dispatcher.add_handler(GBAN_LIST)

if STRICT_GBAN:  # enforce GBANS if this is set
    dispatcher.add_handler(GBAN_ENFORCER, GBAN_ENFORCE_GROUP)
