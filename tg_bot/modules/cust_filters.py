import re

from telegram.ext import CommandHandler, BaseFilter, MessageHandler

from tg_bot import dispatcher

HANDLER_GROUP = 10


class RegexSearcher(BaseFilter):
    def __init__(self, chat_id, word):
        super().__init__()
        self.word = word
        self.pattern = "( |^)" + self.word + "( |$)"
        self.chat_id = chat_id

    def filter(self, message):
        return re.search(self.pattern, message.text, flags=re.IGNORECASE) \
               and message.chat_id == self.chat_id

    def __eq__(self, other):
        return other == self.word

    def __str__(self):
        return self.word

    def __repr__(self):
        return "<RegexSearcher for {} by {} in chat {}>".format(self.word, self.pattern, self.chat_id)


def list_handlers(bot, update):
    handlers = dispatcher.handlers.get(HANDLER_GROUP, [])
    for h in handlers:
        update.effective_message.reply_text(str(h.filters))


def filters(bot, update):
    text = update.effective_message.text
    args = text.split(None, 2)  # use python's maxsplit to separate Cmd, keyword, and reply_text
    keyword = args[1]
    reply = args[2]

    custom_handler = MessageHandler(RegexSearcher(update.effective_chat.id, keyword),
                                    lambda b, u: u.effective_message.reply_text(reply))
    dispatcher.add_handler(custom_handler, HANDLER_GROUP)

    update.effective_message.reply_text("Handler Added!")


def stop_filter(bot, update, args):
    for handler in dispatcher.handlers.get(HANDLER_GROUP):
        if handler.filters == args[0]:
            update.effective_message.reply_text("Yep, gonna stop replying that")
            dispatcher.remove_handler(handler, HANDLER_GROUP)
            break
        else:
            update.effective_message.reply_text("That's not a current filter - run /list for all filters")

FILTER_HANDLER = CommandHandler("filter", filters)
STOP_HANDLER = CommandHandler("stop", stop_filter, pass_args=True)
LIST_HANDLER = CommandHandler("list", list_handlers)

dispatcher.add_handler(FILTER_HANDLER)
dispatcher.add_handler(STOP_HANDLER)
dispatcher.add_handler(LIST_HANDLER)
