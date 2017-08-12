from telegram.ext import CommandHandler, MessageHandler, Filters
from telegram.ext.dispatcher import run_async

from tg_bot import dispatcher
import tg_bot.modules.sql.locks_sql as sql

LOCK_TYPES = ["sticker", "audio", "voice", "document", "video", "contact", "photo"]


def locktypes(bot, update):
    update.effective_message.reply_text(LOCK_TYPES)


def can_delete(bot, update):
    return update.effective_chat.get_member(bot.id).can_delete_messages


def is_user_admin(update, user_id):
    return update.effective_chat.get_member(user_id).status == 'administrator'


def lock(bot, update, args):
    chat_id = update.effective_chat.id
    if len(args) >= 1 and args[0] in LOCK_TYPES:
        lock_type = args[0]
        sql.update_lock(chat_id, lock_type, locked=True)
    else:
        update.effective_message.reply_text("What are you trying to lock...?")

    if not can_delete(bot, update):
        update.effective_message.reply_text("I'm not an administrator, so can't do anything.")


def unlock(bot, update, args):
    chat_id = update.effective_chat.id
    if len(args) >= 1 and args[0] in LOCK_TYPES:
        lock_type = args[0]
        sql.update_lock(chat_id, lock_type, locked=False)
    else:
        bot.sendMessage(chat_id, "What are you trying to unlock...?", "HTML")

    if not can_delete(bot, update):
        update.effective_message.reply_text("I'm not an administrator, so can't do anything.")


@run_async
def del_sticker(bot, update):
    chat_id = update.effective_chat.id
    if sql.is_locked(chat_id, "sticker") and can_delete(bot, update):
        update.effective_message.delete()


@run_async
def del_audio(bot, update):
    chat_id = update.effective_chat.id
    if sql.is_locked(chat_id, "audio") and can_delete(bot, update):
        update.effective_message.delete()


@run_async
def del_voice(bot, update):
    chat_id = update.effective_chat.id
    if sql.is_locked(chat_id, "voice") and can_delete(bot, update):
        update.effective_message.delete()


@run_async
def del_document(bot, update):
    print(update.message.document)
    chat_id = update.effective_chat.id
    if sql.is_locked(chat_id, "document") and can_delete(bot, update):
        update.effective_message.delete()


@run_async
def del_video(bot, update):
    chat_id = update.effective_chat.id
    if sql.is_locked(chat_id, "video") and can_delete(bot, update):
        update.effective_message.delete()


@run_async
def del_contact(bot, update):
    chat_id = update.effective_chat.id
    if sql.is_locked(chat_id, "contact") and can_delete(bot, update):
        update.effective_message.delete()


@run_async
def del_photo(bot, update):
    chat_id = update.effective_chat.id
    if sql.is_locked(chat_id, "photo") and can_delete(bot, update):
        update.effective_message.delete()


LOCKTYPES_HANDLER = CommandHandler("locktypes", locktypes)
LOCK_HANDLER = CommandHandler("lock", lock, pass_args=True)
UNLOCK_HANDLER = CommandHandler("unlock", unlock, pass_args=True)

STICKER_HANDLER = MessageHandler((~ Filters.private) & Filters.sticker, del_sticker)
AUDIO_HANDLER = MessageHandler((~ Filters.private) & Filters.audio, del_audio)
VOICE_HANDLER = MessageHandler((~ Filters.private) & Filters.voice, del_voice)
DOCUMENT_HANDLER = MessageHandler((~ Filters.private) & Filters.document, del_document)
VIDEO_HANDLER = MessageHandler((~ Filters.private) & Filters.video, del_video)
CONTACT_HANDLER = MessageHandler((~ Filters.private) & Filters.contact, del_contact)
PHOTO_HANDLER = MessageHandler((~ Filters.private) & Filters.photo, del_photo)  # TODO: gif detection -> mime_type?

dispatcher.add_handler(LOCK_HANDLER)
dispatcher.add_handler(UNLOCK_HANDLER)
dispatcher.add_handler(LOCKTYPES_HANDLER)
dispatcher.add_handler(STICKER_HANDLER)
dispatcher.add_handler(AUDIO_HANDLER)
dispatcher.add_handler(VOICE_HANDLER)
dispatcher.add_handler(DOCUMENT_HANDLER)
dispatcher.add_handler(VIDEO_HANDLER)
dispatcher.add_handler(CONTACT_HANDLER)
dispatcher.add_handler(PHOTO_HANDLER)
