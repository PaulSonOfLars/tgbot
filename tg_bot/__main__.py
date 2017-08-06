from pprint import pprint

from telegram.error import Unauthorized, BadRequest, TimedOut, NetworkError, ChatMigrated, TelegramError
from telegram.ext import CommandHandler

from tg_bot import dispatcher, updater
# needed to dynamically load modules
# NOTE: Module order is not guaranteed, unless named numerically!
from tg_bot.modules import *

print("Loaded modules: " + str(ALL_MODULES))


def test(bot, update):
    # pprint(eval(str(update)))
    update.effective_message.reply_text("Hola tester")


def get_id(bot, update):
    if update.effective_message.reply_to_message:
        user = update.effective_message.reply_to_message.from_user
        update.effective_message.reply_text(user.username + "'s id is " + str(user.id))
    else:
        chat = update.effective_chat
        update.effective_message.reply_text("This group's id is " + str(chat.id))


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


def main():
    test_handler = CommandHandler("test", test)
    start_handler = CommandHandler("start", start)
    id_handler = CommandHandler("id", get_id)

    # simao_handler = MessageHandler(Filters.text & SimaoFilter, reply_simshit)

    dispatcher.add_handler(CommandHandler("rights", test_rights))

    dispatcher.add_handler(test_handler)
    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(id_handler)

    # dispatcher.add_handler(simao_handler)

    # dispatcher.add_error_handler(error_callback)

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
