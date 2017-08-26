import importlib
from pprint import pprint

import os
from random import randint
from time import sleep

import requests
import telegram
from telegram.error import Unauthorized, BadRequest, TimedOut, NetworkError, ChatMigrated, TelegramError
from telegram.ext import CommandHandler, Filters, MessageHandler
from telegram.ext.dispatcher import run_async

from tg_bot import dispatcher, updater, TOKEN, HEROKU
# needed to dynamically load modules
# NOTE: Module order is not guaranteed, specify that in modules/loadorder.txt!
from tg_bot.custom_filters import SimaoFilter
from tg_bot.modules import ALL_MODULES


help_strings = """
Commands available:
 - /start: start the bot
 - /id: get current group id. if used replying to a message, gets that user's id.
 - /runs: after a 5 sec delay, send a random string from an array of replies.
 - /help: PM's you this message.
"""

print("Loading modules: " + str(ALL_MODULES))

for module_name in ALL_MODULES:
    imported_module = importlib.import_module("tg_bot.modules." + module_name)
    if hasattr(imported_module, "__help__"):
        help_strings += imported_module.__help__
    else:
        help_strings += "\n {} module has no help docs, but is loaded. \n".format(module_name)

print("Successfully loaded modules: " + str(ALL_MODULES))

RUN_STRINGS = (
    "Where do you think you're going?",
    "Huh? what? did he get away?",
    "ZZzzZZzz... Huh? what? oh, just him again, nevermind.",
    "Get back here!",
    "Not so fast...",
    "Look out for the wall!",
    "Don't leave me alone with them!!",
    "You run, you die.",
    "Run fatboy, run!",
    "Jokes on you, I'm everywhere",
    "You're gonna regret that...",
    "You could also try /kickme, I hear thats fun.",
    "Go bother someone else, no-one here cares.",
    "I hear @MSFJarvis wants to hear more about you."
)


@run_async
def test(bot, update):
    # pprint(eval(str(update)))
    update.effective_message.reply_text("Hola tester")


@run_async
def get_id(bot, update):
    if update.effective_message.reply_to_message:
        user = update.effective_message.reply_to_message.from_user
        update.effective_message.reply_text(user.username + "'s id is " + str(user.id))
    else:
        chat = update.effective_chat
        update.effective_message.reply_text("This group's id is " + str(chat.id))


@run_async
def runs(bot, update):
    sleep(5)
    someint = randint(0, len(RUN_STRINGS)-1)
    update.effective_message.reply_text(RUN_STRINGS[someint])


def start(bot, update):
    # sql.init_permissions(update.effective_chat.id)
    update.effective_message.reply_text("Yo, whadup?")


def reply_simshit(bot, update):
    update.effective_message.reply_text("Did you mean: simshit?")


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


def test_rights(bot, update):
    pprint(update.effective_chat.get_member(bot.id).__dict__)


@run_async
def get_bot_ip(bot, update):
    """ Sends the bot's IP address, so as to be able to ssh in if necessary.
        OWNER ONLY.
    """
    sender = update.message.from_user
    if sender.id == 254318997:
        res = requests.get("http://ipinfo.io/ip")
        update.message.reply_text(res.text)


def split_message(msg):
    if len(msg) < telegram.MAX_MESSAGE_LENGTH:
        return [msg]
    else:
        lines = help_strings.splitlines()
        small_help = ""
        result = []
        for line in lines:
            newline = line + "\n"
            if len(small_help) + len(newline) < telegram.MAX_MESSAGE_LENGTH:
                small_help += newline
            else:
                result.append(small_help)
                small_help = newline
        else:
            # Else statement at the end of the for loop, to append leftover string.
            result.append(small_help)

        return result


@run_async
def get_help(bot, update):
    user = update.effective_message.from_user
    chat = update.effective_chat

    if chat.type == "private":
        for msg in split_message(help_strings):
            update.effective_message.reply_text(msg)

    else:
        try:
            for msg in split_message(help_strings):
                bot.send_message(user.id, msg)

            update.effective_message.reply_text("I've PM'ed you about me.")
        except Unauthorized:
            update.effective_message.reply_text("Contact me in PM first to get the list of possible commands.")


def main():
    test_handler = CommandHandler("test", test)
    start_handler = CommandHandler("start", start)
    id_handler = CommandHandler("id", get_id)
    runs_handler = CommandHandler("runs", runs)
    ip_handler = CommandHandler("ip", get_bot_ip)
    help_handler = CommandHandler("help", get_help)

    simao_handler = MessageHandler(Filters.text & SimaoFilter, reply_simshit)

    dispatcher.add_handler(CommandHandler("rights", test_rights))

    # dispatcher.add_handler(test_handler)
    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(id_handler)
    dispatcher.add_handler(runs_handler)
    dispatcher.add_handler(ip_handler)
    dispatcher.add_handler(help_handler)

    # dispatcher.add_handler(simao_handler)

    # dispatcher.add_error_handler(error_callback)

    if HEROKU:
        port = int(os.environ.get('PORT', 5000))
        updater.start_webhook(listen="0.0.0.0",
                              port=port,
                              url_path=TOKEN)
        updater.bot.set_webhook("https://tgpolbot.herokuapp.com/" + TOKEN)
    else:
        updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
