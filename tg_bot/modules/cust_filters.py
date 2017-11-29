import re

import telegram
from telegram.ext import CommandHandler, BaseFilter, MessageHandler, DispatcherHandlerStop, run_async, Filters

from tg_bot import dispatcher
from tg_bot.modules.helper_funcs import user_admin
from tg_bot.modules.sql import cust_filters_sql as sql

HANDLER_GROUP = 10


class CustSearcher(BaseFilter):
    def __init__(self, chat_id, keyword):
        super().__init__()
        self.keyword = keyword
        self.pattern = "( |^|[^\w])" + re.escape(self.keyword) + "( |$|[^\w])"
        self.chat_id = chat_id

    def filter(self, message):
        return bool(message.text
                    and message.chat_id == self.chat_id
                    and re.search(self.pattern, message.text, flags=re.IGNORECASE))

    def __eq__(self, other):
        return other == (self.keyword, self.chat_id)

    def __str__(self):
        return self.keyword

    def __repr__(self):
        return "<RegexSearcher for {} by {} in chat {}>".format(self.keyword, self.pattern, self.chat_id)


def save_filter(chat_id, keyword, content, is_sticker=False):
    # Note: perhaps handlers can be removed somehow using sql.get_chat_filters
    for handler in dispatcher.handlers.get(HANDLER_GROUP, []):
        if handler.filters == (keyword, chat_id):
            dispatcher.remove_handler(handler, HANDLER_GROUP)

    sql.add_filter(chat_id, keyword, content, is_sticker)


@run_async
def list_handlers(bot, update):
    chat = update.effective_chat
    all_handlers = sql.get_chat_filters(chat.id)

    if not all_handlers:
        update.effective_message.reply_text("No filters are active here!")
        return

    filter_list = "Current filters in this chat:\n"
    for handler in all_handlers:
        entry = " - {}\n".format(handler.keyword)
        if len(entry) + len(filter_list) > telegram.MAX_MESSAGE_LENGTH:
            update.effective_message.reply_text(filter_list)
            filter_list = entry
        else:
            filter_list += entry

    if not filter_list == "Current filters in this chat:\n":
        update.effective_message.reply_text(filter_list)


@user_admin
def filters(bot, update):
    chat = update.effective_chat
    msg = update.effective_message
    args = msg.text.split(None, 2)  # use python's maxsplit to separate Cmd, keyword, and reply_text

    if len(args) >= 3:
        keyword = args[1]
        content = args[2]
        is_sticker = False

    elif msg.reply_to_message and msg.reply_to_message.sticker:
        keyword = args[1]
        content = msg.reply_to_message.sticker.file_id
        is_sticker = True

    else:
        return

    save_filter(chat.id, keyword, content, is_sticker)
    update.effective_message.reply_text("Handler {} added!".format(keyword))
    raise DispatcherHandlerStop


@user_admin
def stop_filter(bot, update, args):
    chat = update.effective_chat

    if len(args) < 1:
        return

    chat_filters = sql.get_chat_filters(chat.id)

    if not chat_filters:
        update.effective_message.reply_text("No filters are active here!")
        return

    for filt in chat_filters:
        if filt.chat_id == str(chat.id) and filt.keyword == args[0]:
            sql.remove_filter(chat.id, args[0])
            update.effective_message.reply_text("Yep, I'll stop replying to that.")
            return

    update.effective_message.reply_text("That's not a current filter - run /filters for all active filters.")


@run_async
def reply_filter(bot, update):
    chat_filters = sql.get_chat_filters(update.effective_chat.id)
    message = update.effective_message
    to_match = message.text or message.caption or (message.sticker.emoji if message.sticker else None)
    if not to_match:
        return
    for filt in chat_filters:
        pattern = "( |^|[^\w])" + re.escape(filt.keyword) + "( |$|[^\w])"
        if re.search(pattern, to_match, flags=re.IGNORECASE):
            if filt.is_sticker:
                message.reply_sticker(filt.reply)
            else:
                message.reply_text(filt.reply)
            break


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


__help__ = """
 - /filter <keyword> <reply message>: add a filter to this chat. The bot will now reply the message whenever 'keyword' \
 is mentioned. If you reply to a sticker with a keyword, the bot will reply with that sticker.
 - /stop <filter keyword>: stop that filter.
 - /filters: list all active filters in this chat
"""

FILTER_HANDLER = CommandHandler("filter", filters)
STOP_HANDLER = CommandHandler("stop", stop_filter, pass_args=True)
LIST_HANDLER = CommandHandler("filters", list_handlers)
CUST_FILTER_HANDLER = MessageHandler(Filters.text | Filters.command | Filters.sticker | Filters.photo, reply_filter)

dispatcher.add_handler(FILTER_HANDLER)
dispatcher.add_handler(STOP_HANDLER)
dispatcher.add_handler(LIST_HANDLER)
dispatcher.add_handler(CUST_FILTER_HANDLER, HANDLER_GROUP)
