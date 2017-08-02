from pprint import pprint

from telegram.error import Unauthorized, BadRequest, TimedOut, NetworkError, ChatMigrated, TelegramError
from telegram.ext import CommandHandler

from tg_bot import sql, dispatcher, updater

# needed to dynamically load modules
# NOTE: Module order is not guaranteed, unless named numerically!
from tg_bot.modules import *
print("Loaded modules: " + str(all_modules))


def test(bot, update):
    # pprint(eval(str(update)))
    update.effective_message.reply_text("Hola tester")


def start(bot, update):
    chat_id = update.effective_chat.id
    sql.init_permissions(chat_id)
    update.effective_message.reply_text("Yo, whadup?")


def reply_simshit(bot, update):
    update.effective_message.reply_text("Did you mean: simshit?")


# def promote(bot, update):
#     chat_id = update.effective_chat.id
#     prev_message = update.effective_message.reply_to_message
#     if prev_message:
#         user_id = prev_message.from_user.id
#         res = bot.promoteChatMember(chat_id, user_id,
#                                     can_change_info=True,
#                                     can_post_messages=True,
#                                     can_edit_messages=True,
#                                     can_delete_messages=True,
#                                     can_invite_users=True,
#                                     can_restrict_members=True,
#                                     can_pin_messages=True,
#                                     can_promote_members=True)
#         print("promoted " + str(res))
#
#
# def demote(bot, update):
#     chat_id = update.effective_chat.id
#     prev_message = update.effective_message.reply_to_message
#     if prev_message:
#         user_id = prev_message.from_user.id
#         res = bot.promoteChatMember(int(chat_id), int(user_id),
#                                     can_change_info=False,
#                                     can_post_messages=False,
#                                     can_edit_messages=False,
#                                     can_delete_messages=False,
#                                     can_invite_users=False,
#                                     can_restrict_members=False,
#                                     can_pin_messages=False,
#                                     can_promote_members=False)
#         print("promoted " + str(res))
#
#
# def restrict(bot, update):
#     chat_id = update.effective_chat.id
#     prev_message = update.effective_message.reply_to_message
#     if prev_message:
#         user_id = prev_message.from_user.id
#         print(str(user_id) + "is the user_id")
#         print(str(chat_id) + "is the chat id")
#         res = bot.promoteChatMember(int(chat_id), int(user_id),
#                                     can_edit_message=True)
#         print("promoted " + str(res))

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
        # handle malformed requests - read more below!
    except TimedOut:
        print("no nono3")
        # handle slow connection problems
    except NetworkError:
        print("no nono4")
        # handle other connection problems
    except ChatMigrated as e:
        print("no nono5")
        # the chat_id of a group has changed, use e.new_chat_id instead
    except TelegramError:
        print(error)
        # handle all other telegram related errors


def test_rights(bot, update):
    pprint(update.effective_chat.get_member(bot.id).__dict__)


def main():
    test_handler = CommandHandler("test", test)
    start_handler = CommandHandler("start", start)

    # simao_handler = MessageHandler(Filters.text & SimaoFilter, reply_simshit)

    # promote_handler = CommandHandler("promote", promote)
    # demote_handler = CommandHandler("demote", demote)
    # restrict_handler = CommandHandler("restrict", restrict)
    #
    # dispatcher.add_handler(promote_handler)
    # dispatcher.add_handler(demote_handler)
    # dispatcher.add_handler(restrict_handler)

    dispatcher.add_handler(CommandHandler("rights", test_rights))

    dispatcher.add_handler(test_handler)
    dispatcher.add_handler(start_handler)

    # dispatcher.add_handler(simao_handler)

    dispatcher.add_error_handler(error_callback)

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
