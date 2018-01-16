import re

import telegram
from telegram import MessageEntity, InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.ext import CommandHandler, run_async, DispatcherHandlerStop, MessageHandler, Filters, CallbackQueryHandler
from telegram.utils.helpers import escape_markdown

from tg_bot import dispatcher
from tg_bot.modules.helper_funcs import user_admin, bot_admin, is_user_admin, user_admin_no_reply, extract_text, \
    split_message
from tg_bot.modules.sql import warns_sql as sql
from tg_bot.modules.users import get_user_id

WARN_HANDLER_GROUP = 9
CURRENT_WARNING_FILTER_STRING = "*Current warning filters in this chat:*\n"


# TODO: Make a single user_id and argument extraction function! this one is inaccurate
def extract_userid(message):
    args = message.text.split(None, 2)  # use python's maxsplit to separate Cmd, warn recipient, and warn reason

    if message.entities and message.parse_entities([MessageEntity.TEXT_MENTION]):
        entities = message.parse_entities([MessageEntity.TEXT_MENTION])
        for ent in entities:
            return ent.user.id, message.text[ent.offset + ent.length:]

    elif len(args) >= 2 and args[1][0] == '@':
        user = args[1]
        user_id = get_user_id(user)
        if not user_id:
            message.reply_text("I don't have that user in my db. You'll be able to interact with them if "
                               "you reply to that person's message instead.")
            return None, ""
        return user_id, (args[2] if len(args) >= 3 else "")

    elif len(args) >= 2 and args[0].isdigit():
        return int(args[0]), (args[2] if len(args) >= 3 else "")

    elif message.reply_to_message:
        split = message.text.split(None, 1)
        return message.reply_to_message.from_user.id, (split[1] if len(split) >= 2 else "")

    else:
        return None, ""


def warn(user_id, chat, reason, bot, message):
    if is_user_admin(chat, user_id):
        message.reply_text("Damn admins, can't even be warned!")
        return

    user_warned = sql.warn_user(user_id, chat.id, reason)
    if user_warned.num_warns >= 3:
        res = chat.kick_member(user_id)
        if res:
            bot.send_sticker(chat.id, 'CAADAgADOwADPPEcAXkko5EB3YGYAg')  # banhammer marie sticker
            message.reply_text("3 warnings, this user has been banned!")
            sql.reset_warns(user_id, chat.id)
        else:
            message.reply_text("An error occurred, I couldn't ban this person!")
    else:
        keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton("Remove warn", callback_data="rm_warn({})".format(user_id))]])
        if reason:
            message.reply_text(
                "{}/3 warnings... watch out! Latest one was because:\n{}".format(user_warned.num_warns, reason),
                reply_markup=keyboard)
        else:
            message.reply_text("{}/3 warnings... watch out!".format(user_warned.num_warns), reply_markup=keyboard)


@run_async
@user_admin_no_reply
@bot_admin
def button(bot, update):
    query = update.callback_query
    match = re.match(r"rm_warn\((.+?)\)", query.data)
    if match:
        user_id = match.group(1)
        chat_id = update.effective_chat.id
        res = sql.remove_warn(user_id, chat_id)
        if res:
            update.effective_message.edit_text("Warn removed.")


@run_async
@user_admin
@bot_admin
def warn_user(bot, update):
    message = update.effective_message
    chat = update.effective_chat

    user_id, reason = extract_userid(message)

    if user_id:
        warn(user_id, chat, reason, bot, message)
    else:
        message.reply_text("No user was designated!")


@run_async
@user_admin
@bot_admin
def reset_warns(bot, update):
    message = update.effective_message
    chat = update.effective_chat

    user_id, _ = extract_userid(message)
    if user_id:
        sql.reset_warns(user_id, chat.id)
        message.reply_text("Warnings have been reset!")
    else:
        message.reply_text("No user has been designated!")


@run_async
def warns(bot, update):
    message = update.effective_message
    user_id, _ = extract_userid(message) or (update.effective_user.id, None)
    warned_user = sql.get_warns(user_id, update.effective_chat.id)
    if warned_user and warned_user.num_warns != 0:
        if warned_user.reasons:
            text = "This user has {} warnings, for the following reasons:".format(warned_user.num_warns)
            for reason in warned_user.reasons:
                text += "\n - {}".format(reason)

            msgs = split_message(text)
            for msg in msgs:
                update.effective_message.reply_text(msg)
        else:
            update.effective_message.reply_text(
                "User has {} warnings, but no reasons for any of them.".format(warned_user.num_warns))
    else:
        update.effective_message.reply_text("This user hasn't got any warnings!")


