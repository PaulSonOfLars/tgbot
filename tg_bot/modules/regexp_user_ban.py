import html
import re
from typing import Optional, List

from telegram import Message, Chat, Update, Bot, User
from telegram.error import BadRequest
from telegram.ext import run_async, CommandHandler, Filters, MessageHandler
from telegram.utils.helpers import mention_html

from tg_bot import dispatcher, BAN_STICKER, LOGGER, SUDO_USERS
from tg_bot.modules.disable import DisableAbleCommandHandler
from tg_bot.modules.helper_funcs.chat_status import bot_admin, user_admin, is_user_ban_protected, can_restrict, \
    is_user_admin, is_user_in_chat, bot_can_delete
from tg_bot.modules.helper_funcs.extraction import extract_user_and_text
from tg_bot.modules.helper_funcs.string_handling import extract_time
from tg_bot.modules.log_channel import loggable
from tg_bot.modules.sql import users_sql
from tg_bot.modules.sql import regex_user_bans_sql as sql

# /regexpuserban [regex]
# /listregexpuserban
# /regexpuserunban [regex]
# example regex .*\d+
# 

# /g_regexpuserban [regex]
# /g_listregexpuserban
# /g_regexpuserunban [regex]

@user_admin
@bot_can_delete
@loggable
def regexpuserban(bot: Bot, update: Update, args: List[str]) -> str:
    message = update.effective_message  # type: Optional[Message]
    chat_id = update.effective_chat.id

    regex = args[0]
    if regex is None:
        update.effective_message.reply_text("Regexp value is missing")
        return
    sql.add_regex_bans(chat_id, regex)
    update.effective_message.reply_text("Regex " + regex + " was added to ban list")

@user_admin
@loggable
def listregexpuserban(bot: Bot, update: Update):
    res = sql.get_regex_bans(update.effective_chat.id)
    if res is not None:
        res = list(map(lambda x: x.regex_to_ban, res))
        update.effective_message.reply_text("Regexp banned in this chat: " + ','.join(res))
    elif res is [] or res is None:
        update.effective_message.reply_text("There are no regexp in ban")

@run_async
@user_admin
@loggable
def regexpuserunban(bot: Bot, update: Update, args: List[str]):
    regex = args[0]
    if regex is None:
        update.effective_message.reply_text("Regexp value is missing")
        return
    chat_id = update.effective_chat.id
    sql.delete_regex_ban(chat_id, regex)
    update.effective_message.reply_text("Regexp " + regex + " was removed from ban list")

@user_admin
@bot_can_delete
@loggable
def g_regexpuserban(bot: Bot, update: Update, args: List[str]) -> str:
    if int(update.effective_user.id) not in SUDO_USERS:
        update.effective_message.reply_text("Only SUDO users can use this command")
        return

    message = update.effective_message  # type: Optional[Message]

    regex = args[0]
    if regex is None:
        update.effective_message.reply_text("Regexp value is missing")
        return
    sql.add_regex_global_bans(regex)
    update.effective_message.reply_text("Regex " + regex + " was added to global ban list")

@user_admin
@loggable
def g_listregexpuserban(bot: Bot, update: Update):
    if int(update.effective_user.id) not in SUDO_USERS:
        update.effective_message.reply_text("Only SUDO users can use this command")
        return

    res = sql.get_regex_global_bans()
    if res is not None:
        res = list(map(lambda x: x.regex_to_ban, res))
        update.effective_message.reply_text("Regexp banned globally: " + ','.join(res))
    elif res is [] or res is None:
        update.effective_message.reply_text("There are no regexp in ban globally")

@run_async
@user_admin
@loggable
def g_regexpuserunban(bot: Bot, update: Update, args: List[str]):
    if int(update.effective_user.id) not in SUDO_USERS:
        update.effective_message.reply_text("Only SUDO users can use this command")
        return

    regex = args[0]
    if regex is None:
        update.effective_message.reply_text("Regexp value is missing")
        return
    chat_id = update.effective_chat.id
    sql.delete_regex_global_ban(regex)
    update.effective_message.reply_text("Regexp " + regex + " was removed from global ban list")

@run_async
def remove_banned_nicknames(bot: Bot, update: Update):
    joined_names = update.effective_message.new_chat_members
    chat = update.effective_chat
    regexes = list(map(lambda x: x.regex_to_ban, sql.get_regex_bans(chat.id)))
    regexes_global = list(map(lambda x: x.regex_to_ban, sql.get_regex_global_bans()))

    if joined_names is not None:
        for name in joined_names:
            for regex in regexes:
                is_banned = re.match(regex, name.username)

                if is_banned:
                    update.effective_message.reply_text("#бан_банан тебе 🍌")
                    chat.kick_member(name.id)
                    break

            for regex in regexes_global:
                is_banned = re.match(regex, name.username)

                if is_banned:
                    update.effective_message.reply_text("You're not welcome globally!")
                    chat.kick_member(name.id)
                    break

                # is_exists_in_global = sql.is_global_regex_ban_exists(joined_name)
                # if is_exists_in_global:
                #     update.effective_message.reply_text("User fitting " + regex + " banned in global ban list")
                #     update.effective_message.delete()
                #     break

__help__ = """
*Admin only:*
Usernames processed without @ symbol at the start E.g example_name instead of @example_name
 - /regexpuserban [regex] - ban new users by regexp
 - /listregexpuserban - list regexp bans
 - /regexpuserunban [regex] - unban new users by regexp. Does not unban users already banned.
 - /g\_regexpuserban [regex] - ban new users globally by regexp
 - /g\_listregexpuserban - list regexp global bans
 - /g\_regexpuserunban [regex] - unban new users by regexp. Does not unban users already banned.
"""

__mod_name__ = "Bans Regexp"

REGEXPUSERBAN_HANDLER = CommandHandler("regexpuserban", regexpuserban, pass_args=True, filters=Filters.group)
LISTREGEXPUSERBAN_HANDLER = CommandHandler("listregexpuserban", listregexpuserban, pass_args=False, filters=Filters.group)
UNBANREGEXPUSERBAN_HANDLER = CommandHandler("regexpuserunban", regexpuserunban, pass_args=True, filters=Filters.group)

G_REGEXPUSERBAN_HANDLER = CommandHandler("g_regexpuserban", g_regexpuserban, pass_args=True, filters=Filters.group)
G_LISTREGEXPUSERBAN_HANDLER = CommandHandler("g_listregexpuserban", g_listregexpuserban, pass_args=False, filters=Filters.group)
G_UNBANREGEXPUSERBAN_HANDLER = CommandHandler("g_regexpuserunban", g_regexpuserunban, pass_args=True, filters=Filters.group)

dispatcher.add_handler(REGEXPUSERBAN_HANDLER)
dispatcher.add_handler(LISTREGEXPUSERBAN_HANDLER)
dispatcher.add_handler(UNBANREGEXPUSERBAN_HANDLER)

dispatcher.add_handler(G_REGEXPUSERBAN_HANDLER)
dispatcher.add_handler(G_LISTREGEXPUSERBAN_HANDLER)
dispatcher.add_handler(G_UNBANREGEXPUSERBAN_HANDLER)


PERM_GROUP = 5

dispatcher.add_handler(MessageHandler(Filters.status_update.new_chat_members, remove_banned_nicknames), PERM_GROUP)
