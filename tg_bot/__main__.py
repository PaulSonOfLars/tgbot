import importlib
import os

from telegram import ParseMode
from telegram.error import Unauthorized, BadRequest, TimedOut, NetworkError, ChatMigrated, TelegramError
from telegram.ext import CommandHandler, Filters, MessageHandler
from telegram.ext.dispatcher import run_async, DispatcherHandlerStop
from telegram.utils.helpers import escape_markdown

from tg_bot import dispatcher, updater, TOKEN, WEBHOOK, OWNER_ID
# needed to dynamically load modules
# NOTE: Module order is not guaranteed, specify that in modules/load.json!
from tg_bot.modules import ALL_MODULES
from tg_bot.modules.helper_funcs import split_message

PM_START_TEXT = """
Hi {}, my name is {}! I'm a group manager bot maintained by [this wonderful person](tg://user?id={}).
I'm built in python3, using the python-telegram-bot library, and am fully opensource - you can find what makes me tick \
[here](github.com/PaulSonOfLars/tgbot)!

Feel free to submit pull requests on github, or to contact my creator, @SonOfLars, with any bugs, questions or \
feature requests you might have :)

You can find the list of available commands with /help.
"""

HELP_STRINGS = """
Commands available:
 - /start: start the bot
 - /help: PM's you this message.
"""

MIGRATEABLE = []
STATS = []

for module_name in ALL_MODULES:
    imported_module = importlib.import_module("tg_bot.modules." + module_name)
    if hasattr(imported_module, "__help__"):
        HELP_STRINGS += imported_module.__help__
    else:
        HELP_STRINGS += "\n {} module has no help docs, but is loaded. \n".format(module_name)

    # Chats to migrate on chat_migrated events
    if hasattr(imported_module, "__migrate__"):
        MIGRATEABLE.append(imported_module)
    if hasattr(imported_module, "__stats__"):
        STATS.append(imported_module)


@run_async
def test(bot, update):
    # pprint(eval(str(update)))
    # update.effective_message.reply_text("Hola tester! _I_ *have* `markdown`", parse_mode=ParseMode.MARKDOWN)
    update.effective_message.reply_text("This person edited a message")
    print(update.effective_message)


def start(bot, update):
    if update.effective_chat.type == "private":
        first_name = update.effective_user.first_name
        update.effective_message.reply_text(
            PM_START_TEXT.format(escape_markdown(first_name), escape_markdown(bot.first_name), OWNER_ID),
            parse_mode=ParseMode.MARKDOWN)
    else:
        update.effective_message.reply_text("Yo, whadup?")


# for test purposes
def error_callback(bot, update, error):
    try:
        raise error
    except Unauthorized:
        print("no nono1")
        print(error)
        # remove update.message.chat_id from conversation list
    except BadRequest:
        print("no nono2")
        print("BadRequest caught")
        print(error)

        # handle malformed requests - read more below!
    except TimedOut:
        print("no nono3")
        # handle slow connection problems
    except NetworkError:
        print("no nono4")
        # handle other connection problems
    except ChatMigrated as err:
        print("no nono5")
        print(err)
        # the chat_id of a group has changed, use e.new_chat_id instead
    except TelegramError:
        print(error)
        # handle all other telegram related errors


@run_async
def get_help(bot, update):
    user = update.effective_message.from_user
    chat = update.effective_chat

    if chat.type == "private":
        for msg in split_message(HELP_STRINGS):
            update.effective_message.reply_text(msg)

    else:
        try:
            for msg in split_message(HELP_STRINGS):
                bot.send_message(user.id, msg)

            update.effective_message.reply_text("I've PM'ed you about me.")
        except Unauthorized:
            update.effective_message.reply_text("Contact me in PM first to get the list of possible commands.")


def migrate_chats(bot, update):
    msg = update.effective_message
    if msg.migrate_to_chat_id:
        old_chat = update.effective_chat.id
        new_chat = msg.migrate_to_chat_id
    elif msg.migrate_from_chat_id:
        old_chat = msg.migrate_from_chat_id
        new_chat = update.effective_chat.id
    else:
        return

    print("Migrating from {} to {}".format(old_chat, new_chat))
    for mod in MIGRATEABLE:
        mod.__migrate__(old_chat, new_chat)

    raise DispatcherHandlerStop


def main():
    test_handler = MessageHandler(Filters.all, test, edited_updates=True, message_updates=False)
    start_handler = CommandHandler("start", start)
    help_handler = CommandHandler("help", get_help)
    migrate_handler = MessageHandler(Filters.status_update.migrate, migrate_chats)

    # dispatcher.add_handler(test_handler)
    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(help_handler)
    dispatcher.add_handler(migrate_handler)

    # dispatcher.add_error_handler(error_callback)

    if WEBHOOK:
        port = int(os.environ.get('PORT', 5000))
        updater.start_webhook(listen="0.0.0.0",
                              port=port,
                              url_path=TOKEN)

        from tg_bot import URL
        updater.bot.set_webhook(URL + TOKEN)
    else:
        updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    print("Successfully loaded modules: " + str(ALL_MODULES))
    main()
