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
from tg_bot.modules.sql import regex_name_bans_sql as sql

@user_admin
@bot_can_delete
@loggable
def regexpnameban(bot: Bot, update: Update, args: List[str]) -> str:
    message = update.effective_message  # type: Optional[Message]
    chat_id = update.effective_chat.id

    regex = args[0]
    if regex is None:
        update.effective_message.reply_text("Regexp value is missing")
        return
    sql.add_regex_bans(chat_id, regex)
    update.effective_message.reply_text("Regex name " + regex + " was added to name ban list")

@user_admin
@loggable
def listregexpnameban(bot: Bot, update: Update):
    res = sql.get_regex_bans(update.effective_chat.id)
    if res is not None:
        res = list(map(lambda x: x.regex_to_ban, res))
        update.effective_message.reply_text("Regexp banned in this chat: " + ' || '.join(res))
    elif res is [] or res is None:
        update.effective_message.reply_text("There are no regexp in name ban")

@run_async
@user_admin
@loggable
def regexpnameunban(bot: Bot, update: Update, args: List[str]):
    regex = args[0]
    if regex is None:
        update.effective_message.reply_text("Regexp value is missing")
        return
    chat_id = update.effective_chat.id
    sql.delete_regex_ban(chat_id, regex)
    update.effective_message.reply_text("Regexp name " + regex + " was removed from name ban list")

@user_admin
@bot_can_delete
@loggable
def g_regexpnameban(bot: Bot, update: Update, args: List[str]) -> str:
    if int(update.effective_user.id) not in SUDO_USERS:
        update.effective_message.reply_text("Only SUDO users can use this command")
        return

    message = update.effective_message  # type: Optional[Message]

    regex = args[0]
    if regex is None:
        update.effective_message.reply_text("Regexp value is missing")
        return
    sql.add_regex_global_bans(regex)
    update.effective_message.reply_text("Regex " + regex + " was added to global name ban list")

@user_admin
@loggable
def g_listregexpnameban(bot: Bot, update: Update):
    if int(update.effective_user.id) not in SUDO_USERS:
        update.effective_message.reply_text("Only SUDO users can use this command")
        return

    res = sql.get_regex_global_bans()
    if res is not None:
        res = list(map(lambda x: x.regex_to_ban, res))
        update.effective_message.reply_text("Regexp banned globally: " + ' || '.join(res))
    elif res is [] or res is None:
        update.effective_message.reply_text("There are no regexp in ban globally")

@run_async
@user_admin
@loggable
def g_regexpnameunban(bot: Bot, update: Update, args: List[str]):
    if int(update.effective_user.id) not in SUDO_USERS:
        update.effective_message.reply_text("Only SUDO users can use this command")
        return

    regex = args[0]
    if regex is None:
        update.effective_message.reply_text("Regexp value is missing")
        return
    chat_id = update.effective_chat.id
    sql.delete_regex_global_ban(regex)
    update.effective_message.reply_text("Regexp " + regex + " was removed from global name ban list")

@run_async
def remove_banned_nicknames(bot: Bot, update: Update):
    joined_names = update.effective_message.new_chat_members
    chat = update.effective_chat
    regexes = list(map(lambda x: x.regex_to_ban, sql.get_regex_bans(chat.id)))
    regexes_global = list(map(lambda x: x.regex_to_ban, sql.get_regex_global_bans()))

    if joined_names is not None:
        for name in joined_names:
            for regex in regexes:
                is_banned = re.match(regex, name.first_name) or re.match(regex, name.last_name)

                if is_banned:
                    update.effective_message.reply_text("#бан_банан тебе!")
                    chat.kick_member(name.id)
                    break

            for regex in regexes_global:
                is_banned = re.match(regex, name.username)

                if is_banned:
                    update.effective_message.reply_text("#бан_банан тебе!")
                    chat.kick_member(name.id)
                    break

__help__ = """
*Только администратор:*
Блокирует новых участников чата, имя или фамилия которых соответствуют одному из добавленных шаблонов регулярных выражений.
Regexp проверяет как имя, так и фамилию.
 - /name\_regexpban\_add [регулярное выражение] - добавить регулярное выражение
 - /name\_regexpban\_list - перечислить все регулярные выражения
 - /name\_regexpban\_del [регулярное выражение] - удалить регулярное выражение

 - /g\_name\_regexpban\_add [регулярное выражение] - добавить глобальное регулярное выражение
 - /g\_name\_regexpban\_list - перечислить все глобальные регулярные выражения
 - /g\_name\_regexpban\_del [регулярное выражение] - удалить глобальное регулярное выражение
"""

__mod_name__ = "Regexp имя бан"

REGEXPNAMEBAN_HANDLER = CommandHandler("name_regexpban_add", regexpnameban, pass_args=True, filters=Filters.group)
LISTREGEXPNAMEBAN_HANDLER = CommandHandler("name_regexpban_list", listregexpnameban, pass_args=False, filters=Filters.group)
UNBANREGEXPNAMEBAN_HANDLER = CommandHandler("name_regexpban_del", regexpnameunban, pass_args=True, filters=Filters.group)

G_REGEXPNAMEBAN_HANDLER = CommandHandler("g_name_regexpban_add", g_regexpnameban, pass_args=True, filters=Filters.group)
G_LISTREGEXPNAMEBAN_HANDLER = CommandHandler("g_name_regexpban_list", g_listregexpnameban, pass_args=False, filters=Filters.group)
G_UNBANREGEXPNAMEBAN_HANDLER = CommandHandler("g_name_regexpban_del", g_regexpnameunban, pass_args=True, filters=Filters.group)

dispatcher.add_handler(REGEXPNAMEBAN_HANDLER)
dispatcher.add_handler(LISTREGEXPNAMEBAN_HANDLER)
dispatcher.add_handler(UNBANREGEXPNAMEBAN_HANDLER)

dispatcher.add_handler(G_REGEXPNAMEBAN_HANDLER)
dispatcher.add_handler(G_LISTREGEXPNAMEBAN_HANDLER)
dispatcher.add_handler(G_UNBANREGEXPNAMEBAN_HANDLER)

PERM_GROUP = 6

dispatcher.add_handler(MessageHandler(Filters.status_update.new_chat_members, remove_banned_nicknames), PERM_GROUP)
