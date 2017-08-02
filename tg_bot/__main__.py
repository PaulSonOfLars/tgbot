import logging
from pprint import pprint

from telegram.error import Unauthorized, BadRequest, TimedOut, NetworkError, ChatMigrated, TelegramError
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

from tg_bot import sql
from tg_bot.config import Development as Configuration
from tg_bot.custom_filters import SimaoFilter, HashFilter

lock_types = ["sticker", "audio", "voice", "document", "video", "contact", "photo"]


def test(bot, update):
    # pprint(eval(str(update)))
    update.effective_message.reply_text("Hola tester")


def save(bot, update, args):
    chat_id = update.effective_chat.id
    if len(args) >= 2:
        notename = args[0]
        del args[0]
        note_data = " ".join(args)

        sql.add_note_to_db(chat_id, notename, note_data)
        update.effective_message.reply_text("yas! added " + notename)
    elif update.effective_message.reply_to_message and len(args) >= 1:
        notename = args[0]
        note_data = update.effective_message.reply_to_message
        print(note_data.text)
        sql.add_note_to_db(chat_id, notename, note_data.text)
        update.effective_message.reply_text("yas! added replied message " + notename)

    else:
        update.effective_message.reply_text("Dude, theres no note")


def get(bot, update, args):
    chat_id = update.effective_chat.id
    if len(args) >= 1:
        notename = args[0]

        note = sql.get_note(chat_id, notename)
        if note:
            update.effective_message.reply_text(note.value)
            return
        else:
            update.effective_message.reply_text("This doesn't exist")
    else:
        update.effective_message.reply_text("Get rekt")


def hash_get(bot, update):
    message = update.effective_message.text
    fst_word = message.split()[0]
    no_hash = fst_word[1:]
    get(bot, update, [no_hash])


def delete(bot, update, args):
    chat_id = update.effective_chat.id
    notename = args[0]

    sql.rm_note(chat_id, notename)
    update.effective_message.reply_text("Successfully removed note")


def start(bot, update):
    chat_id = update.effective_chat.id
    sql.init_permissions(chat_id)
    update.effective_message.reply_text("Yo, whadup?")


def reply_simshit(bot, update):
    update.effective_message.reply_text("Did you mean: simshit?")


def del_message(bot, update):
    chat_id = update.effective_chat.id
    message_id = update.effective_message.message_id

    res = bot.deleteMessage(chat_id, message_id)
    if not res:
        bot.sendMessage(chat_id, "Dafarq, I can't delete that", "HTML")


def lock(bot, update, args):
    chat_id = update.effective_chat.id
    lock_type = args[0]
    if len(args) >= 1 and lock_type in lock_types:
        sql.update_lock(chat_id, lock_type, locked=True)
    else:
        bot.sendMessage(chat_id, "What are you trying to lock...?", "HTML")


def unlock(bot, update, args):
    chat_id = update.effective_chat.id
    lock_type = args[0]
    if len(args) >= 1 and lock_type in lock_types:
        sql.update_lock(chat_id, lock_type, locked=False)
    else:
        bot.sendMessage(chat_id, "What are you trying to unlock...?", "HTML")


def del_sticker(bot, update):
    chat_id = update.effective_chat.id
    if sql.is_locked(chat_id, "sticker"):
        del_message(bot, update)


def del_audio(bot, update):
    chat_id = update.effective_chat.id
    if sql.is_locked(chat_id, "audio"):
        del_message(bot, update)


def del_voice(bot, update):
    chat_id = update.effective_chat.id
    if sql.is_locked(chat_id, "voice"):
        del_message(bot, update)


def del_document(bot, update):
    chat_id = update.effective_chat.id
    if sql.is_locked(chat_id, "document"):
        del_message(bot, update)


def del_video(bot, update):
    chat_id = update.effective_chat.id
    if sql.is_locked(chat_id, "video"):
        del_message(bot, update)


def del_contact(bot, update):
    chat_id = update.effective_chat.id
    if sql.is_locked(chat_id, "contact"):
        del_message(bot, update)


def del_photo(bot, update):
    chat_id = update.effective_chat.id
    if sql.is_locked(chat_id, "photo"):
        del_message(bot, update)


def locktypes(bot, update):
    update.effective_message.reply_text(lock_types)


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
    updater = Updater(Configuration.API_KEY)
    dispatcher = updater.dispatcher

    # enable logging
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.INFO)

    LOGGER = logging.getLogger(__name__)

    test_handler = CommandHandler("test", test)
    start_handler = CommandHandler("start", start)
    save_handler = CommandHandler("save", save, pass_args=True)
    get_handler = CommandHandler("get", get, pass_args=True)
    delete_handler = CommandHandler("delete", delete, pass_args=True)
    lock_handler = CommandHandler("lock", lock, pass_args=True)
    unlock_handler = CommandHandler("unlock", unlock, pass_args=True)
    locktypes_handler = CommandHandler("locktypes", locktypes)
    hash_get_handler = MessageHandler(HashFilter, hash_get)
    sticker_handler = MessageHandler((~ Filters.private) & Filters.sticker, del_sticker)
    audio_handler = MessageHandler((~ Filters.private) & Filters.audio, del_audio)
    voice_handler = MessageHandler((~ Filters.private) & Filters.voice, del_voice)
    document_handler = MessageHandler((~ Filters.private) & Filters.document, del_document)
    video_handler = MessageHandler((~ Filters.private) & Filters.video, del_video)
    contact_handler = MessageHandler((~ Filters.private) & Filters.contact, del_contact)
    photo_handler = MessageHandler((~ Filters.private) & Filters.photo, del_photo)  # TODO: gif detection -> mime_type?
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
    dispatcher.add_handler(save_handler)
    dispatcher.add_handler(get_handler)
    dispatcher.add_handler(hash_get_handler)
    dispatcher.add_handler(delete_handler)
    dispatcher.add_handler(lock_handler)
    dispatcher.add_handler(unlock_handler)
    dispatcher.add_handler(locktypes_handler)
    dispatcher.add_handler(sticker_handler)
    dispatcher.add_handler(audio_handler)
    dispatcher.add_handler(voice_handler)
    dispatcher.add_handler(document_handler)
    dispatcher.add_handler(video_handler)
    dispatcher.add_handler(contact_handler)
    dispatcher.add_handler(photo_handler)
    # dispatcher.add_handler(simao_handler)

    dispatcher.add_error_handler(error_callback)

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