@user_admin
def add_warn_filter(bot, update):
    chat = update.effective_chat
    msg = update.effective_message
    args = msg.text.split(None, 2)  # use python's maxsplit to separate Cmd, keyword, and reply_text

    if len(args) >= 3:
        keyword = args[1]
        content = args[2]

    else:
        return

    # Note: perhaps handlers can be removed somehow using sql.get_chat_filters
    for handler in dispatcher.handlers.get(WARN_HANDLER_GROUP, []):
        if handler.filters == (keyword, chat.id):
            dispatcher.remove_handler(handler, WARN_HANDLER_GROUP)

    sql.add_warn_filter(chat.id, keyword, content)

    update.effective_message.reply_text("Warn handler added for {}!".format(keyword))
    raise DispatcherHandlerStop


@user_admin
def remove_warn_filter(bot, update, args):
    chat = update.effective_chat

    if len(args) < 1:
        return

    chat_filters = sql.get_chat_warn_filters(chat.id)

    if not chat_filters:
        update.effective_message.reply_text("No warning filters are active here!")
        return

    for filt in chat_filters:
        if filt.chat_id == str(chat.id) and filt.keyword == args[0]:
            sql.remove_warn_filter(chat.id, args[0])
            update.effective_message.reply_text("Yep, I'll stop warning people for that.")
            raise DispatcherHandlerStop

    update.effective_message.reply_text("That's not a current warning filter - run /warnlist for all \
    active warning filters.")


@run_async
def list_warn_filters(bot, update):
    chat = update.effective_chat
    all_handlers = sql.get_chat_warn_filters(chat.id)

    if not all_handlers:
        update.effective_message.reply_text("No warning filters are active here!")
        return

    filter_list = CURRENT_WARNING_FILTER_STRING
    for handler in all_handlers:
        entry = " - {}\n".format(escape_markdown(handler.keyword))
        if len(entry) + len(filter_list) > telegram.MAX_MESSAGE_LENGTH:
            update.effective_message.reply_text(filter_list, parse_mode=ParseMode.MARKDOWN)
            filter_list = entry
        else:
            filter_list += entry

    if not filter_list == CURRENT_WARNING_FILTER_STRING:
        update.effective_message.reply_text(filter_list, parse_mode=ParseMode.MARKDOWN)


@run_async
def reply_filter(bot, update):
    chat_warn_filters = sql.get_chat_warn_filters(update.effective_chat.id)
    message = update.effective_message
    to_match = extract_text(message)
    if not to_match:
        return

    for warn_filter in chat_warn_filters:
        pattern = r"( |^|[^\w])" + re.escape(warn_filter.keyword) + r"( |$|[^\w])"
        if re.search(pattern, to_match, flags=re.IGNORECASE):
            user_id = update.effective_user.id
            chat = update.effective_chat
            warn(user_id, chat, warn_filter.reply, bot, message)


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


__help__ = """
 - /warn <userhandle>: warn a user. After 3 warns, the user will be banned from the group. Can also be used as a reply.
 - /resetwarn <userhandle>: reset the warnings for a user. Can also be used as a reply.
 - /warns <userhandle>: get a user's number, and reason, of warnings.
 - /addwarn <keyword> <reply message>: set a warning filter on a certain keyword
 - /nowarn <keyword>: stop a warning filter
 - /warnlist: list of all current warning filters
"""

__name__ = "Warnings"


WARN_HANDLER = CommandHandler("warn", warn_user)
RESET_WARN_HANDLER = CommandHandler("resetwarn", reset_warns)
CALLBACK_QUERY_HANDLER = CallbackQueryHandler(button, pattern=r"rm_warn")
MYWARNS_HANDLER = CommandHandler("warns", warns)
ADD_WARN_HANDLER = CommandHandler("addwarn", add_warn_filter)
RM_WARN_HANDLER = CommandHandler("nowarn", remove_warn_filter, pass_args=True)
LIST_WARN_HANDLER = CommandHandler("warnlist", list_warn_filters)
WARN_FILTER_HANDLER = MessageHandler(Filters.text | Filters.command | Filters.sticker | Filters.photo, reply_filter)

dispatcher.add_handler(WARN_HANDLER)
dispatcher.add_handler(CALLBACK_QUERY_HANDLER)
dispatcher.add_handler(RESET_WARN_HANDLER)
dispatcher.add_handler(MYWARNS_HANDLER)
dispatcher.add_handler(ADD_WARN_HANDLER)
dispatcher.add_handler(RM_WARN_HANDLER)
dispatcher.add_handler(LIST_WARN_HANDLER)
dispatcher.add_handler(WARN_FILTER_HANDLER, WARN_HANDLER_GROUP)
